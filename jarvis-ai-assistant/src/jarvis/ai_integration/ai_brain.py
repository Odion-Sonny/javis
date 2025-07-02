"""
AI Brain Module for Jarvis Assistant

This module provides a unified interface for AI processing, including:
- Local LLM inference via Ollama
- Fallback to cloud providers (OpenAI, Anthropic)
- Intent recognition and command parsing
- Context management for conversations
- Response generation with tone control

The module is designed to be provider-agnostic and easily extensible.
"""

import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta

# Import external dependencies conditionally
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class AIProvider(Enum):
    """Supported AI providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class IntentType(Enum):
    """Recognized intent types."""
    QUESTION = "question"
    COMMAND = "command"
    CONVERSATION = "conversation"
    SYSTEM_CONTROL = "system_control"
    FILE_OPERATION = "file_operation"
    INFORMATION = "information"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


class ResponseTone(Enum):
    """Response tone options."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CONCISE = "concise"
    DETAILED = "detailed"


@dataclass
class AIResponse:
    """Represents an AI response with metadata."""
    content: str
    intent: IntentType
    confidence: float
    tone: ResponseTone
    provider: AIProvider
    model: str
    tokens_used: int = 0
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content': self.content,
            'intent': self.intent.value,
            'confidence': self.confidence,
            'tone': self.tone.value,
            'provider': self.provider.value,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'response_time': self.response_time,
            'metadata': self.metadata
        }


