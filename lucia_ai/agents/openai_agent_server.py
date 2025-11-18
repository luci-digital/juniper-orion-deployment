#!/usr/bin/env python3
"""
Enhanced Lucia Agent Server with OpenAI Model Support
Supports both local models (Ollama) and OpenAI models (GPT-4o, o1, etc.)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import tools
import sys
from pathlib import Path
# Add tools directory to path (relative to this file)
tools_dir = Path(__file__).parent.parent / 'tools'
sys.path.insert(0, str(tools_dir))
from openai_integration import LuciaOpenAIAgent, create_openai_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lucia AI - Enhanced Agent Server",
    description="AI agent server supporting both local and OpenAI models",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    model: Optional[str] = Field("mistral", description="Model to use")
    conversation_id: Optional[str] = Field("default", description="Conversation ID")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=128000, description="Max tokens")

class ChatResponse(BaseModel):
    response: str
    model: str
    conversation_id: str
    timestamp: str
    processing_time_ms: int
    usage: Optional[Dict] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    provider: str
    max_tokens: int
    capabilities: Dict[str, bool]

class ModelsListResponse(BaseModel):
    models: List[ModelInfo]
    total_count: int

# Global storage
openai_agents: Dict[str, LuciaOpenAIAgent] = {}
local_models = ["mistral", "llama3.2", "qwen2.5-coder", "codegemma", "phi3.5"]

async def get_openai_agent(model: str) -> LuciaOpenAIAgent:
    """Get or create OpenAI agent for specified model"""
    if model not in openai_agents:
        openai_agents[model] = create_openai_agent(model)
    return openai_agents[model]

async def chat_with_local_model(request: ChatRequest) -> ChatResponse:
    """Chat with local Ollama model"""
    import aiohttp
    start_time = datetime.now()
    
    payload = {
        "model": request.model,
        "prompt": request.message,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens or 2048
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:11434/api/generate", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return ChatResponse(
                    response=data["response"],
                    model=request.model,
                    conversation_id=request.conversation_id,
                    timestamp=datetime.utcnow().isoformat(),
                    processing_time_ms=processing_time
                )
            else:
                raise HTTPException(status_code=500, detail="Local model error")

async def chat_with_openai_model(request: ChatRequest) -> ChatResponse:
    """Chat with OpenAI model"""
    start_time = datetime.now()
    
    agent = await get_openai_agent(request.model)
    response_data = await agent.chat(
        message=request.message,
        conversation_id=request.conversation_id,
        temperature=request.temperature
    )
    
    if "error" in response_data:
        raise HTTPException(status_code=500, detail=response_data["error"])
    
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return ChatResponse(
        response=response_data["response"],
        model=request.model,
        conversation_id=response_data["conversation_id"],
        timestamp=response_data["timestamp"],
        processing_time_ms=processing_time,
        usage=response_data.get("usage")
    )

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Unified chat endpoint supporting both local and OpenAI models"""
    
    # Determine if it's an OpenAI model
    openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "o1-preview", "o1-mini"]
    
    if request.model in openai_models:
        return await chat_with_openai_model(request)
    elif request.model in local_models:
        return await chat_with_local_model(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {request.model}")

@app.get("/v1/models", response_model=ModelsListResponse)
async def list_models():
    """List all available models (local + OpenAI)"""
    models = []
    
    # Add local models
    for model in local_models:
        models.append(ModelInfo(
            id=model,
            name=model.title(),
            description=f"Local {model} model via Ollama",
            provider="ollama",
            max_tokens=4096,
            capabilities={"streaming": True, "local": True}
        ))
    
    # Add OpenAI models
    if os.getenv("OPENAI_API_KEY"):
        openai_models_info = [
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "description": "Most advanced GPT-4 model with multimodal capabilities",
                "max_tokens": 128000,
                "capabilities": {"vision": True, "tools": True, "streaming": True}
            },
            {
                "id": "gpt-4o-mini", 
                "name": "GPT-4o Mini",
                "description": "Faster, more cost-effective GPT-4o variant",
                "max_tokens": 128000,
                "capabilities": {"vision": True, "tools": True, "streaming": True}
            },
            {
                "id": "o1-preview",
                "name": "o1-preview", 
                "description": "Advanced reasoning model (o1 series)",
                "max_tokens": 32768,
                "capabilities": {"reasoning": True, "complex_tasks": True}
            },
            {
                "id": "o1-mini",
                "name": "o1-mini",
                "description": "Faster reasoning model (o1 series)", 
                "max_tokens": 65536,
                "capabilities": {"reasoning": True, "fast": True}
            }
        ]
        
        for model_info in openai_models_info:
            models.append(ModelInfo(
                id=model_info["id"],
                name=model_info["name"],
                description=model_info["description"],
                provider="openai",
                max_tokens=model_info["max_tokens"],
                capabilities=model_info["capabilities"]
            ))
    
    return ModelsListResponse(
        models=models,
        total_count=len(models)
    )

@app.post("/v1/chat/gpt4o")
async def chat_gpt4o(request: ChatRequest):
    """Direct endpoint for GPT-4o"""
    request.model = "gpt-4o"
    return await chat(request)

@app.post("/v1/chat/o1")  
async def chat_o1(request: ChatRequest):
    """Direct endpoint for o1-preview"""
    request.model = "o1-preview"
    return await chat(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "local_models": len(local_models),
        "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Lucia AI - Enhanced Agent Server",
        "version": "2.0.0",
        "models_endpoint": "/v1/models",
        "chat_endpoint": "/v1/chat",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "openai_agent_server:app",
        host="0.0.0.0",
        port=8092,
        reload=True,
        log_level="info"
    ) 