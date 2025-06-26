"""
Jarvis AI Assistant Package

A sophisticated AI assistant with voice interaction, system integration,
and natural language processing capabilities.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Core components
from .core import JarvisAssistant
from .config import Config

# Main interfaces
from .interfaces import CLIInterface

# AI and NLP
from .ai_integration import AIBrain, AIProvider, IntentType, ResponseTone
from .nlp import CommandParser, CommandIntent, ParameterType

# System Tools
from .system_tools import SystemTools, SystemOperation, OperationResult

# Voice Processing
from .voice import VoiceInterface, VoiceProcessor, create_voice_interface

__all__ = [
    # Core
    "JarvisAssistant", "Config",
    # Interfaces  
    "CLIInterface",
    # AI & NLP
    "AIBrain", "AIProvider", "IntentType", "ResponseTone",
    "CommandParser", "CommandIntent", "ParameterType",
    # System Tools
    "SystemTools", "SystemOperation", "OperationResult",
    # Voice Processing
    "VoiceInterface", "VoiceProcessor", "create_voice_interface"
]