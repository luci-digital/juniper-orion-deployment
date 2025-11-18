#!/usr/bin/env python3
"""
OpenAI API Integration for Lucia AI
Supports GPT-4.1, GPT-4o, and other OpenAI models
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class OpenAIEngine:
    """OpenAI API engine for accessing GPT-4.1, GPT-4o and other models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.available_models = {
            "gpt-4o": {
                "name": "GPT-4o",
                "description": "Most advanced GPT-4 model with multimodal capabilities",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True
            },
            "gpt-4o-mini": {
                "name": "GPT-4o Mini", 
                "description": "Faster, more cost-effective GPT-4o variant",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "description": "Latest GPT-4 with improved performance",
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_tools": True
            },
            "gpt-4": {
                "name": "GPT-4",
                "description": "Standard GPT-4 model",
                "max_tokens": 8192,
                "supports_vision": False,
                "supports_tools": True
            },
            "o1-preview": {
                "name": "o1-preview",
                "description": "Advanced reasoning model (o1 series)",
                "max_tokens": 32768,
                "supports_vision": False,
                "supports_tools": False
            },
            "o1-mini": {
                "name": "o1-mini",
                "description": "Faster reasoning model (o1 series)",
                "max_tokens": 65536,
                "supports_vision": False,
                "supports_tools": False
            }
        }
        
    async def list_models(self) -> List[Dict]:
        """List available OpenAI models"""
        return [
            {
                "id": model_id,
                "name": info["name"],
                "description": info["description"],
                "max_tokens": info["max_tokens"],
                "capabilities": {
                    "vision": info["supports_vision"],
                    "tools": info["supports_tools"]
                }
            }
            for model_id, info in self.available_models.items()
        ]
    
    async def chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """Make chat completion request to OpenAI API"""
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
            
        if model not in self.available_models:
            raise ValueError(f"Model {model} not supported. Available: {list(self.available_models.keys())}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if tools and self.available_models[model]["supports_tools"]:
            payload["tools"] = tools
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def stream_chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenAI API"""
        
        response = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        # Process streaming response
        for line in response:
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                except json.JSONDecodeError:
                    continue

class LuciaOpenAIAgent:
    """Lucia agent that uses OpenAI models"""
    
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.engine = OpenAIEngine(api_key)
        self.model = model
        self.conversation_history = {}
        
    async def chat(
        self,
        message: str,
        conversation_id: str = "default",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict:
        """Chat with OpenAI model"""
        
        # Get or create conversation history
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
            
        history = self.conversation_history[conversation_id]
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # Add conversation history
        messages.extend(history[-10:])  # Keep last 10 messages
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.engine.chat_completion(
                messages=messages,
                model=self.model,
                temperature=temperature
            )
            
            assistant_message = response["choices"][0]["message"]["content"]
            
            # Update conversation history
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "response": assistant_message,
                "model": self.model,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "usage": response.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return {
                "error": str(e),
                "model": self.model,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_models(self) -> List[Dict]:
        """Get available OpenAI models"""
        return await self.engine.list_models()

# Factory function for creating OpenAI agents
def create_openai_agent(model: str = "gpt-4o", api_key: Optional[str] = None) -> LuciaOpenAIAgent:
    """Create a Lucia OpenAI agent with specified model"""
    return LuciaOpenAIAgent(model=model, api_key=api_key)

# Predefined agents for different use cases
async def create_gpt4o_agent(api_key: Optional[str] = None) -> LuciaOpenAIAgent:
    """Create GPT-4o agent for advanced multimodal tasks"""
    return create_openai_agent("gpt-4o", api_key)

async def create_gpt4_turbo_agent(api_key: Optional[str] = None) -> LuciaOpenAIAgent:
    """Create GPT-4 Turbo agent for general tasks"""
    return create_openai_agent("gpt-4-turbo", api_key)

async def create_o1_agent(api_key: Optional[str] = None) -> LuciaOpenAIAgent:
    """Create o1-preview agent for advanced reasoning"""
    return create_openai_agent("o1-preview", api_key)

if __name__ == "__main__":
    # Test the OpenAI integration
    async def test_openai():
        agent = create_openai_agent("gpt-4o")
        models = await agent.get_models()
        print("Available OpenAI models:")
        for model in models:
            print(f"  - {model['name']}: {model['description']}")
        
        # Test chat (requires API key)
        if os.getenv("OPENAI_API_KEY"):
            response = await agent.chat("Hello! Test the OpenAI integration.")
            print(f"Response: {response}")
    
    asyncio.run(test_openai()) 