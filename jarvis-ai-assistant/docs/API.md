# Jarvis AI Assistant - API Documentation

This document provides comprehensive API documentation for all Jarvis modules and components.

## Table of Contents

- [Core Classes](#core-classes)
- [AI Integration](#ai-integration)
- [Security Module](#security-module)
- [Memory System](#memory-system)
- [Learning Module](#learning-module)
- [Voice Processing](#voice-processing)
- [System Tools](#system-tools)
- [CLI Management](#cli-management)

---

## Core Classes

### JarvisApplication

Main application orchestrator that manages all components and provides lifecycle management.

**Location**: `jarvis.py`

#### Constructor

```python
JarvisApplication(config_path: Optional[str] = None, debug: bool = False)
```

**Parameters**:
- `config_path` (str, optional): Path to configuration file
- `debug` (bool): Enable debug logging

#### Methods

##### `run(mode: OperationMode = OperationMode.CLI) -> int`

Run Jarvis in the specified operation mode.

**Parameters**:
- `mode` (OperationMode): Operation mode (CLI, VOICE, DAEMON, INTERACTIVE)

**Returns**: Exit code (0 for success, non-zero for error)

**Example**:
```python
from jarvis import JarvisApplication, OperationMode

with JarvisApplication(debug=True) as jarvis:
    exit_code = jarvis.run(OperationMode.CLI)
```

##### `async process_command(command: str, context: Optional[Dict[str, Any]] = None) -> str`

Process a user command and return the response.

**Parameters**:
- `command` (str): User command/input
- `context` (dict, optional): Optional context information

**Returns**: Response string

**Example**:
```python
response = await jarvis.process_command("What's the weather like?")
print(response)
```

##### `get_health_status() -> HealthStatus`

Get current health status of all components.

**Returns**: HealthStatus object with component status information

##### `get_system_metrics() -> SystemMetrics`

Get current system performance metrics.

**Returns**: SystemMetrics object with performance data

#### Data Classes

##### `HealthStatus`

```python
@dataclass
class HealthStatus:
    overall_healthy: bool
    components: Dict[str, bool]
    last_check: datetime
    errors: List[str]
    warnings: List[str]
```

##### `SystemMetrics`

```python
@dataclass
class SystemMetrics:
    uptime: timedelta
    total_interactions: int
    successful_interactions: int
    avg_response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
```

---

## AI Integration

### AIBrain

Main AI integration class that handles multiple AI providers.

**Location**: `src/jarvis/ai_integration/ai_brain.py`

#### Constructor

```python
AIBrain(config: Dict[str, Any], memory_system: MemorySystem)
```

#### Methods

##### `async process_message(message: str, context_override: Optional[Dict] = None) -> AIResponse`

Process a message using the configured AI provider.

**Parameters**:
- `message` (str): User message to process
- `context_override` (dict, optional): Override default context

**Returns**: AIResponse object

##### `get_provider_status() -> Dict[str, Dict[str, Any]]`

Get status of all configured AI providers.

**Returns**: Dictionary mapping provider names to their status

#### AI Providers

##### OpenAIProvider

```python
class OpenAIProvider:
    def __init__(self, config: Dict[str, Any])
    async def generate_response(self, message: str, context: Optional[Dict] = None) -> AIResponse
    def get_status() -> Dict[str, Any]
```

##### AnthropicProvider

```python
class AnthropicProvider:
    def __init__(self, config: Dict[str, Any])
    async def generate_response(self, message: str, context: Optional[Dict] = None) -> AIResponse
    def get_status() -> Dict[str, Any]
```

##### OllamaProvider

```python
class OllamaProvider:
    def __init__(self, config: Dict[str, Any])
    async def generate_response(self, message: str, context: Optional[Dict] = None) -> AIResponse
    def get_status() -> Dict[str, Any]
```

#### Data Classes

##### `AIResponse`

```python
@dataclass
class AIResponse:
    content: str
    provider: AIProvider
    intent: IntentType
    confidence: float
    tokens_used: int
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Security Module

### SecurityManager

Comprehensive security manager for command validation and threat detection.

**Location**: `security.py`

#### Constructor

```python
SecurityManager(config_path: Optional[str] = None)
```

#### Methods

##### `validate_command(command: str, operation_type: OperationType = OperationType.EXECUTE) -> Tuple[bool, str, ThreatLevel]`

Validate a command for security threats.

**Parameters**:
- `command` (str): Command to validate
- `operation_type` (OperationType): Type of operation

**Returns**: Tuple of (is_safe, reason, threat_level)

**Example**:
```python
from security import SecurityManager, OperationType

security = SecurityManager()
is_safe, reason, threat_level = security.validate_command("ls -la")
if is_safe:
    print("Command is safe to execute")
else:
    print(f"Command blocked: {reason}")
```

##### `execute_with_security(command: str, operation_type: OperationType = OperationType.EXECUTE) -> Tuple[bool, str, Any]`

Execute a command with full security validation.

**Parameters**:
- `command` (str): Command to execute
- `operation_type` (OperationType): Type of operation

**Returns**: Tuple of (success, message, result)

##### `request_user_confirmation(command: str, reason: str, threat_level: ThreatLevel) -> bool`

Request user confirmation for potentially dangerous operations.

**Parameters**:
- `command` (str): Command requiring confirmation
- `reason` (str): Reason for requiring confirmation
- `threat_level` (ThreatLevel): Threat level of the operation

**Returns**: True if user confirmed, False otherwise

#### Enums

##### `ThreatLevel`

```python
class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
```

##### `OperationType`

```python
class OperationType(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"
    ADMIN = "admin"
```

#### Security Configuration

The security module automatically creates a configuration file with:

```json
{
  "enabled": true,
  "safe_mode": true,
  "require_confirmation": true,
  "dangerous_commands": ["rm", "sudo", "dd", ...],
  "allowed_commands": ["ls", "cat", "pwd", ...],
  "blocked_paths": ["/etc", "/usr", "/bin", ...],
  "security_rules": []
}
```

---

## Memory System

### MemorySystem

Advanced memory management for conversations, tasks, and user preferences.

**Location**: `src/jarvis/memory/memory_system.py`

#### Constructor

```python
MemorySystem(config: Dict[str, Any])
```

#### Methods

##### `store_conversation(user_input: str, assistant_response: str, **kwargs) -> str`

Store a conversation entry in memory.

**Parameters**:
- `user_input` (str): User's input
- `assistant_response` (str): Assistant's response
- Additional keyword arguments for metadata

**Returns**: Conversation ID

##### `get_conversation_context(limit: int = 10) -> List[ConversationEntry]`

Get recent conversation context.

**Parameters**:
- `limit` (int): Maximum number of entries to return

**Returns**: List of conversation entries

##### `search_memory(query: str, limit: int = 10) -> Dict[str, Any]`

Search through stored conversations and data.

**Parameters**:
- `query` (str): Search query
- `limit` (int): Maximum results to return

**Returns**: Dictionary with search results

##### `learn_user_preference(key: str, value: str, category: PreferenceCategory, confidence: float = 1.0)`

Learn and store a user preference.

**Parameters**:
- `key` (str): Preference key
- `value` (str): Preference value
- `category` (PreferenceCategory): Category of preference
- `confidence` (float): Confidence level (0.0-1.0)

#### Data Classes

##### `ConversationEntry`

```python
@dataclass
class ConversationEntry:
    id: str
    user_input: str
    assistant_response: str
    timestamp: datetime
    interaction_type: InteractionType
    context_summary: str
    sentiment_score: float
    confidence_score: float
```

---

## Learning Module

### LearningModule

Adaptive learning system that improves based on user interactions.

**Location**: `src/jarvis/learning/learning_module.py`

#### Constructor

```python
LearningModule(config: Dict[str, Any], memory_system: MemorySystem)
```

#### Methods

##### `run_learning_cycle(force: bool = False) -> Dict[str, Any]`

Run a complete learning cycle to update patterns and preferences.

**Parameters**:
- `force` (bool): Force learning even if not due

**Returns**: Dictionary with learning results

##### `get_proactive_suggestions(context: str = "") -> List[Dict[str, Any]]`

Get proactive suggestions based on learned patterns.

**Parameters**:
- `context` (str): Current context for suggestions

**Returns**: List of suggestion dictionaries

##### `add_feedback(feedback_data: Dict[str, Any]) -> bool`

Add user feedback to improve learning.

**Parameters**:
- `feedback_data` (dict): Feedback information

**Returns**: True if successful

**Example**:
```python
feedback = {
    'feedback_type': 'positive',
    'rating': 5,
    'comment': 'Great response!',
    'timestamp': datetime.now().isoformat()
}
learning_module.add_feedback(feedback)
```

---

## Voice Processing

### VoiceProcessor

Simple voice processing interface.

**Location**: `src/jarvis/voice/processor.py`

#### Methods

##### `listen(timeout: float = 5.0) -> Optional[bytes]`

Listen for audio input.

**Parameters**:
- `timeout` (float): Maximum time to wait for input

**Returns**: Raw audio data or None

##### `speech_to_text(audio_data: bytes) -> Optional[str]`

Convert speech audio to text.

**Parameters**:
- `audio_data` (bytes): Raw audio data

**Returns**: Transcribed text or None

##### `text_to_speech(text: str, voice: Optional[str] = None) -> bool`

Convert text to speech and play it.

**Parameters**:
- `text` (str): Text to convert
- `voice` (str, optional): Voice to use

**Returns**: True if successful

### VoiceInterface

Advanced voice interface with wake word detection.

**Location**: `src/jarvis/voice/voice_interface.py`

#### Constructor

```python
VoiceInterface(config: Optional[Dict[str, Any]] = None)
```

#### Methods

##### `start_listening()`

Start continuous voice listening with wake word detection.

##### `stop_listening()`

Stop voice listening.

##### `record_speech(timeout: Optional[float] = None) -> VoiceResult`

Record and transcribe speech.

**Returns**: VoiceResult with transcription and metadata

##### `speak(text: str, save_to_file: Optional[str] = None) -> VoiceResult`

Convert text to speech and play it.

---

## System Tools

### SystemToolsManager

Safe system command execution with security integration.

**Location**: `src/jarvis/system_tools/manager.py`

#### Constructor

```python
SystemToolsManager(config: Dict[str, Any])
```

#### Methods

##### `async execute(command: str) -> Optional[str]`

Execute a system command safely.

**Parameters**:
- `command` (str): Command to execute

**Returns**: Command output or None if failed

##### `should_execute(response_content: str) -> bool`

Determine if response content requires system tool execution.

**Parameters**:
- `response_content` (str): AI response content

**Returns**: True if execution is needed

##### `get_system_info() -> Dict[str, Any]`

Get system information.

**Returns**: Dictionary with system details

---

## CLI Management

### JarvisCLI

Professional command-line interface for system management.

**Location**: `jarvis_cli.py`

#### Methods

##### `async run(argv: Optional[List[str]] = None) -> int`

Main CLI entry point.

**Parameters**:
- `argv` (list, optional): Command line arguments

**Returns**: Exit code

#### Usage Examples

```bash
# Configuration management
python3 jarvis_cli.py config show --section ai
python3 jarvis_cli.py config set ai.primary_provider openai
python3 jarvis_cli.py config validate

# System monitoring
python3 jarvis_cli.py status --health --metrics
python3 jarvis_cli.py status --watch 5

# Command execution
python3 jarvis_cli.py exec "What's the weather?"
python3 jarvis_cli.py shell --voice

# System management
python3 jarvis_cli.py system install --optional
python3 jarvis_cli.py system clean --logs
```

---

## Error Handling

### Exception Classes

#### JarvisError

Base exception class for Jarvis-specific errors.

```python
class JarvisError(Exception):
    """Base exception for Jarvis-related errors."""
    pass
```

#### SecurityViolationError

Raised when a security violation is detected.

```python
class SecurityViolationError(JarvisError):
    """Raised when a security violation is detected."""
    def __init__(self, command: str, reason: str, threat_level: ThreatLevel):
        self.command = command
        self.reason = reason
        self.threat_level = threat_level
        super().__init__(f"Security violation: {reason}")
```

#### ConfigurationError

Raised when there are configuration issues.

```python
class ConfigurationError(JarvisError):
    """Raised when there are configuration issues."""
    pass
```

---

## Best Practices

### Using the API

1. **Always use context managers** for JarvisApplication:
   ```python
   with JarvisApplication() as jarvis:
       result = jarvis.run()
   ```

2. **Handle exceptions appropriately**:
   ```python
   try:
       response = await jarvis.process_command(command)
   except SecurityViolationError as e:
       print(f"Security violation: {e.reason}")
   except JarvisError as e:
       print(f"Jarvis error: {e}")
   ```

3. **Use the security module** for any system operations:
   ```python
   from security import SecurityManager
   
   security = SecurityManager()
   is_safe, reason, threat_level = security.validate_command(command)
   if is_safe:
       # Proceed with execution
       pass
   ```

4. **Configure logging** appropriately:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

### Configuration

1. **Use environment variables** for sensitive data:
   ```bash
   export JARVIS_AI_OPENAI_API_KEY="your-key"
   export JARVIS_AI_ANTHROPIC_API_KEY="your-key"
   ```

2. **Validate configuration** before use:
   ```python
   config = Config()
   if config.validate():
       # Configuration is valid
       pass
   ```

### Security

1. **Always validate commands** before execution
2. **Use appropriate operation types** for different actions
3. **Monitor audit logs** regularly
4. **Keep security configuration updated**

---

## Examples

See [EXAMPLES.md](EXAMPLES.md) for comprehensive usage examples and scenarios.

## Support

For API-specific questions and issues:
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review [Example Usage](EXAMPLES.md)
- Open an issue on GitHub