"""
Voice Interface Module for Jarvis AI Assistant

Provides comprehensive voice interaction capabilities including:
- Speech-to-text using OpenAI Whisper (local) or speech_recognition
- Text-to-speech using pyttsx3 with voice customization
- Wake word detection for hands-free operation
- Audio recording and playback controls
- Voice command processing pipeline

Supports multiple languages, voice customization, and audio settings.
"""

import logging
import threading
import queue
import time
import io
import wave
import audioop
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import tempfile

# Optional dependencies with fallbacks
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"


class STTEngine(Enum):
    """Speech-to-text engine options."""
    WHISPER_LOCAL = "whisper_local"
    SPEECH_RECOGNITION = "speech_recognition"
    GOOGLE = "google"
    AZURE = "azure"


class TTSEngine(Enum):
    """Text-to-speech engine options."""
    PYTTSX3 = "pyttsx3"
    SYSTEM = "system"


class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class ProcessingState(Enum):
    """Voice processing states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    WAKE_WORD_DETECTION = "wake_word_detection"


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format: int = 16  # 16-bit
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None
    noise_threshold: float = 0.5
    pause_threshold: float = 0.8
    timeout: float = 5.0
    phrase_timeout: float = 0.3


@dataclass
class VoiceConfig:
    """Voice configuration settings."""
    voice_id: Optional[str] = None
    gender: VoiceGender = VoiceGender.FEMALE
    rate: int = 200  # Words per minute
    volume: float = 0.9  # 0.0 to 1.0
    pitch: int = 0  # -50 to 50
    language: str = "en-US"


@dataclass
class STTConfig:
    """Speech-to-text configuration."""
    engine: STTEngine = STTEngine.WHISPER_LOCAL
    model_size: str = "base"  # For Whisper: tiny, base, small, medium, large
    language: Optional[str] = None  # Auto-detect if None
    energy_threshold: int = 300
    dynamic_energy_threshold: bool = True
    pause_threshold: float = 0.8
    timeout: float = 5.0


@dataclass
class TTSConfig:
    """Text-to-speech configuration."""
    engine: TTSEngine = TTSEngine.PYTTSX3
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    save_audio: bool = False
    audio_format: AudioFormat = AudioFormat.WAV


@dataclass
class WakeWordConfig:
    """Wake word detection configuration."""
    enabled: bool = True
    wake_words: List[str] = field(default_factory=lambda: ["jarvis"])
    sensitivity: float = 0.5  # 0.0 to 1.0
    model_path: Optional[str] = None
    access_key: Optional[str] = None  # For Porcupine


@dataclass
class VoiceResult:
    """Result of voice processing operation."""
    success: bool
    text: Optional[str] = None
    confidence: float = 0.0
    language: Optional[str] = None
    processing_time: float = 0.0
    audio_file: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VoiceInterface:
    """
    Comprehensive voice interface for Jarvis AI Assistant.
    
    Provides speech-to-text, text-to-speech, wake word detection,
    and audio recording/playback capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize voice interface with configuration.
        
        Args:
            config: Configuration dictionary with voice settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize configurations
        self.audio_config = AudioConfig(**self.config.get('audio', {}))
        self.stt_config = STTConfig(**self.config.get('stt', {}))
        self.tts_config = TTSConfig(**self.config.get('tts', {}))
        self.wake_word_config = WakeWordConfig(**self.config.get('wake_word', {}))
        
        # State management
        self.state = ProcessingState.IDLE
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Audio components
        self.audio = None
        self.microphone = None
        self.recognizer = None
        self.tts_engine = None
        self.whisper_model = None
        self.wake_word_detector = None
        
        # Threading
        self.wake_word_thread = None
        self.audio_thread = None
        self.processing_thread = None
        
        # Callbacks
        self.on_wake_word_detected: Optional[Callable] = None
        self.on_speech_recognized: Optional[Callable[[str], None]] = None
        self.on_command_processed: Optional[Callable[[str], str]] = None
        self.on_state_changed: Optional[Callable[[ProcessingState], None]] = None
        
        # Initialize components
        self._initialize_audio()
        self._initialize_stt()
        self._initialize_tts()
        self._initialize_wake_word_detection()
        
        self.logger.info("Voice interface initialized successfully")
    
    def _initialize_audio(self):
        """Initialize audio components."""
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available - audio functionality limited")
            return
        
        try:
            self.audio = pyaudio.PyAudio()
            
            # Initialize microphone for speech recognition
            if SPEECH_RECOGNITION_AVAILABLE:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = self.stt_config.energy_threshold
                self.recognizer.dynamic_energy_threshold = self.stt_config.dynamic_energy_threshold
                self.recognizer.pause_threshold = self.stt_config.pause_threshold
                
                # Find microphone
                if self.audio_config.input_device_index is not None:
                    self.microphone = sr.Microphone(device_index=self.audio_config.input_device_index)
                else:
                    self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
            self.logger.info("Audio components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
    
    def _initialize_stt(self):
        """Initialize speech-to-text engine."""
        if self.stt_config.engine == STTEngine.WHISPER_LOCAL and WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model(self.stt_config.model_size)
                self.logger.info(f"Whisper model '{self.stt_config.model_size}' loaded")
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                # Fallback to speech_recognition
                self.stt_config.engine = STTEngine.SPEECH_RECOGNITION
        
        if self.stt_config.engine == STTEngine.SPEECH_RECOGNITION:
            if not SPEECH_RECOGNITION_AVAILABLE:
                self.logger.error("speech_recognition not available")
            else:
                self.logger.info("Using speech_recognition for STT")
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine."""
        if self.tts_config.engine == TTSEngine.PYTTSX3 and PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Configure voice settings
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Find voice matching preferences
                    selected_voice = self._select_voice(voices)
                    if selected_voice:
                        self.tts_engine.setProperty('voice', selected_voice.id)
                
                # Set speech rate and volume
                self.tts_engine.setProperty('rate', self.tts_config.voice_config.rate)
                self.tts_engine.setProperty('volume', self.tts_config.voice_config.volume)
                
                self.logger.info("TTS engine initialized")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS engine: {e}")
        else:
            self.logger.warning("pyttsx3 not available - TTS functionality limited")
    
    def _initialize_wake_word_detection(self):
        """Initialize wake word detection."""
        if not self.wake_word_config.enabled:
            self.logger.info("Wake word detection disabled")
            return
        
        if PORCUPINE_AVAILABLE and self.wake_word_config.access_key:
            try:
                # Initialize Porcupine for wake word detection
                keywords = self.wake_word_config.wake_words
                sensitivities = [self.wake_word_config.sensitivity] * len(keywords)
                
                self.wake_word_detector = pvporcupine.create(
                    access_key=self.wake_word_config.access_key,
                    keywords=keywords,
                    sensitivities=sensitivities
                )
                
                self.logger.info(f"Porcupine wake word detection initialized for: {keywords}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Porcupine: {e}")
                self._fallback_wake_word_detection()
        else:
            self._fallback_wake_word_detection()
    
    def _fallback_wake_word_detection(self):
        """Fallback wake word detection using simple keyword matching."""
        self.logger.info("Using fallback wake word detection")
        # Will be implemented in the listening loop
    
    def _select_voice(self, voices) -> Optional[Any]:
        """Select the best voice based on configuration."""
        voice_config = self.tts_config.voice_config
        
        # If specific voice ID is provided
        if voice_config.voice_id:
            for voice in voices:
                if voice.id == voice_config.voice_id:
                    return voice
        
        # Filter by language
        language_voices = []
        for voice in voices:
            if hasattr(voice, 'languages') and voice_config.language in str(voice.languages):
                language_voices.append(voice)
            elif voice_config.language.split('-')[0] in str(voice.name).lower():
                language_voices.append(voice)
        
        if not language_voices:
            language_voices = voices
        
        # Filter by gender preference
        gender_voices = []
        gender_keywords = {
            VoiceGender.MALE: ['male', 'man', 'david', 'alex'],
            VoiceGender.FEMALE: ['female', 'woman', 'zira', 'samantha'],
            VoiceGender.NEUTRAL: []
        }
        
        keywords = gender_keywords.get(voice_config.gender, [])
        if keywords:
            for voice in language_voices:
                voice_name = str(voice.name).lower()
                if any(keyword in voice_name for keyword in keywords):
                    gender_voices.append(voice)
        
        # Return best match or first available
        if gender_voices:
            return gender_voices[0]
        elif language_voices:
            return language_voices[0]
        else:
            return voices[0] if voices else None
    
    def start_listening(self):
        """Start the voice interface for continuous listening."""
        if self.is_running:
            self.logger.warning("Voice interface already running")
            return
        
        self.is_running = True
        self._set_state(ProcessingState.WAKE_WORD_DETECTION)
        
        # Start background threads
        if self.wake_word_config.enabled:
            self.wake_word_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
            self.wake_word_thread.start()
        
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        self.logger.info("Voice interface started")
    
    def stop_listening(self):
        """Stop the voice interface."""
        self.is_running = False
        self._set_state(ProcessingState.IDLE)
        
        # Wait for threads to complete
        if self.wake_word_thread and self.wake_word_thread.is_alive():
            self.wake_word_thread.join(timeout=2)
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
        
        self.logger.info("Voice interface stopped")
    
    def _wake_word_loop(self):
        """Main wake word detection loop."""
        while self.is_running:
            try:
                if self.wake_word_detector:
                    # Porcupine-based detection
                    self._porcupine_detection()
                else:
                    # Fallback detection
                    self._fallback_detection()
                    
            except Exception as e:
                self.logger.error(f"Error in wake word detection: {e}")
                time.sleep(1)
    
    def _porcupine_detection(self):
        """Porcupine-based wake word detection."""
        if not self.audio or not self.wake_word_detector:
            return
        
        try:
            # Record audio frame
            audio_frame = self._record_audio_frame()
            if audio_frame is None:
                return
            
            # Process with Porcupine
            keyword_index = self.wake_word_detector.process(audio_frame)
            
            if keyword_index >= 0:
                wake_word = self.wake_word_config.wake_words[keyword_index]
                self.logger.info(f"Wake word detected: {wake_word}")
                self._on_wake_word_detected(wake_word)
                
        except Exception as e:
            self.logger.error(f"Porcupine detection error: {e}")
    
    def _fallback_detection(self):
        """Fallback wake word detection using speech recognition."""
        if not self.recognizer or not self.microphone:
            time.sleep(0.1)
            return
        
        try:
            # Listen for audio
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
            
            # Recognize speech quickly (using faster recognition)
            try:
                text = self.recognizer.recognize_google(audio, language=self.stt_config.language).lower()
                
                # Check for wake words
                for wake_word in self.wake_word_config.wake_words:
                    if wake_word.lower() in text:
                        self.logger.info(f"Wake word detected: {wake_word}")
                        self._on_wake_word_detected(wake_word)
                        return
                        
            except sr.UnknownValueError:
                pass  # No speech detected
            except sr.RequestError:
                pass  # API error
                
        except sr.WaitTimeoutError:
            pass  # Timeout, continue listening
        except Exception as e:
            self.logger.error(f"Fallback detection error: {e}")
    
    def _record_audio_frame(self) -> Optional[List[int]]:
        """Record a single audio frame for wake word detection."""
        if not self.audio:
            return None
        
        try:
            frame_length = self.wake_word_detector.frame_length if self.wake_word_detector else 512
            
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=frame_length,
                input_device_index=self.audio_config.input_device_index
            )
            
            audio_frame = stream.read(frame_length, exception_on_overflow=False)
            stream.close()
            
            # Convert to int16 array
            if NUMPY_AVAILABLE:
                audio_array = np.frombuffer(audio_frame, dtype=np.int16)
                return audio_array.tolist()
            else:
                # Manual conversion for systems without numpy
                import struct
                return list(struct.unpack(f'{frame_length}h', audio_frame))
                
        except Exception as e:
            self.logger.error(f"Error recording audio frame: {e}")
            return None
    
    def _processing_loop(self):
        """Main command processing loop."""
        while self.is_running:
            try:
                # Wait for commands to process
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    self._process_voice_command(command)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                time.sleep(1)
    
    def _on_wake_word_detected(self, wake_word: str):
        """Handle wake word detection."""
        if self.on_wake_word_detected:
            self.on_wake_word_detected(wake_word)
        
        # Start listening for command
        self._listen_for_command()
    
    def _listen_for_command(self):
        """Listen for voice command after wake word."""
        self._set_state(ProcessingState.LISTENING)
        
        try:
            # Record command
            result = self.record_speech(timeout=self.stt_config.timeout)
            
            if result.success and result.text:
                self.logger.info(f"Command recognized: {result.text}")
                
                if self.on_speech_recognized:
                    self.on_speech_recognized(result.text)
                
                # Add to processing queue
                self.command_queue.put(result.text)
            else:
                self.logger.warning("No command recognized")
                
        except Exception as e:
            self.logger.error(f"Error listening for command: {e}")
        finally:
            self._set_state(ProcessingState.WAKE_WORD_DETECTION)
    
    def _process_voice_command(self, command: str):
        """Process a voice command."""
        self._set_state(ProcessingState.PROCESSING)
        
        try:
            if self.on_command_processed:
                response = self.on_command_processed(command)
                if response:
                    self.speak(response)
            else:
                self.logger.warning("No command processor configured")
                
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            self.speak("I'm sorry, I encountered an error processing your command.")
        finally:
            self._set_state(ProcessingState.WAKE_WORD_DETECTION)
    
    def record_speech(self, timeout: Optional[float] = None) -> VoiceResult:
        """
        Record and transcribe speech.
        
        Args:
            timeout: Recording timeout in seconds
            
        Returns:
            VoiceResult with transcribed text and metadata
        """
        start_time = time.time()
        timeout = timeout or self.stt_config.timeout
        
        if not self.recognizer or not self.microphone:
            return VoiceResult(
                success=False,
                error_message="Audio components not initialized"
            )
        
        try:
            # Record audio
            with self.microphone as source:
                self.logger.info("Listening...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=timeout
                )
            
            # Transcribe based on configured engine
            if self.stt_config.engine == STTEngine.WHISPER_LOCAL and self.whisper_model:
                result = self._transcribe_with_whisper(audio)
            else:
                result = self._transcribe_with_speech_recognition(audio)
            
            result.processing_time = time.time() - start_time
            return result
            
        except sr.WaitTimeoutError:
            return VoiceResult(
                success=False,
                error_message="Listening timeout",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Error recording speech: {e}")
            return VoiceResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _transcribe_with_whisper(self, audio) -> VoiceResult:
        """Transcribe audio using Whisper."""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
            # Convert audio to WAV
            with open(tmp_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                tmp_path,
                language=self.stt_config.language
            )
            
            # Clean up
            Path(tmp_path).unlink()
            
            return VoiceResult(
                success=True,
                text=result["text"].strip(),
                language=result.get("language"),
                confidence=1.0,  # Whisper doesn't provide confidence scores
                metadata={
                    "segments": result.get("segments", []),
                    "model": self.stt_config.model_size
                }
            )
            
        except Exception as e:
            self.logger.error(f"Whisper transcription error: {e}")
            return VoiceResult(
                success=False,
                error_message=f"Whisper transcription failed: {str(e)}"
            )
    
    def _transcribe_with_speech_recognition(self, audio) -> VoiceResult:
        """Transcribe audio using speech_recognition."""
        try:
            # Try Google Speech Recognition first
            text = self.recognizer.recognize_google(
                audio, 
                language=self.stt_config.language,
                show_all=False
            )
            
            return VoiceResult(
                success=True,
                text=text,
                confidence=0.8,  # Approximate confidence
                language=self.stt_config.language,
                metadata={"engine": "google"}
            )
            
        except sr.UnknownValueError:
            return VoiceResult(
                success=False,
                error_message="Could not understand audio"
            )
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return VoiceResult(
                success=False,
                error_message=f"Recognition service error: {str(e)}"
            )
    
    def speak(self, text: str, save_to_file: Optional[str] = None) -> VoiceResult:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            save_to_file: Optional file path to save audio
            
        Returns:
            VoiceResult with operation status
        """
        start_time = time.time()
        self._set_state(ProcessingState.SPEAKING)
        
        try:
            if self.tts_config.engine == TTSEngine.PYTTSX3 and self.tts_engine:
                result = self._speak_with_pyttsx3(text, save_to_file)
            else:
                result = self._speak_with_system(text)
            
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Error in speech synthesis: {e}")
            return VoiceResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
        finally:
            if self.wake_word_config.enabled:
                self._set_state(ProcessingState.WAKE_WORD_DETECTION)
            else:
                self._set_state(ProcessingState.IDLE)
    
    def _speak_with_pyttsx3(self, text: str, save_to_file: Optional[str] = None) -> VoiceResult:
        """Speak text using pyttsx3."""
        try:
            if save_to_file:
                # Save to file
                self.tts_engine.save_to_file(text, save_to_file)
                self.tts_engine.runAndWait()
                
                return VoiceResult(
                    success=True,
                    text=text,
                    audio_file=save_to_file,
                    metadata={"engine": "pyttsx3", "saved": True}
                )
            else:
                # Speak directly
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                return VoiceResult(
                    success=True,
                    text=text,
                    metadata={"engine": "pyttsx3"}
                )
                
        except Exception as e:
            raise Exception(f"pyttsx3 speech failed: {str(e)}")
    
    def _speak_with_system(self, text: str) -> VoiceResult:
        """Speak text using system TTS."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["say", text], check=True)
            elif system == "Windows":
                # Use PowerShell for Windows TTS
                ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_command], check=True)
            elif system == "Linux":
                # Try espeak or festival
                try:
                    subprocess.run(["espeak", text], check=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(["festival", "--tts"], input=text.encode(), check=True)
                    except FileNotFoundError:
                        raise Exception("No TTS engine available on Linux")
            else:
                raise Exception(f"Unsupported platform: {system}")
            
            return VoiceResult(
                success=True,
                text=text,
                metadata={"engine": "system", "platform": system}
            )
            
        except Exception as e:
            raise Exception(f"System TTS failed: {str(e)}")
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available TTS voices.
        
        Returns:
            List of voice information dictionaries
        """
        voices = []
        
        if self.tts_engine:
            try:
                engine_voices = self.tts_engine.getProperty('voices')
                for voice in engine_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'gender': self._detect_voice_gender(voice.name),
                        'languages': getattr(voice, 'languages', []),
                        'age': getattr(voice, 'age', None)
                    })
            except Exception as e:
                self.logger.error(f"Error getting voices: {e}")
        
        return voices
    
    def _detect_voice_gender(self, voice_name: str) -> str:
        """Detect voice gender from name."""
        name_lower = voice_name.lower()
        
        male_indicators = ['male', 'man', 'david', 'alex', 'mark', 'paul']
        female_indicators = ['female', 'woman', 'zira', 'samantha', 'anna', 'hazel']
        
        if any(indicator in name_lower for indicator in male_indicators):
            return VoiceGender.MALE.value
        elif any(indicator in name_lower for indicator in female_indicators):
            return VoiceGender.FEMALE.value
        else:
            return VoiceGender.NEUTRAL.value
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the TTS voice by ID.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tts_engine:
            return False
        
        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if voice.id == voice_id:
                    self.tts_engine.setProperty('voice', voice_id)
                    self.tts_config.voice_config.voice_id = voice_id
                    self.logger.info(f"Voice changed to: {voice.name}")
                    return True
            
            self.logger.warning(f"Voice ID not found: {voice_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False
    
    def adjust_speech_rate(self, rate: int) -> bool:
        """
        Adjust speech rate (words per minute).
        
        Args:
            rate: Words per minute (typically 100-300)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tts_engine:
            return False
        
        try:
            self.tts_engine.setProperty('rate', rate)
            self.tts_config.voice_config.rate = rate
            self.logger.info(f"Speech rate set to: {rate} WPM")
            return True
        except Exception as e:
            self.logger.error(f"Error setting speech rate: {e}")
            return False
    
    def adjust_volume(self, volume: float) -> bool:
        """
        Adjust speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tts_engine:
            return False
        
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp to valid range
            self.tts_engine.setProperty('volume', volume)
            self.tts_config.voice_config.volume = volume
            self.logger.info(f"Volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False
    
    def get_audio_devices(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available audio input/output devices.
        
        Returns:
            Dictionary with 'input' and 'output' device lists
        """
        devices = {'input': [], 'output': []}
        
        if not self.audio:
            return devices
        
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                device_data = {
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'] or device_info['maxOutputChannels'],
                    'sample_rate': device_info['defaultSampleRate']
                }
                
                if device_info['maxInputChannels'] > 0:
                    devices['input'].append(device_data)
                if device_info['maxOutputChannels'] > 0:
                    devices['output'].append(device_data)
                    
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
        
        return devices
    
    def _set_state(self, new_state: ProcessingState):
        """Set processing state and notify callbacks."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            self.logger.debug(f"State changed: {old_state.value} -> {new_state.value}")
            
            if self.on_state_changed:
                self.on_state_changed(new_state)
    
    def get_state(self) -> ProcessingState:
        """Get current processing state."""
        return self.state
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self.state == ProcessingState.SPEAKING
    
    def is_listening_for_wake_word(self) -> bool:
        """Check if listening for wake word."""
        return self.state == ProcessingState.WAKE_WORD_DETECTION
    
    def is_listening_for_command(self) -> bool:
        """Check if listening for command."""
        return self.state == ProcessingState.LISTENING
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            'audio': {
                'sample_rate': self.audio_config.sample_rate,
                'channels': self.audio_config.channels,
                'input_device': self.audio_config.input_device_index,
                'output_device': self.audio_config.output_device_index
            },
            'stt': {
                'engine': self.stt_config.engine.value,
                'model_size': self.stt_config.model_size,
                'language': self.stt_config.language
            },
            'tts': {
                'engine': self.tts_config.engine.value,
                'voice_id': self.tts_config.voice_config.voice_id,
                'rate': self.tts_config.voice_config.rate,
                'volume': self.tts_config.voice_config.volume
            },
            'wake_word': {
                'enabled': self.wake_word_config.enabled,
                'words': self.wake_word_config.wake_words,
                'sensitivity': self.wake_word_config.sensitivity
            },
            'state': self.state.value,
            'is_running': self.is_running
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        
        if self.audio:
            self.audio.terminate()
        
        if self.wake_word_detector:
            self.wake_word_detector.delete()
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        
        self.logger.info("Voice interface cleaned up")


# Convenience function for easy initialization
def create_voice_interface(config: Optional[Dict[str, Any]] = None) -> VoiceInterface:
    """
    Create and initialize a Voice Interface instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized VoiceInterface instance
    """
    return VoiceInterface(config)