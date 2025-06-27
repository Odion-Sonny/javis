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
        
        # Initialize Ollama client
        self.client = None
        if OLLAMA_AVAILABLE:
            try:
                self.client = ollama.Client(host=self.base_url)
            except Exception as e:
                self.logger.error(f"Failed to initialize Ollama client: {e}")
        else:
            self.logger.warning("Ollama package not available. Install with: pip install ollama")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AIResponse:
        """Generate response using Ollama."""
        if not self.client:
            raise RuntimeError("Ollama client not initialized")
        
        start_time = time.time()
        
        try:
            # Convert messages to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Generate response
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=ollama_messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )
            
            response_time = time.time() - start_time
            content = response['message']['content']
            
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
                tokens_used=response.get('eval_count', 0),
                response_time=response_time,
                metadata={
                    'total_duration': response.get('total_duration', 0),
                    'load_duration': response.get('load_duration', 0),
                    'prompt_eval_count': response.get('prompt_eval_count', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not OLLAMA_AVAILABLE or not self.client:
            return False
        
        try:
            # Try to list models to check connectivity
            models = self.client.list()
            return len(models.get('models', [])) > 0
        except Exception as e:
            self.logger.warning(f"Ollama availability check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information."""
        if not self.client:
            return {}
        
        try:
            models = self.client.list()
            current_model = next(
                (m for m in models.get('models', []) if m['name'] == self.model),
                None
            )
            return current_model or {}
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
        
        # Simple keyword-based responses
        if 'hello' in last_message or 'hi' in last_message:
            content = "Hello! I'm Jarvis, your AI assistant. How can I help you today?"
            intent = IntentType.GREETING
        elif 'time' in last_message:
            content = f"The current time is {datetime.now().strftime('%H:%M:%S')}"
            intent = IntentType.INFORMATION
        elif 'weather' in last_message:
            content = "I don't have access to current weather data, but I can help you set up weather integration!"
            intent = IntentType.INFORMATION
        elif any(word in last_message for word in ['run', 'execute', 'open']):
            content = "I can help you with system commands. What would you like me to do?"
            intent = IntentType.SYSTEM_CONTROL
        else:
            content = f"You said: '{messages[-1]['content']}'. I'm currently in mock mode. In production, I would process this with a real AI model."
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
                for category in ['voice', 'interface', 'behavior']:
                    prefs = self.memory_system.get_preferences_by_category(category)
                    preferences.extend([f"{p.key}: {p.value}" for p in prefs[:3]])
                
                if preferences:
                    pref_context = f"User preferences: {'; '.join(preferences)}"
                    messages.append({
                        'role': 'system',
                        'content': pref_context
                    })
                
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