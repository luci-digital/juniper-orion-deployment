"""
Unified Inference Engine - Seamlessly integrates all inference backends
with intelligent routing and fallback mechanisms
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json
import logging
from datetime import datetime
import aiohttp

from .base import InferenceEngine, Message, GenerationConfig, InferenceBackend
from .model_router import IntelligentModelRouter, ModelCapability, RoutingDecision

logger = logging.getLogger(__name__)

class UnifiedInferenceEngine(InferenceEngine):
    """
    Unified engine that intelligently routes between Ollama, LM Studio,
    and other backends with automatic failover
    """
    
    def __init__(self, routing_strategy: str = "capability"):
        super().__init__(model_id="unified", device="auto")
        self.router = IntelligentModelRouter()
        self.routing_strategy = routing_strategy
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize unified engine and discover models"""
        self.session = aiohttp.ClientSession()
        await self.router.initialize()
        self._initialized = True
        
        # Log discovered models
        stats = await self.router.get_model_stats()
        logger.info(f"Unified engine initialized with {stats['total_models']} models")
        for backend, count in stats['backends'].items():
            logger.info(f"  {backend}: {count} models")
            
    def _determine_capabilities(self, messages: List[Message]) -> set[ModelCapability]:
        """Analyze messages to determine required capabilities"""
        capabilities = {ModelCapability.CHAT}
        
        # Analyze message content
        all_content = " ".join(msg.content.lower() for msg in messages)
        
        # Code detection
        code_indicators = ["```", "def ", "function", "class ", "import ", "code", "debug", "implement"]
        if any(indicator in all_content for indicator in code_indicators):
            capabilities.add(ModelCapability.CODE)
            
        # Analysis detection
        analysis_indicators = ["analyze", "explain", "compare", "evaluate", "assess"]
        if any(indicator in all_content for indicator in analysis_indicators):
            capabilities.add(ModelCapability.ANALYSIS)
            
        # Creative detection
        creative_indicators = ["story", "poem", "creative", "imagine", "write", "compose"]
        if any(indicator in all_content for indicator in creative_indicators):
            capabilities.add(ModelCapability.CREATIVE)
            
        # Long context detection
        total_length = sum(len(msg.content) for msg in messages)
        if total_length > 2000:
            capabilities.add(ModelCapability.LONG_CONTEXT)
            
        return capabilities
        
    async def _call_ollama(
        self,
        model_name: str,
        messages: List[Message],
        config: GenerationConfig,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call Ollama backend"""
        endpoint = "http://localhost:11434/api/chat"
        
        # Format messages for Ollama
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model_name,
            "messages": ollama_messages,
            "stream": stream,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
                "stop": config.stop_sequences
            }
        }
        
        if stream:
            async def stream_generator():
                async with self.session.post(endpoint, json=payload) as resp:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
                                
            return stream_generator()
        else:
            async with self.session.post(endpoint, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Ollama error: {text}")
                    
                data = await resp.json()
                return data["message"]["content"]
                
    async def _call_lmstudio(
        self,
        model_name: str,
        messages: List[Message],
        config: GenerationConfig,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call LM Studio backend"""
        endpoint = "http://localhost:1234/v1/chat/completions"
        
        # Format messages for LM Studio (OpenAI compatible)
        lm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model_name,
            "messages": lm_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": stream,
            "stop": config.stop_sequences
        }
        
        if stream:
            async def stream_generator():
                async with self.session.post(endpoint, json=payload) as resp:
                    async for line in resp.content:
                        if line and line.startswith(b"data: "):
                            data_str = line[6:].decode('utf-8').strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and data["choices"]:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
            return stream_generator()
        else:
            async with self.session.post(endpoint, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"LM Studio error: {text}")
                    
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
                
    async def generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate response with intelligent routing"""
        config = config or GenerationConfig()
        
        # Determine required capabilities
        capabilities = self._determine_capabilities(messages)
        
        # Get routing decision
        decision = self.router.route_request(
            required_capabilities=capabilities,
            min_context_length=len(str(messages)) * 2  # Rough estimate
        )
        
        logger.info(f"Routed to {decision.model_profile.model_id} "
                   f"(score: {decision.score:.2f}, reasons: {', '.join(decision.reasoning)})")
        
        # Try primary model
        start_time = time.time()
        last_error = None
        
        for model in [decision.model_profile] + decision.fallback_options:
            try:
                # Extract model name without backend prefix
                model_name = model.model_id.split("/", 1)[1]
                
                # Call appropriate backend
                if model.backend == "ollama":
                    response = await self._call_ollama(model_name, messages, config)
                elif model.backend == "lmstudio":
                    response = await self._call_lmstudio(model_name, messages, config)
                else:
                    logger.warning(f"Unknown backend: {model.backend}")
                    continue
                    
                # Update performance metrics
                latency = time.time() - start_time
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=latency,
                    success=True
                )
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {model.model_id}: {e}")
                
                # Update failure metrics
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=time.time() - start_time,
                    success=False
                )
                
                # Try next model
                continue
                
        # All models failed
        raise RuntimeError(f"All models failed. Last error: {last_error}")
        
    async def stream_generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response with intelligent routing"""
        config = config or GenerationConfig()
        
        # Determine required capabilities
        capabilities = self._determine_capabilities(messages)
        
        # Get routing decision
        decision = self.router.route_request(
            required_capabilities=capabilities,
            min_context_length=len(str(messages)) * 2
        )
        
        logger.info(f"Streaming from {decision.model_profile.model_id}")
        
        # Try primary model
        start_time = time.time()
        
        for model in [decision.model_profile] + decision.fallback_options:
            try:
                # Extract model name without backend prefix
                model_name = model.model_id.split("/", 1)[1]
                
                # Get stream generator
                if model.backend == "ollama":
                    stream = await self._call_ollama(model_name, messages, config, stream=True)
                elif model.backend == "lmstudio":
                    stream = await self._call_lmstudio(model_name, messages, config, stream=True)
                else:
                    continue
                    
                # Stream response
                token_count = 0
                async for chunk in stream:
                    token_count += 1
                    yield chunk
                    
                # Update success metrics
                latency = time.time() - start_time
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=latency,
                    success=True,
                    tokens_generated=token_count
                )
                
                return
                
            except Exception as e:
                logger.warning(f"Streaming failed with {model.model_id}: {e}")
                
                # Update failure metrics
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=time.time() - start_time,
                    success=False
                )
                
                # Try next model
                continue
                
        # All models failed
        yield "\n\nError: All models failed to generate response."
        
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about all available models"""
        stats = await self.router.get_model_stats()
        health = await self.router.health_check()
        
        return {
            "engine": "unified",
            "routing_strategy": self.routing_strategy,
            "total_models": stats["total_models"],
            "backends": stats["backends"],
            "capabilities": stats["capabilities"],
            "health": health["router_status"],
            "healthy_models": health["healthy_models"],
            "models": stats["models"]
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        base_health = await super().health_check()
        router_health = await self.router.health_check()
        
        return {
            **base_health,
            "router_health": router_health,
            "available_backends": list(router_health.get("backends", {}).keys()),
            "model_count": router_health.get("total_models", 0)
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.router.cleanup()
        if self.session:
            await self.session.close()
EOFcat > ~/workspace/lucia/core/inference/unified_engine.py << 'EOF'
"""
Unified Inference Engine - Seamlessly integrates all inference backends
with intelligent routing and fallback mechanisms
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json
import logging
from datetime import datetime
import aiohttp

