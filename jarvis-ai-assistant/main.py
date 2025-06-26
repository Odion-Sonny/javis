#!/usr/bin/env python3
"""
Jarvis AI Assistant - Main Entry Point
A voice-controlled AI assistant with system integration capabilities.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jarvis.core import JarvisAssistant
from jarvis.cli import CLIInterface
from jarvis.config import Config
from jarvis.utils.logger import setup_logger


def main():
    """Main entry point for Jarvis AI Assistant."""
    parser = argparse.ArgumentParser(
        description="Jarvis AI Assistant - Your intelligent voice companion"
    )
    parser.add_argument(
        "--mode", 
        choices=["cli", "voice", "daemon"], 
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
        version="Jarvis AI Assistant v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Initialize Jarvis
        jarvis = JarvisAssistant(config)
        
        # Start appropriate interface
        if args.mode == "cli":
            cli = CLIInterface(jarvis)
            cli.run()
        elif args.mode == "voice":
            jarvis.start_voice_mode()
        elif args.mode == "daemon":
            jarvis.start_daemon_mode()
            
    except KeyboardInterrupt:
        logger.info("Shutting down Jarvis...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()