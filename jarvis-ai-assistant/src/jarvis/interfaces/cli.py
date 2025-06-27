"""
Command Line Interface
Provides interactive CLI for Jarvis AI Assistant.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional
import readline  # For command history and editing


class CLIInterface:
    """Command line interface for Jarvis AI Assistant."""
    
    def __init__(self, jarvis_assistant):
        """Initialize CLI interface."""
        self.jarvis = jarvis_assistant
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # CLI commands
        self.commands = {
            "help": self._show_help,
            "exit": self._exit,
            "quit": self._exit,
            "status": self._show_status,
            "health": self._show_health,
            "metrics": self._show_metrics,
            "memory": self._show_memory,
            "config": self._show_config,
            "suggestions": self._show_suggestions,
            "feedback": self._give_feedback,
            "clear": self._clear_screen
        }
        
        self.logger.info("CLI interface initialized")
    
    def run(self):
        """Start the CLI interface."""
        self.running = True
        
        print("🤖 Jarvis AI Assistant - Interactive CLI")
        print("Type 'help' for commands or just start chatting!")
        print("Press Ctrl+C to exit")
        print("-" * 50)
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check for built-in CLI commands
                    if user_input.lower() in self.commands:
                        self.commands[user_input.lower()]()
                        continue
                    
                    # Process as regular command
                    response = asyncio.run(self.jarvis.process_command(user_input))
                    print(f"Jarvis: {response}")
                    print()
                    
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except EOFError:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    
        finally:
            self.running = False
    
    def _show_help(self):
        """Show help information."""
        help_text = """
Available Commands:
  help        - Show this help message
  exit/quit   - Exit the application
  status      - Show system status
  health      - Show component health status
  metrics     - Show performance metrics
  memory      - Show memory/conversation summary  
  config      - Show configuration
  suggestions - Show proactive suggestions
  feedback    - Give feedback on responses
  clear       - Clear screen
  
You can also:
  - Ask questions: "What's the weather like?"
  - Request system info: "Show me system information"
  - Get file listings: "List files in current directory"
  - Control system: "Open calculator"
  - Learn preferences: "I prefer dark mode"
  - And much more!
  
