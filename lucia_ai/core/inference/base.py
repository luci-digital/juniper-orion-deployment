"""
Base inference engine abstraction for Lucia AI
Provides unified interface for different inference backends
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InferenceBackend(str, Enum):
    """Supported inference backends"""
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    TRANSFORMERS = "transformers"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VLLM = "vllm"  # For future NVIDIA GPU support

@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    
@dataclass
class Message:
    """Chat message structure"""
    role: str  # system, user, assistant
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class InferenceEngine(ABC):
    """Abstract base class for inference engines"""
    
    def __init__(self, model_id: str, device: Optional[str] = None):
        self.model_id = model_id
        self.device = device or self._detect_device()
        self._initialized = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the inference engine"""
        pass
        
    @abstractmethod
    async def generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate a response"""
        pass
        
    @abstractmethod
    async def stream_generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response generation"""
        pass
        
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        pass
        
    def _detect_device(self) -> str:
        """Detect the best available device with universal hardware support"""
        import platform
        system = platform.system().lower()
        
        try:
            import torch
            
            # macOS with Apple Silicon (Metal Performance Shaders)
            if system == "darwin":
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    logger.info("Detected Apple Silicon GPU (Metal Performance Shaders)")
                    return "mps"
                else:
                    logger.info("Running on macOS CPU (MPS not available)")
                    return "cpu"
            
            # Linux/Windows with NVIDIA GPU
            elif torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown"
                logger.info(f"Detected NVIDIA GPU: {gpu_name}")
                return "cuda"
            
            # AMD ROCm support (for future compatibility)
            elif hasattr(torch, 'hip') and torch.hip.is_available():
                logger.info("Detected AMD GPU (ROCm)")
                return "rocm"
                
        except ImportError:
            logger.warning("PyTorch not installed, defaulting to CPU")
        except Exception as e:
            logger.warning(f"Error detecting hardware: {e}")
        
        logger.info(f"Using CPU for inference on {system}")
        return "cpu"
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the engine"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "model_id": self.model_id,
            "device": self.device,
            "backend": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
