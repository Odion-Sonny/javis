"""
Voice Processing Implementation
Handles audio input/output, speech recognition, and text-to-speech.
"""

import logging
import threading
import queue
from typing import Optional, Dict, Any
import time
import io
import wave
import struct

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class VoiceProcessor:
    """Handles voice input and output processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize voice processor with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Voice recognition settings
        self.wake_word = config.get("wake_word", "jarvis")
        self.language = config.get("language", "en-US")
        self.voice_engine = config.get("engine", "default")
        
        # Audio settings
        self.chunk_size = config.get("chunk_size", 1024)
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.audio_format = pyaudio.paInt16 if HAS_PYAUDIO else None
        
        # Initialize components
        self.audio_interface = None
        self.recognizer = None
        self.tts_engine = None
        
        self._initialize_audio_components()
        
        self.logger.info("Voice processor initialized")
    
    def listen(self, timeout: float = 5.0) -> Optional[bytes]:
        """
        Listen for audio input.
        
        Args:
            timeout: Maximum time to wait for audio input
            
        Returns:
            Raw audio data or None if no input detected
        """
        try:
            if not HAS_PYAUDIO or not self.audio_interface:
                self.logger.warning("PyAudio not available, using fallback")
                return self._fallback_listen(timeout)
            
            self.logger.info(f"Listening for voice input (timeout: {timeout}s)...")
            
            stream = self.audio_interface.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Simple voice activity detection
                    if self._detect_voice_activity(data):
                        # Continue recording for a bit more
                        for _ in range(10):  # ~0.6 seconds more
                            data = stream.read(self.chunk_size, exception_on_overflow=False)
                            frames.append(data)
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Audio read error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
            if frames:
                # Convert frames to bytes
                audio_data = b''.join(frames)
                return audio_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error during audio capture: {e}")
            return None
    
    def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """
        Convert speech audio to text.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Transcribed text or None if recognition failed
        """
        try:
            if not HAS_SPEECH_RECOGNITION or not self.recognizer:
                self.logger.warning("Speech recognition not available, using fallback")
                return self._fallback_speech_to_text(audio_data)
            
            self.logger.info("Converting speech to text...")
            
            if not audio_data:
                return None
            
            # Convert raw audio to AudioData format
            audio_io = io.BytesIO()
            
            # Create a WAV file in memory
            with wave.open(audio_io, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit audio
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            audio_io.seek(0)
            
            # Convert to AudioData
            with sr.AudioFile(audio_io) as source:
                audio = self.recognizer.record(source)
            
            # Try multiple recognition engines
            for engine in ['google', 'sphinx']:
                try:
                    if engine == 'google':
                        text = self.recognizer.recognize_google(audio, language=self.language)
                    elif engine == 'sphinx':
                        text = self.recognizer.recognize_sphinx(audio)
                    
                    if text:
                        self.logger.info(f"Recognized text: '{text}'")
                        return text
                        
                except Exception as e:
                    self.logger.debug(f"Recognition with {engine} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error during speech recognition: {e}")
            return None
    
    def text_to_speech(self, text: str, voice: Optional[str] = None) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            voice: Optional voice to use (if None, uses default)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not HAS_PYTTSX3 or not self.tts_engine:
                self.logger.warning("TTS engine not available, using fallback")
                return self._fallback_text_to_speech(text)
            
            self.logger.info(f"Converting text to speech: '{text[:50]}...'")
            
            # Configure voice if specified
            if voice:
                voices = self.tts_engine.getProperty('voices')
                for v in voices:
                    if voice.lower() in v.name.lower():
                        self.tts_engine.setProperty('voice', v.id)
                        break
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', self.config.get('speech_rate', 150))
            self.tts_engine.setProperty('volume', self.config.get('speech_volume', 0.8))
            
            # Speak the text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during text-to-speech: {e}")
            return self._fallback_text_to_speech(text)
    
    def detect_wake_word(self, text: str) -> bool:
        """
        Detect if the wake word is present in the text.
        
        Args:
            text: Text to check for wake word
            
        Returns:
            True if wake word detected, False otherwise
        """
        return self.wake_word.lower() in text.lower()
    
    def start_continuous_listening(self):
        """Start continuous listening in a separate thread."""
        if self.is_listening:
            return
        
        self.is_listening = True
        listening_thread = threading.Thread(target=self._continuous_listen_loop)
        listening_thread.daemon = True
        listening_thread.start()
        
        self.logger.info("Started continuous listening")
    
    def stop_continuous_listening(self):
        """Stop continuous listening."""
        self.is_listening = False
        self.logger.info("Stopped continuous listening")
    
    def _continuous_listen_loop(self):
        """Continuous listening loop (runs in separate thread)."""
        while self.is_listening:
            try:
                audio_data = self.listen(timeout=1.0)
                if audio_data:
                    self.audio_queue.put(audio_data)
                time.sleep(0.1)  # Brief pause to prevent excessive CPU usage
            except Exception as e:
                self.logger.error(f"Error in continuous listening: {e}")
                time.sleep(1)  # Wait before retrying
    
    def _initialize_audio_components(self):
        """Initialize audio components if available."""
        # Initialize PyAudio
        if HAS_PYAUDIO:
            try:
                self.audio_interface = pyaudio.PyAudio()
                self.logger.info("PyAudio initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize PyAudio: {e}")
                self.audio_interface = None
        
        # Initialize speech recognition
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                # Adjust for ambient noise
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.logger.info("Speech recognition initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize speech recognition: {e}")
                self.recognizer = None
        
        # Initialize TTS engine
        if HAS_PYTTSX3:
            try:
                self.tts_engine = pyttsx3.init()
                self.logger.info("TTS engine initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize TTS engine: {e}")
                self.tts_engine = None
    
    def _detect_voice_activity(self, audio_data: bytes) -> bool:
        """Simple voice activity detection based on audio energy."""
        try:
            # Convert bytes to numpy-like array
            audio_values = struct.unpack(f'{len(audio_data)//2}h', audio_data)
            
            # Calculate RMS energy
            rms = sum(x**2 for x in audio_values) / len(audio_values)
            rms = rms ** 0.5
            
            # Voice activity threshold
            threshold = self.config.get('voice_threshold', 500)
            return rms > threshold
            
        except Exception:
            return False
    
    def _fallback_listen(self, timeout: float) -> Optional[bytes]:
        """Fallback listening implementation when PyAudio is not available."""
        self.logger.info(f"Fallback listening for {timeout}s (no audio capture)")
        time.sleep(min(timeout, 2.0))
        return b'\x00' * 1024  # Return dummy audio data
    
    def _fallback_speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Fallback speech-to-text when recognition is not available."""
        if audio_data:
            self.logger.info("Fallback: simulating speech recognition")
            return "Hello Jarvis, how can you help me today?"
        return None
    
    def _fallback_text_to_speech(self, text: str) -> bool:
        """Fallback text-to-speech when TTS engine is not available."""
        print(f"🔊 Jarvis: {text}")
        return True
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name, 'language': getattr(v, 'languages', ['unknown'])} for v in voices]
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
            return []
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.is_listening:
            self.stop_continuous_listening()
        
        if self.audio_interface:
            try:
                self.audio_interface.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating audio interface: {e}")
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception as e:
                self.logger.error(f"Error stopping TTS engine: {e}")
        
        self.logger.info("Voice processor cleanup completed")