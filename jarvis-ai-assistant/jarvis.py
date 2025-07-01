#!/usr/bin/env python3
"""
Jarvis AI Assistant - Main Application Class

This is the central orchestrator that ties everything together, providing:
- Initialization of all modules (AI, voice, system tools, memory, learning)
- Main conversation loop management
- Different input modes (text, voice, command line)
- Component coordination and communication
- Clean shutdown process
- Comprehensive error handling and logging
- Health monitoring and diagnostics
"""

import sys
import os
import signal
import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from jarvis.config import Config
    from jarvis.utils.logger import setup_logger
    from jarvis.memory.memory_system import MemorySystem, InteractionType, TaskStatus
    from jarvis.memory.migration import create_memory_system_with_migration
    from jarvis.ai_integration import AIBrain, IntentType
    from jarvis.voice.processor import VoiceProcessor
    from jarvis.system_tools.manager import SystemToolsManager
    from jarvis.learning import create_learning_module, LearningModule
    from jarvis.interfaces.cli import CLIInterface
except ImportError as e:
    print(f"Error importing Jarvis modules: {e}")
    print("Make sure you're running from the correct directory and have all dependencies installed.")
    sys.exit(1)


class OperationMode(Enum):
    """Available operation modes for Jarvis."""
    CLI = "cli"
    VOICE = "voice"
    DAEMON = "daemon"
    INTERACTIVE = "interactive"