Examples:
  "Hello Jarvis, how are you?"
  "What time is it?"
  "Help me find a file named config.json"
  "Run the command 'ls -la'"
  "I like shorter responses"
  "Schedule a reminder for 3 PM"
        """
        print(help_text)
    
    def _exit(self):
        """Exit the CLI."""
        print("Shutting down Jarvis...")
        self.running = False
    
    def _show_status(self):
        """Show system status."""
        try:
            print("🔍 System Status:")
            print(f"  • Jarvis is running: {self.jarvis.is_running}")
            print(f"  • State: {self.jarvis.state.value if hasattr(self.jarvis, 'state') else 'unknown'}")
            print(f"  • Mode: {self.jarvis.mode.value if hasattr(self.jarvis, 'mode') else 'unknown'}")
            
            if hasattr(self.jarvis, 'config'):
                print(f"  • Primary AI Provider: {self.jarvis.config.ai.get('primary_provider', 'unknown')}")
                print(f"  • Voice enabled: {self.jarvis.config.voice.get('enabled', True)}")
                print(f"  • System tools enabled: {self.jarvis.config.system_tools.get('enabled', True)}")
                print(f"  • Learning enabled: {self.jarvis.config.learning.get('enabled', True)}")
            
            # Get AI Brain status
            if hasattr(self.jarvis, 'ai_brain') and self.jarvis.ai_brain:
                try:
                    ai_status = self.jarvis.ai_brain.get_provider_status()
                    print("\\n🧠 AI Providers:")
                    for provider, status in ai_status.items():
                        available = "✅" if status.get('available', False) else "❌"
                        model_info = status.get('model_info', {})
                        model_name = model_info.get('name', 'unknown')
                        print(f"  {available} {provider}: {model_name}")
                except Exception as e:
                    print(f"\\n🧠 AI Providers: Error getting status - {e}")
            
            # Get system info
            if hasattr(self.jarvis, 'system_tools') and self.jarvis.system_tools:
                try:
                    system_info = self.jarvis.system_tools.get_system_info()
                    if "error" not in system_info:
                        print(f"\\n💻 System Info:")
                        print(f"  • CPU cores: {system_info.get('cpu_count', 'unknown')}")
                        print(f"  • Memory available: {system_info.get('memory_available', 0) // (1024**3)} GB")
                        print(f"  • Current user: {system_info.get('user', 'unknown')}")
                except Exception as e:
                    print(f"\\n💻 System Info: Error getting info - {e}")
                
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def _show_health(self):
        """Show component health status."""
        try:
            if hasattr(self.jarvis, 'get_health_status'):
                health = self.jarvis.get_health_status()
                print("🏥 Health Status:")
                print(f"  • Overall: {'✅ Healthy' if health.overall_healthy else '❌ Unhealthy'}")
                print(f"  • Last check: {health.last_check.strftime('%Y-%m-%d %H:%M:%S')}")
                
                print("\\n📦 Components:")
                for component, is_healthy in health.components.items():
                    status = "✅" if is_healthy else "❌"
                    print(f"  {status} {component.replace('_', ' ').title()}")
                
                if health.errors:
                    print("\\n🚨 Errors:")
                    for error in health.errors:
                        print(f"  • {error}")
                
                if health.warnings:
                    print("\\n⚠️  Warnings:")
                    for warning in health.warnings:
                        print(f"  • {warning}")
            else:
                print("Health status not available")
        except Exception as e:
            print(f"Error getting health status: {e}")
    
    def _show_metrics(self):
        """Show performance metrics."""
        try:
            if hasattr(self.jarvis, 'get_system_metrics'):
                metrics = self.jarvis.get_system_metrics()
                print("📊 Performance Metrics:")
                print(f"  • Uptime: {metrics.uptime}")
                print(f"  • Total interactions: {metrics.total_interactions}")
                print(f"  • Successful interactions: {metrics.successful_interactions}")
                if metrics.total_interactions > 0:
                    success_rate = metrics.successful_interactions / metrics.total_interactions * 100
                    print(f"  • Success rate: {success_rate:.1f}%")
                print(f"  • Average response time: {metrics.avg_response_time:.2f}s")
                print(f"  • Memory usage: {metrics.memory_usage_mb:.1f} MB")
                print(f"  • CPU usage: {metrics.cpu_usage_percent:.1f}%")
            else:
                print("Metrics not available")
        except Exception as e:
            print(f"Error getting metrics: {e}")
    
    def _show_memory(self):
        """Show memory/conversation summary."""
        try:
            if hasattr(self.jarvis, 'memory_system') and self.jarvis.memory_system:
                stats = self.jarvis.memory_system.get_memory_statistics()
                print("🧠 Memory Summary:")
                print(f"  • Total conversations: {stats.get('total_conversations', 0)}")
                print(f"  • Recent conversations (7 days): {stats.get('recent_conversations', 0)}")
                print(f"  • Total tasks: {stats.get('total_tasks', 0)}")
                print(f"  • Task success rate: {stats.get('task_success_rate', 0):.1%}")
                print(f"  • Total preferences: {stats.get('total_preferences', 0)}")
                print(f"  • Avg preference confidence: {stats.get('avg_preference_confidence', 0):.2f}")
                print(f"  • Database size: {stats.get('database_size_bytes', 0) / 1024:.1f} KB")
                print(f"  • Current session: {stats.get('session_id', 'unknown')}")
            else:
                print("Memory system not available")
        except Exception as e:
            print(f"Error getting memory summary: {e}")
    
    def _show_suggestions(self):
        """Show proactive suggestions."""
        try:
            if hasattr(self.jarvis, 'get_proactive_suggestions'):
                suggestions = self.jarvis.get_proactive_suggestions()
                if suggestions:
                    print("💡 Proactive Suggestions:")
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"  {i}. {suggestion.get('content', 'No content')}")
                        print(f"     Type: {suggestion.get('suggestion_type', 'unknown')}")
                        print(f"     Confidence: {suggestion.get('confidence', 0):.2f}")
                        print()
                else:
                    print("💡 No suggestions available at this time")
            else:
                print("Suggestions not available")
        except Exception as e:
            print(f"Error getting suggestions: {e}")
    
    def _give_feedback(self):
        """Give feedback on responses."""
        try:
            print("📝 Feedback System:")
            print("Rate the last response (1-5, or 'skip'):")
            rating_input = input("Rating: ").strip()
            
            if rating_input.lower() == 'skip':
                print("Feedback skipped")
                return
            
            try:
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    print("Any specific comments? (optional, press Enter to skip):")
                    comment = input("Comment: ").strip()
                    
                    feedback_data = {
                        'feedback_type': 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral',
                        'rating': rating,
                        'comment': comment if comment else None,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if hasattr(self.jarvis, 'add_user_feedback'):
                        success = self.jarvis.add_user_feedback(feedback_data)
                        if success:
                            print("✅ Thank you for your feedback!")
                        else:
                            print("❌ Failed to record feedback")
                    else:
                        print("❌ Feedback system not available")
                else:
                    print("Please enter a rating between 1 and 5")
            except ValueError:
                print("Please enter a valid number")
                
        except Exception as e:
            print(f"Error with feedback: {e}")
    
    def _show_config(self):
        """Show configuration (sanitized)."""
        try:
            if hasattr(self.jarvis, 'config'):
                print("⚙️  Configuration:")
                print(f"  • AI Primary Provider: {self.jarvis.config.ai.get('primary_provider', 'unknown')}")
                print(f"  • AI Fallback Providers: {self.jarvis.config.ai.get('fallback_providers', [])}")
                print(f"  • Voice Engine: {self.jarvis.config.voice.get('engine', 'unknown')}")
                print(f"  • Memory Database: {self.jarvis.config.memory.get('db_path', 'unknown')}")
                print(f"  • Learning Enabled: {self.jarvis.config.learning.get('enabled', False)}")
                print(f"  • System Tools Enabled: {self.jarvis.config.system_tools.get('enabled', False)}")
            else:
                print("Configuration not available")
        except Exception as e:
            print(f"Error showing configuration: {e}")
    
    def _clear_screen(self):
        """Clear the screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')