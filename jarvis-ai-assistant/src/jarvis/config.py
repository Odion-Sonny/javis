"""
Configuration Management
Handles loading and managing configuration from various sources.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for Jarvis AI Assistant."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = self._get_default_config()
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            # Try to load from default locations
            self._load_from_default_locations()
        
        # Override with environment variables
        self._load_from_environment()
        
        self.logger.info("Configuration loaded successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "ai": {
                "provider": "mock",  # mock, openai, anthropic
                "model": "gpt-3.5-turbo",
                "api_key": None,
                "base_url": None,
                "max_tokens": 1000,
                "temperature": 0.7,
                "system_prompt": (
                    "You are Jarvis, an intelligent AI assistant. "
                    "You are helpful, harmless, and honest. "
                    "You can help with various tasks including answering questions, "
                    "providing information, and assisting with system operations when appropriate."
                )
            },
            "voice": {
                "wake_word": "jarvis",
                "language": "en-US",
                "engine": "default",
                "input_device": None,
                "output_device": None,
                "noise_threshold": 0.5,
                "pause_threshold": 0.8
            },
            "memory": {
                "max_context_length": 4000,
                "context_window_hours": 24,
                "db_path": "jarvis_memory.db"
            },
            "system_tools": {
                "enabled": True,
                "allowed_commands": [
                    "ls", "pwd", "date", "whoami", "uname", "df", "free", "ps", "top"
                ],
                "blocked_commands": [
                    "rm", "sudo", "su", "chmod", "chown", "passwd", "dd", "mkfs", "fdisk"
                ],
                "max_execution_time": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/jarvis.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "security": {
                "require_confirmation": True,
                "safe_mode": True,
                "allowed_file_extensions": [".txt", ".json", ".csv", ".log"],
                "blocked_directories": ["/etc", "/usr", "/bin", "/sbin"]
            }
        }
    
    def _load_from_file(self, config_path: str):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
            
            self._merge_config(self.config, file_config)
            self.logger.info(f"Configuration loaded from: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration from file: {e}")
    
    def _load_from_default_locations(self):
        """Try to load configuration from default locations."""
        default_paths = [
            "config/jarvis.json",
            "jarvis.json",
            os.path.expanduser("~/.jarvis/config.json"),
            "/etc/jarvis/config.json"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                self._load_from_file(path)
                break
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        env_mappings = {
            "JARVIS_AI_PROVIDER": ["ai", "provider"],
            "JARVIS_AI_MODEL": ["ai", "model"],
            "JARVIS_AI_API_KEY": ["ai", "api_key"],
            "JARVIS_AI_BASE_URL": ["ai", "base_url"],
            "JARVIS_VOICE_WAKE_WORD": ["voice", "wake_word"],
            "JARVIS_VOICE_LANGUAGE": ["voice", "language"],
            "JARVIS_MEMORY_DB_PATH": ["memory", "db_path"],
            "JARVIS_LOG_LEVEL": ["logging", "level"]
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(self.config, config_path, value)
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, config: Dict[str, Any], path: list, value: str):
        """Set a nested configuration value."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if value.lower() in ('true', 'false'):
            current[path[-1]] = value.lower() == 'true'
        elif value.isdigit():
            current[path[-1]] = int(value)
        else:
            try:
                current[path[-1]] = float(value)
            except ValueError:
                current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save(self, config_path: str):
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    @property
    def ai(self) -> Dict[str, Any]:
        """Get AI configuration."""
        return self.config["ai"]
    
    @property
    def voice(self) -> Dict[str, Any]:
        """Get voice configuration."""
        return self.config["voice"]
    
    @property
    def memory(self) -> Dict[str, Any]:
        """Get memory configuration."""
        return self.config["memory"]
    
    @property
    def system_tools(self) -> Dict[str, Any]:
        """Get system tools configuration."""
        return self.config["system_tools"]
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config["logging"]
    
    @property
    def security(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.config["security"]
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Validate AI configuration
        ai_provider = self.get("ai.provider")
        if ai_provider in ["openai", "anthropic"] and not self.get("ai.api_key"):
            errors.append(f"API key required for AI provider: {ai_provider}")
        
        # Validate paths
        db_path = self.get("memory.db_path")
        if db_path:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create database directory: {e}")
        
        # Log validation errors
        for error in errors:
            self.logger.error(f"Configuration validation error: {error}")
        
        return len(errors) == 0
    
    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        safe_config = self._sanitize_config(self.config.copy())
        return json.dumps(safe_config, indent=2)
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from configuration."""
        sensitive_keys = ["api_key", "password", "token", "secret"]
        
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = self._sanitize_config(value)
            elif any(sensitive in key.lower() for sensitive in sensitive_keys):
                config[key] = "***" if value else None
        
        return config