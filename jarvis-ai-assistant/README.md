# Jarvis AI Assistant

A sophisticated, voice-controlled AI assistant with system integration capabilities, built with Python. Jarvis combines natural language processing, voice interaction, memory management, and secure system tool execution to provide a comprehensive AI assistant experience.

## Features

- 🤖 **AI Integration**: Support for multiple AI providers (OpenAI, Anthropic, or mock for development)
- 🎤 **Voice Processing**: Speech-to-text and text-to-speech capabilities with wake word detection
- 🧠 **Memory Management**: Persistent conversation history with intelligent context management
- 🛠️ **System Tools**: Safe execution of system commands with security controls
- 💬 **CLI Interface**: Interactive command-line interface for easy interaction
- ⚙️ **Flexible Configuration**: JSON-based configuration with environment variable overrides
- 🔒 **Security First**: Built-in security controls and command filtering

## Quick Start

### Installation

1. Clone or download the project:
```bash
cd jarvis-ai-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

1. **CLI Mode** (Recommended for getting started):
```bash
python main.py --mode cli
```

2. **Voice Mode** (requires additional setup):
```bash
python main.py --mode voice
```

3. **Daemon Mode** (background service):
```bash
python main.py --mode daemon
```

### Configuration

1. Copy the template environment file:
```bash
cp .env.template .env
```

2. Edit `.env` with your API keys and preferences:
```bash
# AI Configuration
JARVIS_AI_PROVIDER=openai  # or 'anthropic' or 'mock'
JARVIS_AI_API_KEY=your_api_key_here
JARVIS_AI_MODEL=gpt-3.5-turbo

# Voice Configuration
JARVIS_VOICE_WAKE_WORD=jarvis
JARVIS_VOICE_LANGUAGE=en-US
```

3. Optionally, customize `config/jarvis.json` for advanced settings.

## Project Structure

```
jarvis-ai-assistant/
├── main.py                 # Application entry point
├── src/
│   └── jarvis/
│       ├── __init__.py
│       ├── core.py         # Main orchestration logic
│       ├── cli.py          # Command line interface
│       ├── config.py       # Configuration management
│       ├── voice/          # Voice processing module
│       │   ├── __init__.py
│       │   └── processor.py
│       ├── ai_integration/ # AI service integration
│       │   ├── __init__.py
│       │   └── client.py
│       ├── memory/         # Memory and context management
│       │   ├── __init__.py
│       │   └── manager.py
│       ├── system_tools/   # System command execution
│       │   ├── __init__.py
│       │   └── manager.py
│       └── utils/          # Utility functions
│           ├── __init__.py
│           └── logger.py
├── config/
│   └── jarvis.json         # Default configuration
├── logs/                   # Application logs
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
├── .env.template          # Environment variables template
└── README.md              # This file
```

## Configuration

### AI Providers

**OpenAI**:
```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "your-openai-key"
  }
}
```

**Anthropic**:
```json
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "api_key": "your-anthropic-key"
  }
}
```

**Mock (Development)**:
```json
{
  "ai": {
    "provider": "mock"
  }
}
```

### Security Settings

Jarvis includes built-in security controls:

```json
{
  "system_tools": {
    "enabled": true,
    "allowed_commands": ["ls", "pwd", "date", "whoami"],
    "blocked_commands": ["rm", "sudo", "chmod"],
    "max_execution_time": 30
  },
  "security": {
    "require_confirmation": true,
    "safe_mode": true,
    "allowed_file_extensions": [".txt", ".json", ".csv"],
    "blocked_directories": ["/etc", "/usr", "/bin"]
  }
}
```

## Usage Examples

### CLI Commands

```bash
# Start interactive session
python main.py

# With specific configuration
python main.py --config /path/to/config.json

# Debug mode
python main.py --debug

# Show help
python main.py --help
```

### Interactive Examples

```
You: Hello Jarvis, how are you?
Jarvis: Hello! I'm Jarvis, your AI assistant. I'm doing well and ready to help you today!

You: What time is it?
Jarvis: The current time is 2024-01-15 14:30:22

You: List files in current directory
Jarvis: Here are the files in the current directory:
[Lists files using system tools]

You: help
Available Commands:
  help     - Show this help message
  exit     - Exit the application
  status   - Show system status
  memory   - Show conversation summary
  config   - Show configuration
```

## Development

### Setting up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

3. Code formatting:
```bash
black src/
```

4. Type checking:
```bash
mypy src/
```

### Extending Jarvis

**Adding New AI Providers**:
1. Extend `AIClient` class in `src/jarvis/ai_integration/client.py`
2. Add provider-specific response handling
3. Update configuration schema

**Adding New System Tools**:
1. Extend `SystemToolsManager` in `src/jarvis/system_tools/manager.py`
2. Add security validation for new tools
3. Update allowed commands in configuration

**Voice Processing**:
1. Implement real audio capture in `src/jarvis/voice/processor.py`
2. Integrate speech recognition libraries
3. Add TTS engine integration

## Security Considerations

- **Command Filtering**: Only whitelisted commands are executed
- **Timeout Protection**: Commands have execution time limits
- **Path Restrictions**: Blocked access to sensitive directories
- **Input Validation**: All user inputs are validated
- **API Key Protection**: Sensitive configuration is sanitized in logs

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in the project directory and virtual environment is activated
cd jarvis-ai-assistant
source venv/bin/activate
```

**Missing Dependencies**:
```bash
pip install -r requirements.txt
```

**Permission Issues**:
```bash
# Check file permissions
ls -la main.py
chmod +x main.py
```

**Database Issues**:
```bash
# Remove corrupted database
rm jarvis_memory.db
```

### Logs

Check logs for detailed error information:
```bash
tail -f logs/jarvis.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is open source. Please check the LICENSE file for details.

## Roadmap

- [ ] Advanced voice processing with noise cancellation
- [ ] Plugin system for third-party integrations
- [ ] Web interface
- [ ] Mobile app companion
- [ ] Advanced memory with semantic search
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Cloud deployment options

## Support

For questions, issues, or contributions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information
4. Join community discussions

---

**Jarvis AI Assistant** - Your intelligent companion for productivity and system management.