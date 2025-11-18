"""
Ollama inference engine for Lucia AI
Optimized for macOS with automatic model management
"""

import ollama
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import InferenceEngine, Message, GenerationConfig

logger = logging.getLogger(__name__)

class OllamaEngine(InferenceEngine):
    """Ollama-based inference engine"""
    
    def __init__(self, model_id: str = "mistral", base_url: str = "http://localhost:11434"):
        super().__init__(model_id)
        self.base_url = base_url
        self.client = ollama.AsyncClient(host=base_url)
        
    async def initialize(self) -> None:
        """Initialize Ollama engine and ensure model is available"""
        try:
            # Check if Ollama is running
            await self._ensure_ollama_running()
            
            # Check if model exists, if not, pull it
            models = await self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            if self.model_id not in model_names:
                logger.info(f"Model {self.model_id} not found, pulling...")
                await self._pull_model_with_progress(self.model_id)
                
            self._initialized = True
            logger.info(f"Ollama engine initialized with model: {self.model_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama engine: {e}")
            raise
            
    async def _ensure_ollama_running(self) -> None:
        """Ensure Ollama service is running"""
        try:
            await self.client.list()
        except Exception:
            # Try to start Ollama
            logger.info("Starting Ollama service...")
            import subprocess
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            await asyncio.sleep(3)  # Wait for service to start
            
    async def _pull_model_with_progress(self, model_name: str) -> None:
        """Pull model with progress tracking"""
        stream = await self.client.pull(model_name, stream=True)
        
        async for chunk in stream:
            if 'status' in chunk:
                status = chunk['status']
                if 'completed' in chunk and 'total' in chunk:
                    progress = chunk['completed'] / chunk['total'] * 100
                    logger.info(f"Pulling {model_name}: {status} - {progress:.1f}%")
                else:
                    logger.info(f"Pulling {model_name}: {status}")
                    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate response using Ollama"""
        config = config or GenerationConfig()
        
        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = await self.client.chat(
            model=self.model_id,
            messages=ollama_messages,
            options={
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "num_predict": config.max_tokens,
                "seed": config.seed,
                "stop": config.stop_sequences
            }
        )
        
        return response['message']['content']
        
    async def stream_generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response generation"""
        config = config or GenerationConfig()
        
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        stream = await self.client.chat(
            model=self.model_id,
            messages=ollama_messages,
            stream=True,
            options={
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "num_predict": config.max_tokens,
                "seed": config.seed,
                "stop": config.stop_sequences
            }
        )
        
        async for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
                
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        try:
            info = await self.client.show(self.model_id)
            return {
                "model_id": self.model_id,
                "family": info.get("details", {}).get("family", "unknown"),
                "parameter_size": info.get("details", {}).get("parameter_size", "unknown"),
                "quantization": info.get("details", {}).get("quantization_level", "unknown"),
                "context_length": info.get("details", {}).get("context_length", 4096),
                "backend": "ollama"
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"model_id": self.model_id, "error": str(e)}
