#!/usr/bin/env python3
"""
Jarvis AI Assistant - Command-Line Management Interface

This module provides a professional command-line management interface for Jarvis with:
- Professional argument parsing with argparse
- Multiple operation modes (interactive, voice-only, command execution)
- Configuration management from command line
- Status reporting and diagnostics
- Comprehensive help system with examples
- Subcommand architecture for extensibility
"""

import sys
import os
import argparse
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import subprocess

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from jarvis.config import Config
    from jarvis.utils.logger import setup_logger
except ImportError as e:
    print(f"Error importing Jarvis modules: {e}")
    print("Make sure you're running from the correct directory and have all dependencies installed.")
    sys.exit(1)

# Version information
VERSION = "2.0.0"
DESCRIPTION = "Jarvis AI Assistant - Your intelligent companion"

class JarvisCLI:
    """
    Professional command-line interface for Jarvis AI Assistant.
    
    Provides comprehensive CLI functionality including configuration management,
    status reporting, diagnostics, and multiple operation modes.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.config: Optional[Config] = None
        self.logger: Optional[logging.Logger] = None
        self.jarvis_app = None
        
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the main argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog='jarvis',
            description=DESCRIPTION,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_usage_examples()
        )
        
        # Global options
        parser.add_argument(
            '--version',
            action='version',
            version=f'Jarvis AI Assistant v{VERSION}'
        )
        
        parser.add_argument(
            '--config',
            type=str,
            metavar='PATH',
            help='Path to configuration file'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Increase verbosity (use -v, -vv, or -vvv)'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress all output except errors'
        )
        
        parser.add_argument(
            '--log-file',
            type=str,
            metavar='PATH',
            help='Log file path (default: logs/jarvis.log)'
        )
        
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(
            dest='subcommand',
            title='Available Commands',
            description='Use "jarvis <command> --help" for detailed help on each command',
            help='Command to execute'
        )
        
        # Run command (default operation)
        self._add_run_parser(subparsers)
        
        # Configuration management
        self._add_config_parser(subparsers)
        
        # Status and diagnostics
        self._add_status_parser(subparsers)
        
        # Interactive shell
        self._add_shell_parser(subparsers)
        
        # Voice-only mode
        self._add_voice_parser(subparsers)
        
        # Command execution
        self._add_exec_parser(subparsers)
        
        # System management
        self._add_system_parser(subparsers)
        
        return parser
    
    def _add_run_parser(self, subparsers):
        """Add the run command parser."""
        run_parser = subparsers.add_parser(
            'run',
            help='Run Jarvis in specified mode',
            description='Start Jarvis AI Assistant in various operation modes'
        )
        
        run_parser.add_argument(
            '--mode',
            choices=['cli', 'voice', 'daemon', 'interactive'],
            default='cli',
            help='Operation mode (default: cli)'
        )
        
        run_parser.add_argument(
            '--background',
            action='store_true',
            help='Run in background (daemon mode)'
        )
        
        run_parser.add_argument(
            '--pid-file',
            type=str,
            metavar='PATH',
            help='PID file for daemon mode'
        )
    
    def _add_config_parser(self, subparsers):
        """Add the config command parser."""
        config_parser = subparsers.add_parser(
            'config',
            help='Manage configuration settings',
            description='View and modify Jarvis configuration'
        )
        
        config_subparsers = config_parser.add_subparsers(
            dest='config_action',
            title='Configuration Actions'
        )
        
        # Show config
        show_parser = config_subparsers.add_parser('show', help='Display current configuration')
        show_parser.add_argument(
            '--section',
            type=str,
            help='Show specific configuration section'
        )
        show_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        # Set config value
        set_parser = config_subparsers.add_parser('set', help='Set configuration value')
        set_parser.add_argument('key', help='Configuration key (use dot notation)')
        set_parser.add_argument('value', help='Configuration value')
        
        # Get config value
        get_parser = config_subparsers.add_parser('get', help='Get configuration value')
        get_parser.add_argument('key', help='Configuration key (use dot notation)')
        
        # Reset config
        reset_parser = config_subparsers.add_parser('reset', help='Reset configuration to defaults')
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm reset operation'
        )
        
        # Validate config
        config_subparsers.add_parser('validate', help='Validate current configuration')
    
    def _add_status_parser(self, subparsers):
        """Add the status command parser."""
        status_parser = subparsers.add_parser(
            'status',
            help='Show system status and diagnostics',
            description='Display Jarvis system status, health, and diagnostic information'
        )
        
        status_parser.add_argument(
            '--health',
            action='store_true',
            help='Show component health status'
        )
        
        status_parser.add_argument(
            '--metrics',
            action='store_true',
            help='Show performance metrics'
        )
        
        status_parser.add_argument(
            '--memory',
            action='store_true',
            help='Show memory system statistics'
        )
        
        status_parser.add_argument(
            '--ai',
            action='store_true',
            help='Show AI provider status'
        )
        
        status_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        status_parser.add_argument(
            '--watch',
            type=int,
            metavar='SECONDS',
            help='Continuously monitor status (refresh interval in seconds)'
        )
    
    def _add_shell_parser(self, subparsers):
        """Add the shell command parser."""
        shell_parser = subparsers.add_parser(
            'shell',
            help='Start interactive shell',
            description='Start an interactive Jarvis shell for ongoing conversations'
        )
        
        shell_parser.add_argument(
            '--voice',
            action='store_true',
            help='Enable voice interaction in shell'
        )
        
        shell_parser.add_argument(
            '--history',
            action='store_true',
            help='Load conversation history'
        )
    
    def _add_voice_parser(self, subparsers):
        """Add the voice command parser."""
        voice_parser = subparsers.add_parser(
            'voice',
            help='Voice-only interaction mode',
            description='Start Jarvis in voice-only mode for hands-free operation'
        )
        
        voice_parser.add_argument(
            '--wake-word',
            type=str,
            help='Custom wake word (default: jarvis)'
        )
        
        voice_parser.add_argument(
            '--continuous',
            action='store_true',
            help='Continuous listening mode'
        )
        
        voice_parser.add_argument(
            '--sensitivity',
            type=float,
            metavar='0.0-1.0',
            help='Wake word detection sensitivity'
        )
    
    def _add_exec_parser(self, subparsers):
        """Add the exec command parser."""
        exec_parser = subparsers.add_parser(
            'exec',
            help='Execute single command',
            description='Execute a single command and exit'
        )
        
        exec_parser.add_argument(
            'command',
            nargs='+',
            help='Command to execute'
        )
        
        exec_parser.add_argument(
            '--output-format',
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format (default: text)'
        )
        
        exec_parser.add_argument(
            '--timeout',
            type=int,
            default=180,
            help='Command timeout in seconds (default: 180)'
        )
    
    def _add_system_parser(self, subparsers):
        """Add the system command parser."""
        system_parser = subparsers.add_parser(
            'system',
            help='System management commands',
            description='Manage Jarvis system components and data'
        )
        
        system_subparsers = system_parser.add_subparsers(
            dest='system_action',
            title='System Actions'
        )
        
        # Install dependencies
        install_parser = system_subparsers.add_parser('install', help='Install dependencies')
        install_parser.add_argument(
            '--optional',
            action='store_true',
            help='Install optional dependencies'
        )
        
        # Update system
        system_subparsers.add_parser('update', help='Update Jarvis system')
        
        # Clean data
        clean_parser = system_subparsers.add_parser('clean', help='Clean system data')
        clean_parser.add_argument(
            '--memory',
            action='store_true',
            help='Clean memory database'
        )
        clean_parser.add_argument(
            '--logs',
            action='store_true',
            help='Clean log files'
        )
        clean_parser.add_argument(
            '--all',
            action='store_true',
            help='Clean all data'
        )
        
        # Backup/restore
        backup_parser = system_subparsers.add_parser('backup', help='Backup system data')
        backup_parser.add_argument('path', help='Backup file path')
        
        restore_parser = system_subparsers.add_parser('restore', help='Restore system data')
        restore_parser.add_argument('path', help='Backup file path')
    
    def _get_usage_examples(self) -> str:
        """Get usage examples for the help text."""
        return """
