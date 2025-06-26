"""
Voice Processing Module
Handles speech-to-text, text-to-speech, and audio processing.
"""

from .processor import VoiceProcessor
from .voice_interface import (
    VoiceInterface,
    create_voice_interface,
    VoiceResult,
    AudioConfig,
    VoiceConfig,
    STTConfig,
    TTSConfig,
    WakeWordConfig,
    AudioFormat,
    STTEngine,
    TTSEngine,
    VoiceGender,
    ProcessingState
)

__all__ = [
    "VoiceProcessor",
    "VoiceInterface", 
    "create_voice_interface",
    "VoiceResult",
    "AudioConfig",
    "VoiceConfig", 
    "STTConfig",
    "TTSConfig",
    "WakeWordConfig",
    "AudioFormat",
    "STTEngine",
    "TTSEngine",
    "VoiceGender",
    "ProcessingState"
]