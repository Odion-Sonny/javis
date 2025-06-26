"""
Command Line Interface
Provides interactive CLI for Jarvis AI Assistant.
"""

import asyncio
import logging
import sys
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
            "memory": self._show_memory,
            "config": self._show_config,
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
  help     - Show this help message
  exit     - Exit the application
  quit     - Exit the application
  status   - Show system status
  memory   - Show memory/conversation summary  
  config   - Show configuration
  clear    - Clear screen
  
You can also:
  - Ask questions: "What's the weather like?"
  - Request system info: "Show me system information"
  - Get file listings: "List files in current directory"
  - And much more!
  
Examples:
  "Hello Jarvis, how are you?"
  "What time is it?"
  "Help me find a file named config.json"
  "Run the command 'ls -la'"
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
            print(f"  • AI Provider: {self.jarvis.config.ai['provider']}")
            print(f"  • Voice enabled: {self.jarvis.config.voice.get('enabled', True)}")
            print(f"  • System tools enabled: {self.jarvis.config.system_tools['enabled']}")
            
            # Get system info
            system_info = self.jarvis.system_tools.get_system_info()
            if "error" not in system_info:
                print(f"  • CPU cores: {system_info.get('cpu_count', 'unknown')}")
                print(f"  • Memory available: {system_info.get('memory_available', 0) // (1024**3)} GB")
                print(f"  • Current user: {system_info.get('user', 'unknown')}")
                
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def _show_memory(self):
        """Show memory/conversation summary."""
        try:
            summary = asyncio.run(self.jarvis.memory_manager.get_conversation_summary())
            print("🧠 Memory Summary:")
            print(summary)
        except Exception as e:
            print(f"Error getting memory summary: {e}")
    
    def _show_config(self):
        """Show configuration (sanitized)."""
        try:
            print("⚙️  Configuration:")
            print(str(self.jarvis.config))
        except Exception as e:
            print(f"Error showing configuration: {e}")
    
    def _clear_screen(self):
        """Clear the screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')