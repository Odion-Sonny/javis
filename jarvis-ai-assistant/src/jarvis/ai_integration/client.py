"""
AI Client Implementation
Handles communication with various AI service providers (OpenAI, Anthropic, etc.).
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AIResponse:
    """Represents an AI response."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any] = None


class AIClient:
    """Client for interacting with AI services."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AI client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        
        # System prompt
        self.system_prompt = config.get("system_prompt", 
            "You are Jarvis, an intelligent AI assistant. "
            "You are helpful, harmless, and honest. "
            "You can help with various tasks including answering questions, "
            "providing information, and assisting with system operations when appropriate."
        )
        
        self.logger.info(f"AI client initialized with provider: {self.provider}")
    
    async def get_response(
        self, 
        message: str, 
        context: Optional[List[Dict[str, Any]]] = None,
        memory_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get AI response for a message.
        
        Args:
            message: User message
            context: Additional context information
            memory_context: Conversation history from memory
            
        Returns:
            AI response text
        """
        try:
            # Build messages list
            messages = self._build_messages(message, context, memory_context)
            
            # Get response based on provider
            if self.provider.lower() == "openai":
                response = await self._get_openai_response(messages)
            elif self.provider.lower() == "anthropic":
                response = await self._get_anthropic_response(messages)
            else:
                # Fallback to mock response for development/testing
                response = await self._get_mock_response(message)
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _build_messages(
        self, 
        message: str, 
        context: Optional[List[Dict[str, Any]]] = None,
        memory_context: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build messages list for AI API."""
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Add memory context (conversation history)
        if memory_context:
            for interaction in memory_context[-10:]:  # Last 10 interactions
                messages.append({
                    "role": interaction["role"],
                    "content": interaction["content"]
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Add additional context if provided
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items() if isinstance(v, (str, int, float))])
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Additional context: {context_str}"
                })
        
        return messages
    
    async def _get_openai_response(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Get response from OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    choice = data["choices"][0]
                    
                    return AIResponse(
                        content=choice["message"]["content"],
                        model=data["model"],
                        tokens_used=data["usage"]["total_tokens"],
                        finish_reason=choice["finish_reason"]
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
    
    async def _get_anthropic_response(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Get response from Anthropic API."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        url = self.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages format for Anthropic
        system_messages = [msg["content"] for msg in messages if msg["role"] == "system"]
        user_messages = [msg for msg in messages if msg["role"] != "system"]
        
        payload = {
            "model": self.model or "claude-3-sonnet-20240229",
            "max_tokens": self.max_tokens,
            "system": " ".join(system_messages) if system_messages else None,
            "messages": user_messages
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return AIResponse(
                        content=data["content"][0]["text"],
                        model=data["model"],
                        tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
                        finish_reason=data["stop_reason"]
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
    
    async def _get_mock_response(self, message: str) -> AIResponse:
        """Generate a mock response for development/testing."""
        # Simple mock responses based on message content
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            content = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
        elif "time" in message_lower:
            from datetime import datetime
            content = f"The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif "weather" in message_lower:
            content = "I don't have access to current weather data yet, but I'd be happy to help you set up weather integration!"
        elif "system" in message_lower or "computer" in message_lower:
            content = "I can help you with system tasks! Try asking me to run a command or get system information."
        else:
            content = f"I understand you said: '{message}'. I'm currently running in development mode with mock responses. In a full implementation, I would process this request using a real AI service."
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        return AIResponse(
            content=content,
            model="mock-model",
            tokens_used=len(content) // 4,  # Rough estimate
            finish_reason="stop"
        )
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get text embedding (for future use in semantic search, etc.)."""
        try:
            if self.provider.lower() == "openai":
                return await self._get_openai_embedding(text)
            else:
                # Return mock embedding for development
                import random
                return [random.random() for _ in range(384)]
                
        except Exception as e:
            self.logger.error(f"Error getting embedding: {e}")
            return []
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-ada-002",
            "input": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["data"][0]["embedding"]
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI Embedding API error {response.status}: {error_text}")
    
    def validate_configuration(self) -> bool:
        """Validate AI client configuration."""
        if self.provider.lower() in ["openai", "anthropic"] and not self.api_key:
            self.logger.error(f"API key required for provider: {self.provider}")
            return False
        
        return True