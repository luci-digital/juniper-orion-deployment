"""
Inference Manager - Orchestrates multiple inference engines
Provides unified API with automatic failover and load balancing
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime
import logging
from enum import Enum

from .base import InferenceEngine, InferenceBackend, Message, GenerationConfig
from .ollama_engine import OllamaEngine
from .transformers_engine import TransformersEngine

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY = "priority"
    FAILOVER = "failover"

class InferenceManager:
    """Manages multiple inference engines with load balancing and failover"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.FAILOVER):
        self.engines: Dict[str, InferenceEngine] = {}
        self.strategy = strategy
        self._round_robin_index = 0
        self._engine_stats: Dict[str, Dict[str, Any]] = {}
        
    async def register_engine(
        self, 
        name: str, 
        engine: InferenceEngine,
        priority: int = 0
    ) -> None:
        """Register an inference engine"""
        await engine.initialize()
        self.engines[name] = engine
        self._engine_stats[name] = {
            "requests": 0,
            "errors": 0,
            "avg_latency": 0,
            "priority": priority,
            "last_used": None
        }
        logger.info(f"Registered engine: {name}")
        
    async def register_ollama(
        self, 
        name: str = "ollama",
        model_id: str = "mistral",
        priority: int = 1
    ) -> None:
        """Register an Ollama engine"""
        engine = OllamaEngine(model_id)
        await self.register_engine(name, engine, priority)
        
    async def register_transformers(
        self,
        name: str = "transformers",
        model_id: str = "microsoft/phi-2",
        priority: int = 2,
        **kwargs
    ) -> None:
        """Register a Transformers engine"""
        engine = TransformersEngine(model_id, **kwargs)
        await self.register_engine(name, engine, priority)
        
    def _select_engine(self) -> Optional[str]:
        """Select engine based on strategy"""
        if not self.engines:
            return None
            
        available_engines = [
            name for name, engine in self.engines.items()
            if engine._initialized
        ]
        
        if not available_engines:
            return None
            
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            engine_name = available_engines[self._round_robin_index % len(available_engines)]
            self._round_robin_index += 1
            return engine_name
            
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            # Select engine with lowest request count
            return min(
                available_engines,
                key=lambda x: self._engine_stats[x]["requests"]
            )
            
        elif self.strategy == LoadBalancingStrategy.PRIORITY:
            # Select highest priority available engine
            return max(
                available_engines,
                key=lambda x: self._engine_stats[x]["priority"]
            )
            
        else:  # FAILOVER
            # Use first available engine by priority
            return sorted(
                available_engines,
                key=lambda x: -self._engine_stats[x]["priority"]
            )[0]
            
    async def generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None,
        engine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response with automatic engine selection"""
        # Select engine
        if engine_name and engine_name in self.engines:
            selected_engine_name = engine_name
        else:
            selected_engine_name = self._select_engine()
            
        if not selected_engine_name:
            raise RuntimeError("No available inference engines")
            
        engine = self.engines[selected_engine_name]
        stats = self._engine_stats[selected_engine_name]
        
        # Track timing
        start_time = datetime.utcnow()
        
        try:
            # Generate response
            response = await engine.generate(messages, config)
            
            # Update stats
            latency = (datetime.utcnow() - start_time).total_seconds()
            stats["requests"] += 1
            stats["avg_latency"] = (
                (stats["avg_latency"] * (stats["requests"] - 1) + latency) 
                / stats["requests"]
            )
            stats["last_used"] = datetime.utcnow()
            
            return {
                "response": response,
                "engine": selected_engine_name,
                "latency": latency,
                "model": engine.model_id
            }
            
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Engine {selected_engine_name} failed: {e}")
            
            # Try failover if using failover strategy
            if self.strategy == LoadBalancingStrategy.FAILOVER:
                # Remove failed engine temporarily
                failed_engine = selected_engine_name
                del self.engines[failed_engine]
                
                try:
                    # Retry with different engine
                    result = await self.generate(messages, config)
                    
                    # Re-add failed engine for next attempt
                    self.engines[failed_engine] = engine
                    
                    return result
                    
                except Exception as retry_error:
                    # Re-add failed engine
                    self.engines[failed_engine] = engine
                    raise retry_error
                    
            raise
            
    async def stream_generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None,
        engine_name: Optional[str] = None
    ):
        """Stream response generation"""
        # Select engine
        if engine_name and engine_name in self.engines:
            selected_engine_name = engine_name
        else:
            selected_engine_name = self._select_engine()
            
        if not selected_engine_name:
            raise RuntimeError("No available inference engines")
            
        engine = self.engines[selected_engine_name]
        
        # Stream response
        async for chunk in engine.stream_generate(messages, config):
            yield {
                "chunk": chunk,
                "engine": selected_engine_name,
                "model": engine.model_id
            }
            
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all engines"""
        health_results = {}
        
        for name, engine in self.engines.items():
            try:
                health = await engine.health_check()
                health_results[name] = health
            except Exception as e:
                health_results[name] = {
                    "status": "error",
                    "error": str(e)
                }
                
        return {
            "manager_status": "healthy" if health_results else "no_engines",
            "engines": health_results,
            "stats": self._engine_stats,
            "strategy": self.strategy.value
        }
        
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get information about all available models"""
        models = []
        
        for name, engine in self.engines.items():
            try:
                info = await engine.get_model_info()
                info["engine_name"] = name
                models.append(info)
            except Exception as e:
                logger.error(f"Failed to get model info for {name}: {e}")
                
        return models
