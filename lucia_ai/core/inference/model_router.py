"""
Lucia Model Router - Intelligent routing between inference backends
Supports Ollama, LM Studio, and local Transformers with automatic failover
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from enum import Enum, auto
from collections import defaultdict
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ModelCapability(Enum):
    """Model capabilities for routing decisions"""
    CHAT = auto()
    CODE = auto()
    ANALYSIS = auto()
    CREATIVE = auto()
    MULTILINGUAL = auto()
    FUNCTION_CALLING = auto()
    LONG_CONTEXT = auto()
    FAST_INFERENCE = auto()

@dataclass
class ModelProfile:
    """Profile for each available model"""
    model_id: str
    backend: str  # ollama, lmstudio, transformers
    endpoint: str
    capabilities: Set[ModelCapability]
    context_length: int
    performance_score: float = 1.0  # Dynamic performance metric
    error_rate: float = 0.0
    avg_latency: float = 0.0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoutingDecision:
    """Routing decision with reasoning"""
    model_profile: ModelProfile
    score: float
    reasoning: List[str]
    fallback_options: List[ModelProfile]

class IntelligentModelRouter:
    """Routes requests to optimal models based on capabilities and performance"""
    
    def __init__(self):
        self.models: Dict[str, ModelProfile] = {}
        self.performance_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.session: Optional[aiohttp.ClientSession] = None
        self._discovery_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize router and discover available models"""
        self.session = aiohttp.ClientSession()
        
        # Start model discovery
        await self._discover_models()
        
        # Start periodic discovery
        self._discovery_task = asyncio.create_task(self._periodic_discovery())
        
        logger.info(f"Model router initialized with {len(self.models)} models")
        
    async def _discover_models(self):
        """Discover available models from all backends"""
        discovered = []
        
        # Discover Ollama models
        discovered.extend(await self._discover_ollama_models())
        
        # Discover LM Studio models
        discovered.extend(await self._discover_lmstudio_models())
        
        # Register discovered models
        for profile in discovered:
            self.models[profile.model_id] = profile
            
    async def _discover_ollama_models(self) -> List[ModelProfile]:
        """Discover models from Ollama"""
        profiles = []
        
        try:
            async with self.session.get("http://localhost:11434/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for model in data.get("models", []):
                        model_name = model["name"]
                        
                        # Determine capabilities based on model name
                        capabilities = {ModelCapability.CHAT}
                        
                        if "code" in model_name.lower() or "codellama" in model_name:
                            capabilities.add(ModelCapability.CODE)
                        if "mistral" in model_name.lower():
                            capabilities.update({
                                ModelCapability.FAST_INFERENCE,
                                ModelCapability.MULTILINGUAL
                            })
                        if "llama" in model_name.lower():
                            capabilities.add(ModelCapability.LONG_CONTEXT)
                        if "neural" in model_name.lower():
                            capabilities.add(ModelCapability.CREATIVE)
                            
                        profile = ModelProfile(
                            model_id=f"ollama/{model_name}",
                            backend="ollama",
                            endpoint="http://localhost:11434",
                            capabilities=capabilities,
                            context_length=model.get("context_length", 4096),
                            metadata={
                                "size": model.get("size"),
                                "modified": model.get("modified_at"),
                                "family": model.get("details", {}).get("family")
                            }
                        )
                        
                        profiles.append(profile)
                        logger.info(f"Discovered Ollama model: {model_name}")
                        
        except Exception as e:
            logger.warning(f"Failed to discover Ollama models: {e}")
            
        return profiles
        
    async def _discover_lmstudio_models(self) -> List[ModelProfile]:
        """Discover models from LM Studio"""
        profiles = []
        
        try:
            async with self.session.get("http://localhost:1234/v1/models") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for model in data.get("data", []):
                        model_id = model["id"]
                        
                        # LM Studio models generally support chat and long context
                        capabilities = {
                            ModelCapability.CHAT,
                            ModelCapability.LONG_CONTEXT
                        }
                        
                        # Add specific capabilities based on model
                        if "code" in model_id.lower():
                            capabilities.add(ModelCapability.CODE)
                        if "instruct" in model_id.lower():
                            capabilities.add(ModelCapability.ANALYSIS)
                            
                        profile = ModelProfile(
                            model_id=f"lmstudio/{model_id}",
                            backend="lmstudio",
                            endpoint="http://localhost:1234",
                            capabilities=capabilities,
                            context_length=8192,  # LM Studio typically supports 8k context
                            metadata={
                                "owned_by": model.get("owned_by", "lmstudio")
                            }
                        )
                        
                        profiles.append(profile)
                        logger.info(f"Discovered LM Studio model: {model_id}")
                        
        except Exception as e:
            logger.warning(f"Failed to discover LM Studio models: {e}")
            
        return profiles
        
    async def _periodic_discovery(self):
        """Periodically rediscover models"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            try:
                await self._discover_models()
            except Exception as e:
                logger.error(f"Error in periodic discovery: {e}")
                
    def _calculate_capability_score(
        self, 
        model: ModelProfile, 
        required_capabilities: Set[ModelCapability]
    ) -> float:
        """Calculate how well a model matches required capabilities"""
        if not required_capabilities:
            return 1.0
            
        matched = model.capabilities.intersection(required_capabilities)
        return len(matched) / len(required_capabilities)
        
    def _calculate_performance_score(self, model: ModelProfile) -> float:
        """Calculate performance score based on historical metrics"""
        base_score = model.performance_score
        
        # Penalize for high error rate
        error_penalty = model.error_rate * 0.5
        
        # Penalize for high latency (normalized)
        latency_penalty = min(model.avg_latency / 10.0, 0.3)  # Cap at 0.3
        
        # Boost for recent successful use
        recency_boost = 0.0
        if model.last_used:
            time_since_use = (datetime.utcnow() - model.last_used).total_seconds()
            if time_since_use < 300:  # Used in last 5 minutes
                recency_boost = 0.1
                
        return max(0.1, base_score - error_penalty - latency_penalty + recency_boost)
        
    def route_request(
        self,
        required_capabilities: Optional[Set[ModelCapability]] = None,
        min_context_length: int = 4096,
        preferred_backend: Optional[str] = None,
        exclude_models: Optional[Set[str]] = None
    ) -> RoutingDecision:
        """Route request to optimal model"""
        
        if not self.models:
            raise RuntimeError("No models available")
            
        required_capabilities = required_capabilities or {ModelCapability.CHAT}
        exclude_models = exclude_models or set()
        
        # Filter eligible models
        eligible_models = []
        for model_id, model in self.models.items():
            if model_id in exclude_models:
                continue
            if model.context_length < min_context_length:
                continue
            if preferred_backend and model.backend != preferred_backend:
                continue
                
            eligible_models.append(model)
            
        if not eligible_models:
            raise RuntimeError("No eligible models found")
            
        # Score and rank models
        scored_models = []
        for model in eligible_models:
            capability_score = self._calculate_capability_score(model, required_capabilities)
            performance_score = self._calculate_performance_score(model)
            
            # Combined score with weights
            total_score = (capability_score * 0.6) + (performance_score * 0.4)
            
            reasoning = []
            if capability_score == 1.0:
                reasoning.append("Perfect capability match")
            elif capability_score > 0.5:
                reasoning.append(f"Good capability match ({capability_score:.0%})")
            else:
                reasoning.append(f"Partial capability match ({capability_score:.0%})")
                
            if performance_score > 0.8:
                reasoning.append("Excellent performance history")
            elif performance_score < 0.5:
                reasoning.append("Performance concerns")
                
            scored_models.append((model, total_score, reasoning))
            
        # Sort by score
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        # Select best model
        best_model, best_score, reasoning = scored_models[0]
        
        # Get fallback options
        fallback_options = [m[0] for m in scored_models[1:4]]  # Top 3 alternatives
        
        return RoutingDecision(
            model_profile=best_model,
            score=best_score,
            reasoning=reasoning,
            fallback_options=fallback_options
        )
        
    async def update_performance_metrics(
        self,
        model_id: str,
        latency: float,
        success: bool,
        tokens_generated: Optional[int] = None
    ):
        """Update model performance metrics"""
        if model_id not in self.models:
            return
            
        model = self.models[model_id]
        model.last_used = datetime.utcnow()
        
        # Update latency (exponential moving average)
        alpha = 0.2
        model.avg_latency = (alpha * latency) + ((1 - alpha) * model.avg_latency)
        
        # Update error rate
        if success:
            model.error_rate = max(0, model.error_rate - 0.01)  # Slowly decrease
        else:
            model.error_rate = min(1.0, model.error_rate + 0.1)  # Quickly increase
            
        # Update performance score
        if success and latency < 2.0:  # Good performance
            model.performance_score = min(1.0, model.performance_score + 0.05)
        elif not success or latency > 10.0:  # Poor performance
            model.performance_score = max(0.1, model.performance_score - 0.1)
            
        # Record in history
        self.performance_history[model_id].append((datetime.utcnow(), latency))
        
        # Keep only recent history (last hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.performance_history[model_id] = [
            (ts, lat) for ts, lat in self.performance_history[model_id]
            if ts > cutoff
        ]
        
    async def get_model_stats(self) -> Dict[str, Any]:
        """Get comprehensive model statistics"""
        stats = {
            "total_models": len(self.models),
            "backends": defaultdict(int),
            "capabilities": defaultdict(int),
            "models": []
        }
        
        for model_id, model in self.models.items():
            stats["backends"][model.backend] += 1
            
            for capability in model.capabilities:
                stats["capabilities"][capability.name] += 1
                
            model_stats = {
                "model_id": model_id,
                "backend": model.backend,
                "capabilities": [c.name for c in model.capabilities],
                "context_length": model.context_length,
                "performance_score": round(model.performance_score, 3),
                "error_rate": round(model.error_rate, 3),
                "avg_latency": round(model.avg_latency, 3),
                "last_used": model.last_used.isoformat() if model.last_used else None,
                "recent_requests": len(self.performance_history.get(model_id, []))
            }
            
            stats["models"].append(model_stats)
            
        # Convert defaultdicts to regular dicts
        stats["backends"] = dict(stats["backends"])
        stats["capabilities"] = dict(stats["capabilities"])
        
        return stats
        
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all registered models"""
        health_results = {
            "router_status": "healthy",
            "total_models": len(self.models),
            "healthy_models": 0,
            "unhealthy_models": 0,
            "model_health": {}
        }
        
        for model_id, model in self.models.items():
            try:
                # Quick health check based on backend
                if model.backend == "ollama":
                    endpoint = f"{model.endpoint}/api/generate"
                    payload = {
                        "model": model.model_id.replace("ollama/", ""),
                        "prompt": "Hello",
                        "options": {"num_predict": 1}
                    }
                elif model.backend == "lmstudio":
                    endpoint = f"{model.endpoint}/v1/completions"
                    payload = {
                        "model": model.model_id.replace("lmstudio/", ""),
                        "prompt": "Hello",
                        "max_tokens": 1
                    }
                else:
                    continue
                    
                start_time = time.time()
                async with self.session.post(endpoint, json=payload, timeout=5) as resp:
                    latency = time.time() - start_time
                    
                    if resp.status == 200:
                        health_results["healthy_models"] += 1
                        health_results["model_health"][model_id] = {
                            "status": "healthy",
                            "latency": round(latency, 3)
                        }
                    else:
                        health_results["unhealthy_models"] += 1
                        health_results["model_health"][model_id] = {
                            "status": "unhealthy",
                            "error": f"HTTP {resp.status}"
                        }
                        
            except Exception as e:
                health_results["unhealthy_models"] += 1
                health_results["model_health"][model_id] = {
                    "status": "error",
                    "error": str(e)
                }
                
        if health_results["healthy_models"] == 0:
            health_results["router_status"] = "critical"
        elif health_results["unhealthy_models"] > health_results["healthy_models"]:
            health_results["router_status"] = "degraded"
            
        return health_results
        
    async def cleanup(self):
        """Cleanup resources"""
        if self._discovery_task:
            self._discovery_task.cancel()
            
        if self.session:
            await self.session.close()