Examples:
  # Start interactive CLI
  python3 jarvis_cli.py run --mode cli
  
  # Start voice-only mode
  python3 jarvis_cli.py voice --continuous
  
  # Execute single command
  python3 jarvis_cli.py exec "What's the weather like today?"
  
  # Show system status
  python3 jarvis_cli.py status --health --metrics
  
  # Configure AI provider
  python3 jarvis_cli.py config set ai.primary_provider openai
  python3 jarvis_cli.py config set ai.openai.api_key "your-key-here"
  
  # Start interactive shell with voice
  python3 jarvis_cli.py shell --voice --history
  
  # Run in daemon mode
  python3 jarvis_cli.py run --mode daemon --background --pid-file /var/run/jarvis.pid
  
  # Show configuration
  python3 jarvis_cli.py config show --section ai --json
  
  # System maintenance
  python3 jarvis_cli.py system clean --logs
  python3 jarvis_cli.py system backup /backup/jarvis-$(date +%Y%m%d).tar.gz
  
  # Monitor status continuously
  python3 jarvis_cli.py status --watch 5
        """
    
    def setup_logging(self, args) -> logging.Logger:
        """
        Setup logging based on command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Configured logger instance
        """
        # Determine log level
        if args.quiet:
            log_level = logging.ERROR
        elif args.debug:
            log_level = logging.DEBUG
        elif args.verbose >= 3:
            log_level = logging.DEBUG
        elif args.verbose >= 2:
            log_level = logging.INFO
        elif args.verbose >= 1:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Setup logger
        logger = setup_logger(log_level)
        
        # Configure log file if specified
        if hasattr(args, 'log_file') and args.log_file:
            file_handler = logging.FileHandler(args.log_file)
            file_handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _import_jarvis_app(self):
        """Import JarvisApplication and related classes."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("jarvis_app", "jarvis.py")
        jarvis_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jarvis_module)
        return jarvis_module.JarvisApplication, jarvis_module.OperationMode
    
    def load_config(self, args) -> Config:
        """
        Load configuration based on command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Configuration instance
        """
        try:
            config = Config(args.config if hasattr(args, 'config') else None)
            self.logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    async def handle_run_command(self, args) -> int:
        """Handle the run command."""
        try:
            JarvisApplication, OperationMode = self._import_jarvis_app()
            
            # Map mode string to enum
            mode_map = {
                'cli': OperationMode.CLI,
                'voice': OperationMode.VOICE,
                'daemon': OperationMode.DAEMON,
                'interactive': OperationMode.INTERACTIVE
            }
            
            operation_mode = mode_map[args.mode]
            
            # Create and run Jarvis application
            with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
                self.jarvis_app = jarvis
                
                if args.background and args.mode == 'daemon':
                    return self._run_daemon_background(jarvis, args)
                else:
                    return jarvis.run(operation_mode)
                    
        except Exception as e:
            self.logger.error(f"Failed to run Jarvis: {e}")
            if args.debug:
                raise
            return 1
    
    def _run_daemon_background(self, jarvis, args) -> int:
        """Run Jarvis as a background daemon."""
        try:
            import daemon
            import daemon.pidfile
            
            pid_file_path = args.pid_file or '/tmp/jarvis.pid'
            
            with daemon.DaemonContext(pidfile=daemon.pidfile.PIDLockFile(pid_file_path)):
                return jarvis.run(OperationMode.DAEMON)
                
        except ImportError:
            self.logger.error("python-daemon package required for background mode")
            self.logger.info("Install with: pip install python-daemon")
            return 1
        except Exception as e:
            self.logger.error(f"Failed to start daemon: {e}")
            return 1
    
    def handle_config_command(self, args) -> int:
        """Handle configuration management commands."""
        try:
            if args.config_action == 'show':
                return self._handle_config_show(args)
            elif args.config_action == 'set':
                return self._handle_config_set(args)
            elif args.config_action == 'get':
                return self._handle_config_get(args)
            elif args.config_action == 'reset':
                return self._handle_config_reset(args)
            elif args.config_action == 'validate':
                return self._handle_config_validate(args)
            else:
                print("No configuration action specified. Use --help for options.")
                return 1
                
        except Exception as e:
            self.logger.error(f"Configuration command failed: {e}")
            return 1
    
    def _handle_config_show(self, args) -> int:
        """Handle config show command."""
        try:
            if args.section:
                # Show specific section
                value = self.config.get(args.section)
                if value is None:
                    print(f"Configuration section '{args.section}' not found")
                    return 1
                
                if args.json:
                    print(json.dumps(value, indent=2))
                else:
                    self._print_config_section(args.section, value)
            else:
                # Show all configuration
                if args.json:
                    print(str(self.config))  # Config.__str__ returns sanitized JSON
                else:
                    self._print_full_config()
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to show configuration: {e}")
            return 1
    
    def _handle_config_set(self, args) -> int:
        """Handle config set command."""
        try:
            # Convert value to appropriate type
            value = args.value
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string
            
            self.config.set(args.key, value)
            
            # Save configuration
            config_path = getattr(args, 'config', None) or 'config/jarvis.json'
            self.config.save(config_path)
            
            print(f"Configuration updated: {args.key} = {value}")
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration: {e}")
            return 1
    
    def _handle_config_get(self, args) -> int:
        """Handle config get command."""
        try:
            value = self.config.get(args.key)
            if value is None:
                print(f"Configuration key '{args.key}' not found")
                return 1
            
            print(f"{args.key} = {value}")
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to get configuration: {e}")
            return 1
    
    def _handle_config_reset(self, args) -> int:
        """Handle config reset command."""
        if not args.confirm:
            print("This will reset all configuration to defaults.")
            response = input("Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("Reset cancelled")
                return 0
        
        try:
            # Create new config with defaults
            self.config = Config()
            
            # Save to file
            config_path = getattr(args, 'config', None) or 'config/jarvis.json'
            self.config.save(config_path)
            
            print("Configuration reset to defaults")
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return 1
    
    def _handle_config_validate(self, args) -> int:
        """Handle config validate command."""
        try:
            is_valid = self.config.validate()
            
            if is_valid:
                print("✅ Configuration is valid")
                return 0
            else:
                print("❌ Configuration has errors (check logs for details)")
                return 1
                
        except Exception as e:
            self.logger.error(f"Failed to validate configuration: {e}")
            return 1
    
    def handle_status_command(self, args) -> int:
        """Handle status and diagnostics commands."""
        try:
            JarvisApplication, _ = self._import_jarvis_app()
            
            # Create temporary Jarvis instance for status checking
            with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
                if args.watch:
                    return self._watch_status(jarvis, args)
                else:
                    return self._show_status_once(jarvis, args)
                    
        except Exception as e:
            self.logger.error(f"Status command failed: {e}")
            return 1
    
    def _show_status_once(self, jarvis, args) -> int:
        """Show status information once."""
        status_data = {}
        
        try:
            # Basic system status
            if not any([args.health, args.metrics, args.memory, args.ai]):
                # Show all by default
                status_data.update(self._get_basic_status(jarvis))
                status_data.update(self._get_health_status(jarvis))
                status_data.update(self._get_metrics_status(jarvis))
            else:
                # Show specific sections
                if args.health:
                    status_data.update(self._get_health_status(jarvis))
                if args.metrics:
                    status_data.update(self._get_metrics_status(jarvis))
                if args.memory:
                    status_data.update(self._get_memory_status(jarvis))
                if args.ai:
                    status_data.update(self._get_ai_status(jarvis))
            
            # Output results
            if args.json:
                print(json.dumps(status_data, indent=2, default=str))
            else:
                self._print_status(status_data)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            return 1
    
    def _watch_status(self, jarvis, args) -> int:
        """Continuously watch and display status."""
        import time
        
        try:
            while True:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Show status
                print(f"🤖 Jarvis Status Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                
                self._show_status_once(jarvis, args)
                
                print(f"\nRefreshing every {args.watch} seconds... (Press Ctrl+C to exit)")
                time.sleep(args.watch)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            return 0
    
    async def handle_exec_command(self, args) -> int:
        """Handle single command execution."""
        try:
            JarvisApplication, _ = self._import_jarvis_app()
            
            # Join command parts
            command = ' '.join(args.command)
            
            # Create Jarvis application
            with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
                # Set the application to running state for exec mode
                jarvis.is_running = True
                
                # Process command with timeout
                try:
                    response = await asyncio.wait_for(
                        jarvis.process_command(command),
                        timeout=args.timeout
                    )
                    
                    # Format output
                    if args.output_format == 'json':
                        result = {
                            'command': command,
                            'response': response,
                            'timestamp': datetime.now().isoformat()
                        }
                        print(json.dumps(result, indent=2))
                    elif args.output_format == 'yaml':
                        try:
                            import yaml
                            result = {
                                'command': command,
                                'response': response,
                                'timestamp': datetime.now().isoformat()
                            }
                            print(yaml.dump(result, default_flow_style=False))
                        except ImportError:
                            print("PyYAML package required for YAML output")
                            print("Install with: pip install PyYAML")
                            return 1
                    else:
                        print(response)
                    
                    return 0
                    
                except asyncio.TimeoutError:
                    print(f"Command timed out after {args.timeout} seconds")
                    return 1
                    
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return 1
    
    def handle_shell_command(self, args) -> int:
        """Handle interactive shell command."""
        try:
            JarvisApplication, OperationMode = self._import_jarvis_app()
            
            # Create Jarvis application
            with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
                if args.voice:
                    # Interactive mode with voice
                    return jarvis.run(OperationMode.INTERACTIVE)
                else:
                    # CLI mode
                    return jarvis.run(OperationMode.CLI)
                    
        except Exception as e:
            self.logger.error(f"Shell command failed: {e}")
            return 1
    
    def handle_voice_command(self, args) -> int:
        """Handle voice-only mode command."""
        try:
            JarvisApplication, OperationMode = self._import_jarvis_app()
            
            # Create Jarvis application
            with JarvisApplication(config_path=args.config, debug=args.debug) as jarvis:
                # Configure voice settings if specified
                if args.wake_word:
                    jarvis.config.set('voice.wake_word', args.wake_word)
                if args.sensitivity is not None:
                    jarvis.config.set('voice.sensitivity', args.sensitivity)
                
                return jarvis.run(OperationMode.VOICE)
                
        except Exception as e:
            self.logger.error(f"Voice command failed: {e}")
            return 1
    
    def handle_system_command(self, args) -> int:
        """Handle system management commands."""
        try:
            if args.system_action == 'install':
                return self._handle_system_install(args)
            elif args.system_action == 'update':
                return self._handle_system_update(args)
            elif args.system_action == 'clean':
                return self._handle_system_clean(args)
            elif args.system_action == 'backup':
                return self._handle_system_backup(args)
            elif args.system_action == 'restore':
                return self._handle_system_restore(args)
            else:
                print("No system action specified. Use --help for options.")
                return 1
                
        except Exception as e:
            self.logger.error(f"System command failed: {e}")
            return 1
    
    def _handle_system_install(self, args) -> int:
        """Handle dependency installation."""
        try:
            requirements_file = 'requirements.txt'
            if args.optional:
                # Install optional dependencies
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file, '--upgrade']
                # Add optional packages
                optional_packages = [
                    'pyaudio', 'openai-whisper', 'pvporcupine', 'gTTS', 'librosa', 
                    'soundfile', 'python-daemon', 'PyYAML'
                ]
                cmd.extend(optional_packages)
            else:
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file]
            
            print("Installing dependencies...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return 0
            else:
                print("❌ Installation failed:")
                print(result.stderr)
                return 1
                
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return 1
    
    def _get_basic_status(self, jarvis) -> Dict[str, Any]:
        """Get basic system status."""
        return {
            'basic_status': {
                'running': jarvis.is_running,
                'state': jarvis.state.value,
                'mode': jarvis.mode.value,
                'uptime': str(datetime.now() - jarvis.start_time),
                'version': VERSION
            }
        }
    
    def _get_health_status(self, jarvis) -> Dict[str, Any]:
        """Get health status."""
        health = jarvis.get_health_status()
        return {
            'health': {
                'overall_healthy': health.overall_healthy,
                'components': health.components,
                'last_check': health.last_check.isoformat(),
                'errors': health.errors,
                'warnings': health.warnings
            }
        }
    
    def _get_metrics_status(self, jarvis) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = jarvis.get_system_metrics()
        return {
            'metrics': {
                'uptime': str(metrics.uptime),
                'total_interactions': metrics.total_interactions,
                'successful_interactions': metrics.successful_interactions,
                'success_rate': f"{metrics.successful_interactions / max(metrics.total_interactions, 1) * 100:.1f}%",
                'avg_response_time': f"{metrics.avg_response_time:.2f}s",
                'memory_usage_mb': f"{metrics.memory_usage_mb:.1f} MB",
                'cpu_usage_percent': f"{metrics.cpu_usage_percent:.1f}%"
            }
        }
    
    def _get_memory_status(self, jarvis) -> Dict[str, Any]:
        """Get memory system status."""
        if jarvis.memory_system:
            stats = jarvis.memory_system.get_memory_statistics()
            return {'memory': stats}
        return {'memory': {'status': 'not_available'}}
    
    def _get_ai_status(self, jarvis) -> Dict[str, Any]:
        """Get AI provider status."""
        if jarvis.ai_brain:
            status = jarvis.ai_brain.get_provider_status()
            return {'ai_providers': status}
        return {'ai_providers': {'status': 'not_available'}}
    
    def _print_status(self, status_data: Dict[str, Any]):
        """Print status information in a formatted way."""
        for section, data in status_data.items():
            print(f"\n📊 {section.replace('_', ' ').title()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for subkey, subvalue in value.items():
                            print(f"    {subkey}: {subvalue}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  {data}")
    
    def _print_config_section(self, section: str, data: Any):
        """Print a configuration section."""
        print(f"📋 Configuration - {section}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")
    
    def _print_full_config(self):
        """Print full configuration."""
        print("📋 Full Configuration:")
        sections = ['ai', 'voice', 'memory', 'system_tools', 'learning', 'logging', 'security']
        
        for section in sections:
            data = self.config.get(section)
            if data:
                print(f"\n  {section}:")
                for key, value in data.items():
                    # Hide sensitive data
                    if 'key' in key.lower() or 'password' in key.lower():
                        value = "***" if value else None
                    print(f"    {key}: {value}")
    
    async def run(self, argv: Optional[List[str]] = None) -> int:
        """
        Main CLI entry point.
        
        Args:
            argv: Command line arguments (defaults to sys.argv)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self.create_parser()
        
        # Parse arguments
        if argv is None:
            argv = sys.argv[1:]
        
        # Handle case where no command is provided - default to run
        subparser_choices = None
        for action in parser._subparsers._actions:
            if hasattr(action, 'choices'):
                subparser_choices = action.choices
                break
        
        # Only default to 'run' if no arguments at all, or if first arg doesn't look like a command/option
        if not argv:
            argv = ['run']
        elif subparser_choices and argv[0] not in subparser_choices and not argv[0].startswith('-'):
            # This looks like a direct command to execute, so use 'exec'
            argv = ['exec'] + argv
        
        try:
            args = parser.parse_args(argv)
        except SystemExit as e:
            # Handle help and version, which call sys.exit()
            raise
        except Exception as e:
            print(f"Argument parsing error: {e}")
            print(f"Raw argv: {argv}")
            return 1
        
        # Setup logging
        self.logger = self.setup_logging(args)
        
        # Load configuration
        self.config = self.load_config(args)
        
        try:
            # Debug: print the parsed command
            self.logger.debug(f"Parsed subcommand: {args.subcommand}")
            self.logger.debug(f"All args: {args}")
            
            # Handle commands
            if args.subcommand == 'run':
                return await self.handle_run_command(args)
            elif args.subcommand == 'config':
                return self.handle_config_command(args)
            elif args.subcommand == 'status':
                return self.handle_status_command(args)
            elif args.subcommand == 'shell':
                return self.handle_shell_command(args)
            elif args.subcommand == 'voice':
                return self.handle_voice_command(args)
            elif args.subcommand == 'exec':
                return await self.handle_exec_command(args)
            elif args.subcommand == 'system':
                return self.handle_system_command(args)
            else:
                print(f"Unknown subcommand: {args.subcommand}")
                print(f"Available commands: run, config, status, shell, voice, exec, system")
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 0
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if args.debug:
                raise
            return 1


def main():
    """Main entry point for the CLI."""
    cli = JarvisCLI()
    
    # Run with asyncio support
    exit_code = asyncio.run(cli.run())
    sys.exit(exit_code)


if __name__ == '__main__':
    main()