"""
Jarvis AI Assistant Core Module
Main orchestration and coordination logic.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .voice.processor import VoiceProcessor
from .ai_integration import AIBrain, IntentType
from .memory.memory_system import MemorySystem, ConversationEntry, InteractionType, TaskRecord, TaskStatus
from .memory.migration import create_memory_system_with_migration
from .learning import create_learning_module, LearningModule
from .system_tools.manager import SystemToolsManager
from .config import Config


class JarvisAssistant:
    """Main Jarvis AI Assistant class."""
    
    def __init__(self, config: Config):
        """Initialize Jarvis with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components with migration support
        self.voice_processor = VoiceProcessor(config.voice)
        self.memory_system = create_memory_system_with_migration(config.memory)
        self.ai_brain = AIBrain(config.ai, self.memory_system)
        self.system_tools = SystemToolsManager(config.system_tools)
        
        # Initialize learning module if enabled
        if config.learning.get('enabled', True):
            self.learning_module = create_learning_module(config.learning, self.memory_system)
        else:
            self.learning_module = None
        
        self.is_running = False
        self.logger.info("Jarvis AI Assistant initialized")
    
    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a command and return response."""
        try:
            # Get conversation context from advanced memory system
            conversation_context = self.memory_system.get_conversation_context()
            
            # Get AI response using the brain with enhanced context
            ai_response = await self.ai_brain.process_message(command, context_override=context)
            
            # Store conversation in advanced memory system
            conversation_id = self.memory_system.store_conversation(
                user_input=command,
                assistant_response=ai_response.content,
                interaction_type=self._map_intent_to_interaction_type(ai_response.intent),
                context_summary=str(context) if context else "",
                sentiment_score=0.0,  # Could be enhanced with sentiment analysis
                confidence_score=ai_response.confidence,
                tokens_used=ai_response.tokens_used,
                response_time=ai_response.response_time,
                metadata=ai_response.metadata
            )
            
            response_content = ai_response.content
            
            # Check if system tools need to be executed based on intent or content
            should_execute_tools = (
                ai_response.intent in [IntentType.SYSTEM_CONTROL, IntentType.COMMAND, IntentType.FILE_OPERATION] or
                self.system_tools.should_execute(response_content)
            )
            
            task_id = None
            if should_execute_tools:
                # Generate unique task ID
                task_id = f"task_{int(time.time())}_{hash(command) % 10000}"
                
                # Store task record
                self.memory_system.store_task_record(
                    task_id=task_id,
                    user_request=command,
                    task_type=ai_response.intent.value,
                    status=TaskStatus.REQUESTED,
                    started_at=datetime.now()
                )
                
                tool_result = await self.system_tools.execute(response_content)
                
                # Update task record with results
                self.memory_system.store_task_record(
                    task_id=task_id,
                    user_request=command,
                    task_type=ai_response.intent.value,
                    status=TaskStatus.COMPLETED if tool_result else TaskStatus.FAILED,
                    started_at=datetime.now() - timedelta(seconds=1),  # Approximation
                    completed_at=datetime.now(),
                    success=bool(tool_result),
                    result_data={'output': tool_result} if tool_result else {},
                    error_message=None if tool_result else "Tool execution failed"
                )
                
                if tool_result:
                    response_content += f"\n\nSystem Tool Result: {tool_result}"
            
            # Learn from the interaction patterns
            self._learn_from_interaction(command, ai_response, task_id)
            
            # Trigger learning cycle if enabled and due
            if self.learning_module:
                try:
                    learning_status = self.learning_module.get_learning_status()
                    if learning_status.get('should_run_learning', False):
                        asyncio.create_task(self._run_background_learning())
                except Exception as e:
                    self.logger.warning(f"Failed to check learning status: {e}")
            
            self.logger.info(f"Processed command with intent: {ai_response.intent.value}, "
                           f"confidence: {ai_response.confidence:.2f}, "
                           f"provider: {ai_response.provider.value}")
            
            return response_content
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _map_intent_to_interaction_type(self, intent: IntentType) -> InteractionType:
        """Map AI intent to memory system interaction type."""
        intent_mapping = {
            IntentType.QUESTION: InteractionType.QUESTION,
            IntentType.COMMAND: InteractionType.COMMAND,
            IntentType.CONVERSATION: InteractionType.CONVERSATION,
            IntentType.SYSTEM_CONTROL: InteractionType.TASK_REQUEST,
            IntentType.FILE_OPERATION: InteractionType.TASK_REQUEST,
            IntentType.INFORMATION: InteractionType.QUESTION,
            IntentType.GREETING: InteractionType.CONVERSATION,
            IntentType.GOODBYE: InteractionType.CONVERSATION,
            IntentType.UNKNOWN: InteractionType.CONVERSATION
        }
        return intent_mapping.get(intent, InteractionType.CONVERSATION)
    
    def _learn_from_interaction(self, command: str, ai_response, task_id: Optional[str]):
        """Learn user preferences and patterns from interactions."""
        try:
            # Extract potential preferences
            command_lower = command.lower()
            
            # Learn interface preferences
            if "make it" in command_lower or "prefer" in command_lower:
                # This would be enhanced with more sophisticated NLP
                pass
            
            # Learn task completion patterns
            if task_id and ai_response.confidence > 0.8:
                self.memory_system.learn_user_preference(
                    key=f"successful_task_{ai_response.intent.value}",
                    value="high_confidence",
                    category=self.memory_system.PreferenceCategory.AUTOMATION,
                    confidence=ai_response.confidence
                )
                
        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
    
    def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights from the memory system."""
        try:
            return {
                'statistics': self.memory_system.get_memory_statistics(),
                'patterns': self.memory_system.analyze_interaction_patterns(),
                'contextual_suggestions': self.memory_system.get_contextual_suggestions("general", 3)
            }
        except Exception as e:
            self.logger.error(f"Error getting memory insights: {e}")
            return {}
    
    def search_memory(self, query: str) -> Dict[str, Any]:
        """Search through memory for relevant information."""
        try:
            return self.memory_system.search_memory(query)
        except Exception as e:
            self.logger.error(f"Error searching memory: {e}")
            return {}
    
    async def _run_background_learning(self):
        """Run learning cycle in background."""
        try:
            if self.learning_module:
                result = self.learning_module.run_learning_cycle()
                self.logger.info(f"Background learning completed: {result.get('status')}")
        except Exception as e:
            self.logger.error(f"Background learning failed: {e}")
    
    def get_proactive_suggestions(self, context: str = "") -> List[Dict[str, Any]]:
        """Get proactive suggestions based on learned patterns."""
        try:
            if self.learning_module:
                return self.learning_module.get_proactive_suggestions(context)
            return []
        except Exception as e:
            self.logger.error(f"Error getting proactive suggestions: {e}")
            return []
    
    def add_user_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Add user feedback for learning improvement."""
        try:
            if self.learning_module:
                return self.learning_module.add_feedback(feedback_data)
            return False
        except Exception as e:
            self.logger.error(f"Error adding user feedback: {e}")
            return False
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from the learning module."""
        try:
            if self.learning_module:
                status = self.learning_module.get_learning_status()
                # Run a quick learning cycle to get fresh insights
                result = self.learning_module.run_learning_cycle(force=True)
                return {
                    'status': status,
                    'latest_results': result
                }
            return {'message': 'Learning module not enabled'}
        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return {'error': str(e)}
    
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
            self.memory_system.close()
            if self.learning_module:
                # Run final learning cycle before shutdown
                try:
                    self.learning_module.run_learning_cycle(force=True)
                except Exception as e:
                    self.logger.warning(f"Final learning cycle failed: {e}")
    
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