class JarvisState(Enum):
    """Current state of the Jarvis application."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class HealthStatus:
    """Health status of Jarvis components."""
    overall_healthy: bool
    components: Dict[str, bool]
    last_check: datetime
    errors: List[str]
    warnings: List[str]


@dataclass
class SystemMetrics:
    """System performance metrics."""
    uptime: timedelta
    total_interactions: int
    successful_interactions: int
    avg_response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float


class JarvisApplication:
    """
    Main Jarvis AI Assistant Application Class
    
    This is the central orchestrator that manages all components and provides
    the main application lifecycle management.
    """
    
    def __init__(self, config_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the Jarvis application.
        
        Args:
            config_path: Path to configuration file
            debug: Enable debug logging
        """
        self.start_time = datetime.now()
        self.state = JarvisState.INITIALIZING
        self.mode = OperationMode.CLI
        self.debug = debug
        
        # Initialize logging first
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = setup_logger(log_level)
        self.logger.info("Starting Jarvis AI Assistant...")
        
        # Core components (will be initialized)
        self.config: Optional[Config] = None
        self.memory_system: Optional[MemorySystem] = None
        self.ai_brain: Optional[AIBrain] = None
        self.voice_processor: Optional[VoiceProcessor] = None
        self.system_tools: Optional[SystemToolsManager] = None
        self.learning_module: Optional[LearningModule] = None
        self.cli_interface: Optional[CLIInterface] = None
        
        # Application state
        self.is_running = False
        self.shutdown_requested = False
        self.health_status = HealthStatus(
            overall_healthy=False,
            components={},
            last_check=datetime.now(),
            errors=[],
            warnings=[]
        )
        
        # Performance tracking
        self.interaction_count = 0
        self.successful_interactions = 0
        self.response_times: List[float] = []
        
        # Threading for background tasks
        self.background_thread: Optional[threading.Thread] = None
        self.health_check_interval = 60  # seconds
        
        try:
            # Load configuration
            self._load_configuration(config_path)
            
            # Initialize components
            self._initialize_components()
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Perform initial health check
            self._perform_health_check()
            
            self.state = JarvisState.RUNNING
            self.logger.info("Jarvis AI Assistant initialized successfully")
            
        except Exception as e:
            self.state = JarvisState.ERROR
            self.logger.error(f"Failed to initialize Jarvis: {e}")
            if debug:
                raise
            sys.exit(1)
    
    def _load_configuration(self, config_path: Optional[str]):
        """Load and validate configuration."""
        try:
            self.config = Config(config_path)
            self.logger.info("Configuration loaded successfully")
            
            # Update health check interval from config
            self.health_check_interval = self.config.get('health_check_interval', 60)
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _initialize_components(self):
        """Initialize all Jarvis components."""
        try:
            self.logger.info("Initializing components...")
            
            # Initialize memory system with migration support
            self.logger.debug("Initializing memory system...")
            self.memory_system = create_memory_system_with_migration(self.config.memory)
            self.health_status.components['memory_system'] = True
            
            # Initialize AI brain
            self.logger.debug("Initializing AI brain...")
            self.ai_brain = AIBrain(self.config.ai, self.memory_system)
            
            # Perform async initialization (model preloading) in background
            def preload_in_background():
                try:
                    asyncio.run(self.ai_brain.initialize_async())
                except Exception as e:
                    self.logger.warning(f"AI brain async initialization failed: {e}")
            
            # Start preloading in a separate thread
            import threading
            preload_thread = threading.Thread(target=preload_in_background, daemon=True)
            preload_thread.start()
            
            self.health_status.components['ai_brain'] = True
            
            # Initialize voice processor
            self.logger.debug("Initializing voice processor...")
            try:
                self.voice_processor = VoiceProcessor(self.config.voice)
                self.health_status.components['voice_processor'] = True
            except Exception as e:
                self.logger.warning(f"Voice processor initialization failed: {e}")
                self.health_status.components['voice_processor'] = False
                self.health_status.warnings.append(f"Voice processing disabled: {e}")
            
            # Initialize system tools
            self.logger.debug("Initializing system tools...")
            self.system_tools = SystemToolsManager(self.config.system_tools)
            self.health_status.components['system_tools'] = True
            
            # Initialize learning module if enabled
            if self.config.learning.get('enabled', True):
                self.logger.debug("Initializing learning module...")
                try:
                    self.learning_module = create_learning_module(self.config.learning, self.memory_system)
                    self.health_status.components['learning_module'] = True
                except Exception as e:
                    self.logger.warning(f"Learning module initialization failed: {e}")
                    self.health_status.components['learning_module'] = False
                    self.health_status.warnings.append(f"Learning disabled: {e}")
            else:
                self.health_status.components['learning_module'] = False
                self.logger.info("Learning module disabled by configuration")
            
            # Initialize CLI interface
            self.logger.debug("Initializing CLI interface...")
            self.cli_interface = CLIInterface(self)
            self.health_status.components['cli_interface'] = True
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # On Windows, handle Ctrl+Break
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def run(self, mode: OperationMode = OperationMode.CLI) -> int:
        """
        Run the Jarvis application in the specified mode.
        
        Args:
            mode: Operation mode to run in
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if self.state != JarvisState.RUNNING:
            self.logger.error("Cannot run Jarvis - not in RUNNING state")
            return 1
        
        self.mode = mode
        self.is_running = True
        
        try:
            # Start background tasks
            self._start_background_tasks()
            
            # Run appropriate interface based on mode
            if mode == OperationMode.CLI:
                return self._run_cli_mode()
            elif mode == OperationMode.VOICE:
                return self._run_voice_mode()
            elif mode == OperationMode.DAEMON:
                return self._run_daemon_mode()
            elif mode == OperationMode.INTERACTIVE:
                return self._run_interactive_mode()
            else:
                self.logger.error(f"Unknown operation mode: {mode}")
                return 1
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            return 0
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            if self.debug:
                raise
            return 1
        finally:
            self.shutdown()
    
    def _run_cli_mode(self) -> int:
        """Run in CLI mode."""
        self.logger.info("Starting CLI mode...")
        try:
            if self.cli_interface:
                self.cli_interface.run()
            return 0
        except Exception as e:
            self.logger.error(f"CLI mode failed: {e}")
            return 1
    
    def _run_voice_mode(self) -> int:
        """Run in voice interaction mode."""
        self.logger.info("Starting voice mode...")
        
        if not self.voice_processor or not self.health_status.components.get('voice_processor', False):
            self.logger.error("Voice processor not available")
            return 1
        
        try:
            self.logger.info("Voice mode active. Say 'Jarvis' to get attention.")
            
            while self.is_running and not self.shutdown_requested:
                try:
                    # Listen for wake word or direct input
                    audio_input = self.voice_processor.listen()
                    
                    if audio_input:
                        # Convert speech to text
                        text = self.voice_processor.speech_to_text(audio_input)
                        
                        if text:
                            self.logger.debug(f"Voice input: {text}")
                            
                            # Process the command
                            response = asyncio.run(self.process_command(text))
                            
                            # Convert response to speech and play
                            self.voice_processor.text_to_speech(response)
                        
                except Exception as e:
                    self.logger.error(f"Voice processing error: {e}")
                    time.sleep(1)  # Brief pause before retrying
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Voice mode failed: {e}")
            return 1
    
    def _run_daemon_mode(self) -> int:
        """Run in daemon mode for background operation."""
        self.logger.info("Starting daemon mode...")
        
        try:
            # In daemon mode, we can:
            # 1. Monitor system events
            # 2. Run scheduled learning cycles
            # 3. Provide API endpoints
            # 4. Process background tasks
            
            while self.is_running and not self.shutdown_requested:
                try:
                    # Run learning cycle if enabled and due
                    if self.learning_module:
                        learning_status = self.learning_module.get_learning_status()
                        if learning_status.get('should_run_learning', False):
                            self.logger.info("Running scheduled learning cycle...")
                            result = self.learning_module.run_learning_cycle()
                            self.logger.info(f"Learning cycle completed: {result.get('status')}")
                    
                    # Perform health checks
                    self._perform_health_check()
                    
                    # Sleep for a while
                    time.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"Daemon mode error: {e}")
                    time.sleep(10)  # Longer pause on errors
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Daemon mode failed: {e}")
            return 1
    
    def _run_interactive_mode(self) -> int:
        """Run in interactive mode (enhanced CLI with voice)."""
        self.logger.info("Starting interactive mode...")
        
        try:
            print("🤖 Jarvis AI Assistant - Interactive Mode")
            print("You can type messages or speak (if voice is available)")
            print("Type 'help' for commands, or 'exit' to quit")
            print("-" * 50)
            
            while self.is_running and not self.shutdown_requested:
                try:
                    print("\n[Type or speak your message]")
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    
                    # Process the command
                    response = asyncio.run(self.process_command(user_input))
                    print(f"Jarvis: {response}")
                    
                    # Also speak the response if voice is available
                    if (self.voice_processor and 
                        self.health_status.components.get('voice_processor', False)):
                        try:
                            self.voice_processor.text_to_speech(response)
                        except Exception as e:
                            self.logger.debug(f"Text-to-speech failed: {e}")
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Interactive mode failed: {e}")
            return 1
    
    def _start_background_tasks(self):
        """Start background tasks."""
        if self.background_thread is None or not self.background_thread.is_alive():
            self.background_thread = threading.Thread(
                target=self._background_worker,
                daemon=True,
                name="JarvisBackgroundWorker"
            )
            self.background_thread.start()
            self.logger.debug("Background tasks started")
    
    def _background_worker(self):
        """Background worker for periodic tasks."""
        while self.is_running and not self.shutdown_requested:
            try:
                # Periodic health checks
                if datetime.now() - self.health_status.last_check > timedelta(seconds=self.health_check_interval):
                    self._perform_health_check()
                
                # Memory cleanup if needed
                if self.memory_system:
                    # Check if cleanup is needed (could be configurable)
                    stats = self.memory_system.get_memory_statistics()
                    if stats.get('total_conversations', 0) > 10000:  # Example threshold
                        self.logger.info("Running memory cleanup...")
                        self.memory_system.cleanup_old_data(days_to_keep=30)
                
                time.sleep(30)  # Background task interval
                
            except Exception as e:
                self.logger.error(f"Background worker error: {e}")
                time.sleep(60)  # Longer pause on errors
    
    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a user command and return the response.
        
        Args:
            command: User command/input
            context: Optional context information
            
        Returns:
            Response string
        """
        if not self.is_running or self.state != JarvisState.RUNNING:
            return "Sorry, I'm not ready to process commands right now."
        
        start_time = time.time()
        self.interaction_count += 1
        
        try:
            # Get conversation context from memory system
            conversation_context = []
            if self.memory_system:
                conversation_context = self.memory_system.get_conversation_context()
            
            # Process with AI brain
            if not self.ai_brain:
                return "Sorry, my AI brain is not available right now."
            
            ai_response = await self.ai_brain.process_message(command, context_override=context)
            
            # Store conversation in memory system
            if self.memory_system:
                conversation_id = self.memory_system.store_conversation(
                    user_input=command,
                    assistant_response=ai_response.content,
                    interaction_type=self._map_intent_to_interaction_type(ai_response.intent),
                    context_summary=str(context) if context else "",
                    sentiment_score=0.0,  # Could be enhanced
                    confidence_score=ai_response.confidence,
                    tokens_used=ai_response.tokens_used,
                    response_time=ai_response.response_time,
                    metadata=ai_response.metadata
                )
            
            response_content = ai_response.content
            
            # Check if system tools should be executed
            should_execute_tools = (
                ai_response.intent in [IntentType.SYSTEM_CONTROL, IntentType.COMMAND, IntentType.FILE_OPERATION] or
                (self.system_tools and self.system_tools.should_execute(response_content))
            )
            
            if should_execute_tools and self.system_tools:
                try:
                    tool_result = await self.system_tools.execute(response_content)
                    if tool_result:
                        response_content += f"\\n\\nSystem Result: {tool_result}"
                except Exception as e:
                    self.logger.error(f"System tool execution failed: {e}")
                    response_content += f"\\n\\nNote: System operation failed: {e}"
            
            # Track successful interaction
            self.successful_interactions += 1
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            # Keep only recent response times for performance calculation
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-50:]
            
            # Trigger learning if enabled
            if self.learning_module:
                try:
                    learning_status = self.learning_module.get_learning_status()
                    if learning_status.get('should_run_learning', False):
                        # Run learning in background
                        threading.Thread(
                            target=lambda: self.learning_module.run_learning_cycle(),
                            daemon=True
                        ).start()
                except Exception as e:
                    self.logger.warning(f"Learning trigger failed: {e}")
            
            return response_content
            
        except Exception as e:
            self.logger.error(f"Command processing failed: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _map_intent_to_interaction_type(self, intent: IntentType) -> InteractionType:
        """Map AI intent to memory system interaction type."""
        mapping = {
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
        return mapping.get(intent, InteractionType.CONVERSATION)
    
    def _perform_health_check(self):
        """Perform comprehensive health check of all components."""
        try:
            self.health_status.last_check = datetime.now()
            self.health_status.errors.clear()
            self.health_status.warnings.clear()
            
            # Check each component
            healthy_count = 0
            total_count = 0
            
            for component_name, is_healthy in self.health_status.components.items():
                total_count += 1
                if is_healthy:
                    healthy_count += 1
                else:
                    self.health_status.warnings.append(f"{component_name} is not healthy")
            
            # Check AI brain responsiveness
            if self.ai_brain:
                try:
                    status = self.ai_brain.get_provider_status()
                    available_providers = sum(1 for p in status.values() if p.get('available', False))
                    if available_providers == 0:
                        self.health_status.errors.append("No AI providers available")
                        self.health_status.components['ai_brain'] = False
                    else:
                        self.health_status.components['ai_brain'] = True
                except Exception as e:
                    self.health_status.errors.append(f"AI brain health check failed: {e}")
                    self.health_status.components['ai_brain'] = False
            
            # Check memory system
            if self.memory_system:
                try:
                    stats = self.memory_system.get_memory_statistics()
                    if 'error' in stats:
                        self.health_status.errors.append("Memory system error")
                        self.health_status.components['memory_system'] = False
                    else:
                        self.health_status.components['memory_system'] = True
                except Exception as e:
                    self.health_status.errors.append(f"Memory system health check failed: {e}")
                    self.health_status.components['memory_system'] = False
            
            # Overall health
            self.health_status.overall_healthy = len(self.health_status.errors) == 0
            
            # Log health status periodically
            if not self.health_status.overall_healthy:
                self.logger.warning(f"Health check issues: {self.health_status.errors}")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.health_status.overall_healthy = False
            self.health_status.errors.append(f"Health check system failure: {e}")
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status."""
        return self.health_status
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        return SystemMetrics(
            uptime=datetime.now() - self.start_time,
            total_interactions=self.interaction_count,
            successful_interactions=self.successful_interactions,
            avg_response_time=sum(self.response_times) / len(self.response_times) if self.response_times else 0.0,
            memory_usage_mb=self._get_memory_usage_mb(),
            cpu_usage_percent=self._get_cpu_usage_percent()
        )
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_cpu_usage_percent(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except:
            return 0.0
    
    def add_user_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Add user feedback for learning improvement."""
        try:
            if self.learning_module:
                return self.learning_module.add_feedback(feedback_data)
            return False
        except Exception as e:
            self.logger.error(f"Failed to add user feedback: {e}")
            return False
    
    def get_proactive_suggestions(self, context: str = "") -> List[Dict[str, Any]]:
        """Get proactive suggestions based on learned patterns."""
        try:
            if self.learning_module:
                return self.learning_module.get_proactive_suggestions(context)
            return []
        except Exception as e:
            self.logger.error(f"Failed to get proactive suggestions: {e}")
            return []
    
    def shutdown(self):
        """Perform graceful shutdown of all components."""
        if self.state == JarvisState.SHUTTING_DOWN:
            return  # Already shutting down
        
        self.logger.info("Initiating graceful shutdown...")
        self.state = JarvisState.SHUTTING_DOWN
        self.shutdown_requested = True
        self.is_running = False
        
        try:
            # Run final learning cycle if enabled
            if self.learning_module:
                try:
                    self.logger.info("Running final learning cycle...")
                    self.learning_module.run_learning_cycle(force=True)
                except Exception as e:
                    self.logger.warning(f"Final learning cycle failed: {e}")
            
            # Close memory system
            if self.memory_system:
                try:
                    self.memory_system.close()
                    self.logger.debug("Memory system closed")
                except Exception as e:
                    self.logger.error(f"Error closing memory system: {e}")
            
            # Cleanup other components
            if self.voice_processor:
                try:
                    # Voice processor cleanup if needed
                    pass
                except Exception as e:
                    self.logger.error(f"Error cleaning up voice processor: {e}")
            
            # Wait for background thread to finish
            if self.background_thread and self.background_thread.is_alive():
                self.background_thread.join(timeout=5)
            
            self.state = JarvisState.STOPPED
            self.logger.info("Jarvis AI Assistant shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.state = JarvisState.ERROR
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


def main():
    """Main entry point for the Jarvis application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Jarvis AI Assistant - Your intelligent companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jarvis.py --mode cli          # Start in CLI mode
  python jarvis.py --mode voice        # Start in voice mode  
  python jarvis.py --mode daemon       # Start as background daemon
  python jarvis.py --mode interactive  # Start in enhanced interactive mode
  python jarvis.py --debug             # Start with debug logging
        """
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["cli", "voice", "daemon", "interactive"],
        default="cli",
        help="Operation mode (default: cli)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Jarvis AI Assistant v2.0.0"
    )
    
    args = parser.parse_args()
    
    # Convert string mode to enum
    mode_map = {
        "cli": OperationMode.CLI,
        "voice": OperationMode.VOICE,
        "daemon": OperationMode.DAEMON,
        "interactive": OperationMode.INTERACTIVE
    }
    
    operation_mode = mode_map[args.mode]
    
    try:
        # Create and run Jarvis application
        with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
            exit_code = jarvis.run(operation_mode)
            sys.exit(exit_code)
            
    except KeyboardInterrupt:
        print("\\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()