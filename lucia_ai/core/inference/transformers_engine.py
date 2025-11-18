"""
Transformers inference engine with Metal Performance Shaders support
Optimized for Apple Silicon Macs
"""

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TextIteratorStreamer,
    BitsAndBytesConfig
)
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
from threading import Thread
import logging

from .base import InferenceEngine, Message, GenerationConfig

logger = logging.getLogger(__name__)

class TransformersEngine(InferenceEngine):
    """Transformers-based inference engine with MPS support"""
    
    def __init__(
        self, 
        model_id: str = "microsoft/phi-2",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False
    ):
        super().__init__(model_id)
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self.model = None
        self.tokenizer = None
        
    async def initialize(self) -> None:
        """Initialize the transformers model"""
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            # Configure quantization if needed
            quantization_config = None
            if self.load_in_4bit or self.load_in_8bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=self.load_in_4bit,
                    load_in_8bit=self.load_in_8bit,
                    bnb_4bit_compute_dtype=torch.float16
                )
            
            # Determine device and dtype with universal hardware support
            if self.device == "mps":
                # Apple Silicon with Metal Performance Shaders
                device_map = {"": "mps"}
                torch_dtype = torch.float16
                logger.info("Using Apple Silicon GPU with Metal Performance Shaders")
            elif self.device == "cuda":
                # NVIDIA GPU
                device_map = "auto"
                torch_dtype = torch.float16
                logger.info(f"Using NVIDIA GPU with CUDA")
            elif self.device == "rocm":
                # AMD GPU with ROCm
                device_map = "auto"
                torch_dtype = torch.float16
                logger.info("Using AMD GPU with ROCm")
            else:
                # CPU fallback - works on all platforms
                device_map = {"": "cpu"}
                torch_dtype = torch.float32
                logger.info(f"Using CPU inference (platform: {self.device})")
                
            # Load model
            logger.info(f"Loading model {self.model_id} on {self.device}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map=device_map,
                torch_dtype=torch_dtype,
                quantization_config=quantization_config,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            self._initialized = True
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize transformers engine: {e}")
            raise
            
    def _format_messages(self, messages: List[Message]) -> str:
        """Format messages for the model"""
        # Try to use chat template if available
        if hasattr(self.tokenizer, 'chat_template') and self.tokenizer.chat_template:
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            return self.tokenizer.apply_chat_template(
                formatted_messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
        else:
            # Fallback formatting
            formatted = []
            for msg in messages:
                if msg.role == "system":
                    formatted.append(f"System: {msg.content}")
                elif msg.role == "user":
                    formatted.append(f"Human: {msg.content}")
                elif msg.role == "assistant":
                    formatted.append(f"Assistant: {msg.content}")
            formatted.append("Assistant:")
            return "\n\n".join(formatted)
            
    async def generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate response"""
        config = config or GenerationConfig()
        
        # Format input
        prompt = self._format_messages(messages)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.model.config.max_position_embeddings
        )
        
        # Move to device - universal hardware support
        if self.device in ["mps", "cuda", "rocm"]:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        # CPU tensors don't need to be moved
            
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
        # Decode
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        )
        
        return response.strip()
        
    async def stream_generate(
        self, 
        messages: List[Message], 
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response generation"""
        config = config or GenerationConfig()
        
        # Format input
        prompt = self._format_messages(messages)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.model.config.max_position_embeddings
        )
        
        # Move to device - universal hardware support
        if self.device in ["mps", "cuda", "rocm"]:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        # CPU tensors don't need to be moved
            
        # Create streamer
        streamer = TextIteratorStreamer(
            self.tokenizer, 
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Generation kwargs
        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )
        
        # Run generation in thread
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Stream tokens
        for token in streamer:
            yield token
            
        thread.join()
        
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if not self.model:
            return {"error": "Model not loaded"}
            
        config = self.model.config
        
        # Calculate model size
        param_count = sum(p.numel() for p in self.model.parameters())
        param_size_gb = param_count * 2 / (1024**3)  # Assuming fp16
        
        return {
            "model_id": self.model_id,
            "architecture": config.architectures[0] if hasattr(config, 'architectures') else "unknown",
            "hidden_size": getattr(config, 'hidden_size', None),
            "num_layers": getattr(config, 'num_hidden_layers', None),
            "num_heads": getattr(config, 'num_attention_heads', None),
            "vocab_size": getattr(config, 'vocab_size', None),
            "context_length": getattr(config, 'max_position_embeddings', None),
            "parameter_count": param_count,
            "parameter_size_gb": round(param_size_gb, 2),
            "device": str(self.device),
            "dtype": str(self.model.dtype),
            "quantization": {
                "4bit": self.load_in_4bit,
                "8bit": self.load_in_8bit
            }
        }