@dataclass
class ConversationContext:
    """Manages conversation context and history."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    last_intent: Optional[IntentType] = None
    context_window: int = 10
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation history."""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.messages.append(message)
        
        # Maintain context window
        if len(self.messages) > self.context_window * 2:  # *2 for user+assistant pairs
            self.messages = self.messages[-self.context_window * 2:]
    
    def get_recent_messages(self, count: int = None) -> List[Dict[str, str]]:
        """Get recent messages for context."""
        if count is None:
            count = self.context_window
        return self.messages[-count:] if self.messages else []
    
    def clear_history(self):
        """Clear conversation history."""
        self.messages.clear()


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AIResponse:
        """Generate a response from the AI provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass


class OllamaProvider(BaseAIProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'llama2')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        
        # Initialize HTTP client for direct API calls
        self.client_available = AIOHTTP_AVAILABLE
        if not AIOHTTP_AVAILABLE:
            self.logger.warning("aiohttp package not available. Install with: pip install aiohttp")
    
    async def preload_model(self):
        """Preload the model to avoid cold start delays."""
        if not self.client_available:
            return False
        
        try:
            self.logger.info(f"Preloading Ollama model: {self.model}")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": "Hi",
                    "stream": False,
                    "options": {"num_predict": 1}  # Minimal generation
                }
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120.0)
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Model {self.model} preloaded successfully")
                        return True
                    else:
                        self.logger.warning(f"Preload failed with status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.warning(f"Failed to preload model {self.model}: {e}")
            return False
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AIResponse:
        """Generate response using Ollama via direct HTTP API."""
        if not self.client_available:
            raise RuntimeError("HTTP client not available")
        
        start_time = time.time()
        
        try:
            # Convert messages to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Convert messages to a single prompt (using generate API instead of chat API)
            prompt = ""
            for msg in ollama_messages:
                if msg['role'] == 'system':
                    prompt += f"System: {msg['content']}\n"
                elif msg['role'] == 'user':
                    prompt += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    prompt += f"Assistant: {msg['content']}\n"
            
            # Prepare request payload for generate API
            payload = {
                "model": self.model,
                "prompt": prompt.strip(),
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            # Make HTTP request with timeout
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180.0)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API returned status {response.status}: {error_text}")
                    
                    response_data = await response.json()
            
            response_time = time.time() - start_time
            content = response_data['response']
            
            # Analyze response for intent and tone
            intent = self._analyze_intent(content)
            tone = self._analyze_tone(content)
            
            return AIResponse(
                content=content,
                intent=intent,
                confidence=0.8,  # Ollama doesn't provide confidence scores
                tone=tone,
                provider=AIProvider.OLLAMA,
                model=self.model,
                tokens_used=response_data.get('eval_count', 0),
                response_time=response_time,
                metadata={
                    'total_duration': response_data.get('total_duration', 0),
                    'load_duration': response_data.get('load_duration', 0),
                    'prompt_eval_count': response_data.get('prompt_eval_count', 0)
                }
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"Ollama generation timed out after 180.0 seconds for model {self.model}")
            raise
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {type(e).__name__}: {e}")
            if hasattr(e, '__dict__'):
                self.logger.error(f"Error details: {e.__dict__}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not self.client_available:
            return False
        
        try:
            # Try to ping Ollama API to check connectivity
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama availability check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information."""
        if not self.client_available:
            return {}
        
        try:
            # Use HTTP request to get model info
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                # Handle both exact match and base model name match (e.g., llama2 matches llama2:latest)
                current_model = next(
                    (m for m in models_data.get('models', []) if m.get('name', '').startswith(self.model.split(':')[0])),
                    None
                )
                return current_model or {}
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {}
    
    def _analyze_intent(self, content: str) -> IntentType:
        """Analyze content to determine intent type."""
        content_lower = content.lower()
        
        # Simple rule-based intent recognition
        if any(word in content_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return IntentType.GREETING
        elif any(word in content_lower for word in ['bye', 'goodbye', 'farewell', 'exit']):
            return IntentType.GOODBYE
        elif any(word in content_lower for word in ['run', 'execute', 'open', 'launch']):
            return IntentType.SYSTEM_CONTROL
        elif any(word in content_lower for word in ['file', 'folder', 'directory', 'save', 'delete']):
            return IntentType.FILE_OPERATION
        elif content_lower.strip().endswith('?'):
            return IntentType.QUESTION
        elif any(word in content_lower for word in ['please', 'can you', 'could you', 'would you']):
            return IntentType.COMMAND
        else:
            return IntentType.CONVERSATION
    
    def _analyze_tone(self, content: str) -> ResponseTone:
        """Analyze content to determine appropriate tone."""
        content_lower = content.lower()
        
        # Simple tone analysis
        if len(content.split()) > 50:
            return ResponseTone.DETAILED
        elif any(word in content_lower for word in ['technical', 'implementation', 'algorithm']):
            return ResponseTone.TECHNICAL
        elif any(word in content_lower for word in ['thanks', 'please', 'appreciate']):
            return ResponseTone.FRIENDLY
        else:
            return ResponseTone.CASUAL


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        
        if not self.api_key:
            self.logger.warning("OpenAI API key not provided")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AIResponse:
        """Generate response using OpenAI API."""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp package not available. Install with: pip install aiohttp")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_time = time.time() - start_time
                        
                        choice = data['choices'][0]
                        content = choice['message']['content']
                        
                        return AIResponse(
                            content=content,
                            intent=self._analyze_intent(content),
                            confidence=0.9,
                            tone=self._analyze_tone(content),
                            provider=AIProvider.OPENAI,
                            model=data['model'],
                            tokens_used=data['usage']['total_tokens'],
                            response_time=response_time,
                            metadata={
                                'finish_reason': choice['finish_reason'],
                                'prompt_tokens': data['usage']['prompt_tokens'],
                                'completion_tokens': data['usage']['completion_tokens']
                            }
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
                        
        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return AIOHTTP_AVAILABLE and self.api_key is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            'name': self.model,
            'provider': 'openai',
            'type': 'cloud'
        }
    
    def _analyze_intent(self, content: str) -> IntentType:
        """Analyze content to determine intent type."""
        # Reuse Ollama's intent analysis
        return OllamaProvider._analyze_intent(self, content)
    
    def _analyze_tone(self, content: str) -> ResponseTone:
        """Analyze content to determine appropriate tone."""
        # Reuse Ollama's tone analysis
        return OllamaProvider._analyze_tone(self, content)


class MockProvider(BaseAIProvider):
    """Mock provider for testing and development."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.responses = config.get('mock_responses', {})
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AIResponse:
        """Generate mock response."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        last_message = messages[-1]['content'].lower() if messages else ""
        
        # Enhanced keyword-based responses with better pattern matching
        content, intent = self._generate_mock_response(last_message)
        
        # Fallback response
        if not content:
            content = f"I understand you're asking about '{messages[-1]['content']}'. As your AI assistant, I'm here to help with various tasks including system commands, information queries, and general conversation. What specific assistance do you need?"
            intent = IntentType.CONVERSATION
        
        return AIResponse(
            content=content,
            intent=intent,
            confidence=0.7,
            tone=ResponseTone.FRIENDLY,
            provider=AIProvider.MOCK,
            model="mock-model",
            tokens_used=len(content) // 4,
            response_time=0.1
        )
    
    def is_available(self) -> bool:
        """Mock provider is always available."""
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information."""
        return {
            'name': 'mock-model',
            'provider': 'mock',
            'type': 'development'
        }
    
    def _generate_mock_response(self, message: str) -> tuple[str, IntentType]:
        """Generate sophisticated mock responses based on message analysis."""
        import re
        
        # Greeting patterns
        greeting_patterns = [
            r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
            r'\bjarvis\b.*\b(hello|hi|hey)\b'
        ]
        
        # Question patterns
        question_patterns = [
            r'\bwhat\s+(is|are|was|were|time|weather|date)',
            r'\bhow\s+(do|can|to|are)',
            r'\bwhen\s+(is|are|will|did)',
            r'\bwhere\s+(is|are|can)',
            r'\bwhy\s+(is|are|do|did)'
        ]
        
        # Command patterns
        command_patterns = [
            r'\b(run|execute|start|launch|open|close|stop)\b',
            r'\b(create|make|build|generate|write)\b',
            r'\b(find|search|locate|look)\b',
            r'\b(help|assist|support)\b.*\bwith\b'
        ]
        
        # Time-related patterns
        time_patterns = [
            r'\b(time|clock|hour|minute|second)\b',
            r'\bwhat.*time\b'
        ]
        
        # System patterns
        system_patterns = [
            r'\b(system|computer|cpu|memory|disk|network)\b',
            r'\b(file|folder|directory|path)\b',
            r'\b(install|uninstall|update|upgrade)\b'
        ]
        
        # Check patterns and generate appropriate responses
        for pattern in greeting_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                greetings = [
                    "Hello! I'm Jarvis, your AI assistant. How can I help you today?",
                    "Hi there! I'm ready to assist you. What would you like to do?",
                    "Greetings! I'm here to help with whatever you need.",
                    "Hello! Nice to meet you. What can I do for you?"
                ]
                return greetings[hash(message) % len(greetings)], IntentType.GREETING
        
        for pattern in time_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                from datetime import datetime
                now = datetime.now()
                return f"The current time is {now.strftime('%I:%M:%S %p')} on {now.strftime('%A, %B %d, %Y')}", IntentType.INFORMATION
        
        for pattern in system_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                responses = [
                    "I can help you with system operations. What specific system task would you like me to perform?",
                    "System commands are one of my specialties. Please specify what you'd like me to do.",
                    "I'm ready to assist with system-level tasks. What do you need help with?"
                ]
                return responses[hash(message) % len(responses)], IntentType.SYSTEM_CONTROL
        
        for pattern in command_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                responses = [
                    "I can execute various commands and operations. What would you like me to run?",
                    "Command execution is available. Please specify the exact command or operation.",
                    "I'm ready to help with running commands. What should I execute for you?"
                ]
                return responses[hash(message) % len(responses)], IntentType.SYSTEM_CONTROL
        
        for pattern in question_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                responses = [
                    "That's an interesting question! While I'm in mock mode, I'd normally research that for you using my knowledge base and available tools.",
                    "I'd be happy to help answer that. In production mode, I would analyze your question and provide detailed information.",
                    "Great question! I would typically search through available resources and provide you with accurate information."
                ]
                return responses[hash(message) % len(responses)], IntentType.INFORMATION
        
        # Weather-specific response
        if re.search(r'\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b', message, re.IGNORECASE):
            return "I don't currently have access to weather data, but I can help you set up weather integration with APIs like OpenWeatherMap or AccuWeather!", IntentType.INFORMATION
        
        # Learning and memory patterns
        if re.search(r'\b(remember|learn|memorize|recall|forget)\b', message, re.IGNORECASE):
            return "I have learning capabilities that allow me to remember our conversations and adapt to your preferences. What would you like me to remember?", IntentType.LEARNING
        
        # Help patterns
        if re.search(r'\b(help|assist|support|guide|tutorial)\b', message, re.IGNORECASE):
            return "I'm here to help! I can assist with system commands, answer questions, manage files, set reminders, and much more. What specific help do you need?", IntentType.INFORMATION
        
        return "", IntentType.CONVERSATION


class AIBrain:
    """
    Main AI Brain class that orchestrates AI processing.
    
    This class provides a unified interface for:
    - AI provider management and fallback
    - Intent recognition and command parsing
    - Context management
    - Response generation with tone control
    """
    
    def __init__(self, config: Dict[str, Any], memory_system=None):
        """
        Initialize the AI Brain.
        
        Args:
            config: Configuration dictionary containing AI settings
            memory_system: Optional advanced memory system for enhanced context
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.memory_system = memory_system  # Enhanced memory system integration
        
        # Initialize providers
        self.providers: Dict[AIProvider, BaseAIProvider] = {}
        self._initialize_providers()
        
        # Set primary and fallback providers
        self.primary_provider = AIProvider(config.get('primary_provider', 'ollama'))
        self.fallback_providers = [
            AIProvider(p) for p in config.get('fallback_providers', ['openai', 'mock'])
        ]
        
        # Context management
        self.context = ConversationContext(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            context_window=config.get('context_window', 10)
        )
        
        # System prompt
        self.system_prompt = config.get('system_prompt', self._get_default_system_prompt())
        
        self.logger.info(f"AI Brain initialized with primary provider: {self.primary_provider.value}")
    
    async def initialize_async(self):
        """Perform async initialization tasks like model preloading."""
        try:
            # Preload the primary provider if it's Ollama
            if self.primary_provider == AIProvider.OLLAMA and AIProvider.OLLAMA in self.providers:
                ollama_provider = self.providers[AIProvider.OLLAMA]
                if hasattr(ollama_provider, 'preload_model'):
                    await ollama_provider.preload_model()
        except Exception as e:
            self.logger.warning(f"Async initialization failed: {e}")
    
    def set_memory_system(self, memory_system):
        """Set the memory system for enhanced context and learning."""
        self.memory_system = memory_system
        self.logger.info("Advanced memory system connected to AI Brain")
    
    def _initialize_providers(self):
        """Initialize all available AI providers."""
        try:
            # Ollama provider
            ollama_config = self.config.get('ollama', {})
            self.providers[AIProvider.OLLAMA] = OllamaProvider(ollama_config)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Ollama provider: {e}")
        
        try:
            # OpenAI provider
            openai_config = self.config.get('openai', {})
            self.providers[AIProvider.OPENAI] = OpenAIProvider(openai_config)
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        try:
            # Mock provider (always available)
            mock_config = self.config.get('mock', {})
            self.providers[AIProvider.MOCK] = MockProvider(mock_config)
        except Exception as e:
            self.logger.error(f"Failed to initialize Mock provider: {e}")
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return """You are Jarvis, an intelligent AI assistant created to help users with various tasks.

Key characteristics:
- You are helpful, harmless, and honest
- You can assist with questions, system operations, file management, and general conversation
- You should be concise but thorough in your responses
- When asked to perform system operations, provide clear instructions or ask for confirmation
- Maintain context from previous conversations
- Adapt your tone based on the user's communication style

Remember to:
- Ask for clarification when requests are ambiguous
- Provide step-by-step instructions for complex tasks
- Respect user privacy and security
- Acknowledge your limitations honestly"""
    
    async def process_message(
        self, 
        message: str, 
        user_id: str = "default",
        context_override: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            message: The user's input message
            user_id: Identifier for the user (for context management)
            context_override: Optional context to override defaults
            
        Returns:
            AIResponse object containing the generated response and metadata
        """
        try:
            # Add user message to context
            self.context.add_message('user', message)
            
            # Prepare messages for AI processing
            messages = self._prepare_messages(context_override)
            
            # Try to generate response with available providers
            response = await self._generate_with_fallback(messages)
            
            # Add assistant response to context
            self.context.add_message('assistant', response.content, {
                'intent': response.intent.value,
                'provider': response.provider.value,
                'model': response.model
            })
            
            # Update last intent
            self.context.last_intent = response.intent
            
            self.logger.info(f"Generated response using {response.provider.value} ({response.model})")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            # Return error response
            return AIResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                tone=ResponseTone.PROFESSIONAL,
                provider=AIProvider.MOCK,
                model="error-handler"
            )
    
    def _prepare_messages(self, context_override: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Prepare messages for AI processing with enhanced memory context."""
        messages = []
        
        # Add system prompt
        messages.append({
            'role': 'system',
            'content': self.system_prompt
        })
        
        # Add enhanced context from memory system if available
        if self.memory_system:
            try:
                # Get conversation context from advanced memory system
                memory_context = self.memory_system.get_conversation_context(
                    max_entries=self.context.context_window,
                    include_metadata=True
                )
                
                # Get user preferences for enhanced context
                preferences = []
                try:
                    # Try to get some common preferences
                    common_prefs = ['response_style', 'verbosity', 'tone', 'preferred_format']
                    for pref_key in common_prefs:
                        pref_value = self.memory_system.get_user_preference(pref_key)
                        if pref_value:
                            preferences.append(f"{pref_key}: {pref_value}")
                    
                    if preferences:
                        pref_context = f"User preferences: {'; '.join(preferences)}"
                        messages.append({
                            'role': 'system',
                            'content': pref_context
                        })
                except Exception as e:
                    self.logger.debug(f"Could not retrieve user preferences: {e}")
                
                # Get contextual suggestions
                suggestions = self.memory_system.get_contextual_suggestions("", 2)
                if suggestions:
                    suggestion_text = "Recent patterns: " + "; ".join([
                        s.get('type', 'unknown') for s in suggestions
                    ])
                    messages.append({
                        'role': 'system',
                        'content': suggestion_text
                    })
                
                # Use memory context instead of local context
                for ctx in memory_context[-self.context.context_window:]:
                    if ctx['role'] in ['user', 'assistant']:
                        messages.append({
                            'role': ctx['role'],
                            'content': ctx['content']
                        })
                        
            except Exception as e:
                self.logger.warning(f"Failed to get enhanced memory context: {e}")
                # Fall back to local context
                recent_messages = self.context.get_recent_messages()
                for msg in recent_messages:
                    if msg['role'] in ['user', 'assistant']:
                        messages.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
        else:
            # Add conversation history from local context
            recent_messages = self.context.get_recent_messages()
            for msg in recent_messages:
                if msg['role'] in ['user', 'assistant']:
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        
        # Add context override if provided
        if context_override:
            context_content = f"Additional context: {json.dumps(context_override, indent=2)}"
            messages.append({
                'role': 'system',
                'content': context_content
            })
        
        return messages
    
    async def _generate_with_fallback(self, messages: List[Dict[str, str]]) -> AIResponse:
        """Generate response with provider fallback."""
        # Try primary provider first
        if self.primary_provider in self.providers:
            provider = self.providers[self.primary_provider]
            if provider.is_available():
                try:
                    return await provider.generate_response(messages)
                except Exception as e:
                    self.logger.warning(f"Primary provider {self.primary_provider.value} failed: {e}")
        
        # Try fallback providers
        for fallback_provider in self.fallback_providers:
            if fallback_provider in self.providers:
                provider = self.providers[fallback_provider]
                if provider.is_available():
                    try:
                        self.logger.info(f"Using fallback provider: {fallback_provider.value}")
                        return await provider.generate_response(messages)
                    except Exception as e:
                        self.logger.warning(f"Fallback provider {fallback_provider.value} failed: {e}")
        
        # If all providers fail, raise an exception
        raise RuntimeError("All AI providers failed or are unavailable")
    
    def parse_command(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a message to extract commands and parameters.
        
        Note: This is a simple implementation. For advanced parsing,
        use the dedicated CommandParser module.
        
        Args:
            message: The input message to parse
            
        Returns:
            Tuple of (command, parameters)
        """
        # Simple command parsing - enhanced version available in command_parser.py
        message = message.strip().lower()
        
        # Command patterns
        patterns = {
            'open': r'open\s+(.+)',
            'run': r'run\s+(.+)',
            'execute': r'execute\s+(.+)',
            'search': r'search\s+(?:for\s+)?(.+)',
            'find': r'find\s+(.+)',
            'create': r'create\s+(.+)',
            'delete': r'delete\s+(.+)',
            'move': r'move\s+(.+)\s+to\s+(.+)',
            'copy': r'copy\s+(.+)\s+to\s+(.+)'
        }
        
        for command, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                return command, {'args': match.groups()}
        
        return 'unknown', {'original': message}
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers."""
        status = {}
        for provider_type, provider in self.providers.items():
            status[provider_type.value] = {
                'available': provider.is_available(),
                'model_info': provider.get_model_info()
            }
        return status
    
    def set_context_preference(self, key: str, value: Any):
        """Set a user preference in the context."""
        self.context.user_preferences[key] = value
    
    def get_context_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference from the context."""
        return self.context.user_preferences.get(key, default)
    
    def clear_context(self):
        """Clear the conversation context."""
        self.context.clear_history()
        self.logger.info("Conversation context cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation."""
        return {
            'session_id': self.context.session_id,
            'message_count': len(self.context.messages),
            'last_intent': self.context.last_intent.value if self.context.last_intent else None,
            'user_preferences': self.context.user_preferences,
            'primary_provider': self.primary_provider.value,
            'provider_status': self.get_provider_status()
        }


# Convenience function for easy initialization
def create_ai_brain(config: Dict[str, Any]) -> AIBrain:
    """
    Create and initialize an AI Brain instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized AIBrain instance
    """
    return AIBrain(config)