from .base import InferenceEngine, Message, GenerationConfig, InferenceBackend
from .model_router import IntelligentModelRouter, ModelCapability, RoutingDecision

logger = logging.getLogger(__name__)

class UnifiedInferenceEngine(InferenceEngine):
    """
    Unified engine that intelligently routes between Ollama, LM Studio,
    and other backends with automatic failover
    """
    
    def __init__(self, routing_strategy: str = "capability"):
        super().__init__(model_id="unified", device="auto")
        self.router = IntelligentModelRouter()
        self.routing_strategy = routing_strategy
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize unified engine and discover models"""
        self.session = aiohttp.ClientSession()
        await self.router.initialize()
        self._initialized = True
        
        # Log discovered models
        stats = await self.router.get_model_stats()
        logger.info(f"Unified engine initialized with {stats['total_models']} models")
        for backend, count in stats['backends'].items():
            logger.info(f"  {backend}: {count} models")
            
    def _determine_capabilities(self, messages: List[Message]) -> set[ModelCapability]:
        """Analyze messages to determine required capabilities"""
        capabilities = {ModelCapability.CHAT}
        
        # Analyze message content
        all_content = " ".join(msg.content.lower() for msg in messages)
        
        # Code detection
        code_indicators = ["```", "def ", "function", "class ", "import ", "code", "debug", "implement"]
        if any(indicator in all_content for indicator in code_indicators):
            capabilities.add(ModelCapability.CODE)
            
        # Analysis detection
        analysis_indicators = ["analyze", "explain", "compare", "evaluate", "assess"]
        if any(indicator in all_content for indicator in analysis_indicators):
            capabilities.add(ModelCapability.ANALYSIS)
            
        # Creative detection
        creative_indicators = ["story", "poem", "creative", "imagine", "write", "compose"]
        if any(indicator in all_content for indicator in creative_indicators):
            capabilities.add(ModelCapability.CREATIVE)
            
        # Long context detection
        total_length = sum(len(msg.content) for msg in messages)
        if total_length > 2000:
            capabilities.add(ModelCapability.LONG_CONTEXT)
            
        return capabilities
        
    async def _call_ollama(
        self,
        model_name: str,
        messages: List[Message],
        config: GenerationConfig,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call Ollama backend"""
        endpoint = "http://localhost:11434/api/chat"
        
        # Format messages for Ollama
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model_name,
            "messages": ollama_messages,
            "stream": stream,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
                "stop": config.stop_sequences
            }
        }
        
        if stream:
            async def stream_generator():
                async with self.session.post(endpoint, json=payload) as resp:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
                                
            return stream_generator()
        else:
            async with self.session.post(endpoint, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Ollama error: {text}")
                    
                data = await resp.json()
                return data["message"]["content"]
                
    async def _call_lmstudio(
        self,
        model_name: str,
        messages: List[Message],
        config: GenerationConfig,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Call LM Studio backend"""
        endpoint = "http://localhost:1234/v1/chat/completions"
        
        # Format messages for LM Studio (OpenAI compatible)
        lm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model_name,
            "messages": lm_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": stream,
            "stop": config.stop_sequences
        }
        
        if stream:
            async def stream_generator():
                async with self.session.post(endpoint, json=payload) as resp:
                    async for line in resp.content:
                        if line and line.startswith(b"data: "):
                            data_str = line[6:].decode('utf-8').strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and data["choices"]:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
            return stream_generator()
        else:
            async with self.session.post(endpoint, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"LM Studio error: {text}")
                    
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
                
    async def generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate response with intelligent routing"""
        config = config or GenerationConfig()
        
        # Determine required capabilities
        capabilities = self._determine_capabilities(messages)
        
        # Get routing decision
        decision = self.router.route_request(
            required_capabilities=capabilities,
            min_context_length=len(str(messages)) * 2  # Rough estimate
        )
        
        logger.info(f"Routed to {decision.model_profile.model_id} "
                   f"(score: {decision.score:.2f}, reasons: {', '.join(decision.reasoning)})")
        
        # Try primary model
        start_time = time.time()
        last_error = None
        
        for model in [decision.model_profile] + decision.fallback_options:
            try:
                # Extract model name without backend prefix
                model_name = model.model_id.split("/", 1)[1]
                
                # Call appropriate backend
                if model.backend == "ollama":
                    response = await self._call_ollama(model_name, messages, config)
                elif model.backend == "lmstudio":
                    response = await self._call_lmstudio(model_name, messages, config)
                else:
                    logger.warning(f"Unknown backend: {model.backend}")
                    continue
                    
                # Update performance metrics
                latency = time.time() - start_time
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=latency,
                    success=True
                )
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {model.model_id}: {e}")
                
                # Update failure metrics
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=time.time() - start_time,
                    success=False
                )
                
                # Try next model
                continue
                
        # All models failed
        raise RuntimeError(f"All models failed. Last error: {last_error}")
        
    async def stream_generate(
        self,
        messages: List[Message],
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response with intelligent routing"""
        config = config or GenerationConfig()
        
        # Determine required capabilities
        capabilities = self._determine_capabilities(messages)
        
        # Get routing decision
        decision = self.router.route_request(
            required_capabilities=capabilities,
            min_context_length=len(str(messages)) * 2
        )
        
        logger.info(f"Streaming from {decision.model_profile.model_id}")
        
        # Try primary model
        start_time = time.time()
        
        for model in [decision.model_profile] + decision.fallback_options:
            try:
                # Extract model name without backend prefix
                model_name = model.model_id.split("/", 1)[1]
                
                # Get stream generator
                if model.backend == "ollama":
                    stream = await self._call_ollama(model_name, messages, config, stream=True)
                elif model.backend == "lmstudio":
                    stream = await self._call_lmstudio(model_name, messages, config, stream=True)
                else:
                    continue
                    
                # Stream response
                token_count = 0
                async for chunk in stream:
                    token_count += 1
                    yield chunk
                    
                # Update success metrics
                latency = time.time() - start_time
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=latency,
                    success=True,
                    tokens_generated=token_count
                )
                
                return
                
            except Exception as e:
                logger.warning(f"Streaming failed with {model.model_id}: {e}")
                
                # Update failure metrics
                await self.router.update_performance_metrics(
                    model_id=model.model_id,
                    latency=time.time() - start_time,
                    success=False
                )
                
                # Try next model
                continue
                
        # All models failed
        yield "\n\nError: All models failed to generate response."
        
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about all available models"""
        stats = await self.router.get_model_stats()
        health = await self.router.health_check()
        
        return {
            "engine": "unified",
            "routing_strategy": self.routing_strategy,
            "total_models": stats["total_models"],
            "backends": stats["backends"],
            "capabilities": stats["capabilities"],
            "health": health["router_status"],
            "healthy_models": health["healthy_models"],
            "models": stats["models"]
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        base_health = await super().health_check()
        router_health = await self.router.health_check()
        
        return {
            **base_health,
            "router_health": router_health,
            "available_backends": list(router_health.get("backends", {}).keys()),
            "model_count": router_health.get("total_models", 0)
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.router.cleanup()
        if self.session:
            await self.session.close()
