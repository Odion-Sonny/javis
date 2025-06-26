"""
Jarvis AI Assistant Core Module
Main orchestration and coordination logic.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from .voice.processor import VoiceProcessor
from .ai_integration.client import AIClient
from .memory.manager import MemoryManager
from .system_tools.manager import SystemToolsManager
from .config import Config


class JarvisAssistant:
    """Main Jarvis AI Assistant class."""
    
    def __init__(self, config: Config):
        """Initialize Jarvis with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.voice_processor = VoiceProcessor(config.voice)
        self.ai_client = AIClient(config.ai)
        self.memory_manager = MemoryManager(config.memory)
        self.system_tools = SystemToolsManager(config.system_tools)
        
        self.is_running = False
        self.logger.info("Jarvis AI Assistant initialized")
    
    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a command and return response."""
        try:
            # Store command in memory
            await self.memory_manager.add_interaction(command, "user")
            
            # Get AI response
            response = await self.ai_client.get_response(
                command, 
                context=context,
                memory_context=await self.memory_manager.get_context()
            )
            
            # Store response in memory
            await self.memory_manager.add_interaction(response, "assistant")
            
            # Check if system tools need to be executed
            if self.system_tools.should_execute(response):
                tool_result = await self.system_tools.execute(response)
                if tool_result:
                    response += f"\n\nSystem Tool Result: {tool_result}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def start_voice_mode(self):
        """Start voice interaction mode."""
        self.logger.info("Starting voice mode...")
        self.is_running = True
        
        try:
            while self.is_running:
                # Listen for voice input
                audio_input = self.voice_processor.listen()
                if audio_input:
                    # Convert speech to text
                    text = self.voice_processor.speech_to_text(audio_input)
                    if text:
                        # Process command
                        response = asyncio.run(self.process_command(text))
                        
                        # Convert response to speech and play
                        self.voice_processor.text_to_speech(response)
                        
        except KeyboardInterrupt:
            self.logger.info("Voice mode interrupted by user")
        finally:
            self.is_running = False
    
    def start_daemon_mode(self):
        """Start daemon mode for background operation."""
        self.logger.info("Starting daemon mode...")
        self.is_running = True
        
        # Implementation for daemon mode
        # This could listen for system events, scheduled tasks, etc.
        try:
            while self.is_running:
                # Daemon logic here
                asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Daemon mode interrupted")
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the assistant."""
        self.logger.info("Stopping Jarvis AI Assistant...")
        self.is_running = False