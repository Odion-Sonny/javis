# Jarvis AI Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security](https://img.shields.io/badge/security-enhanced-green.svg)](docs/SECURITY.md)

Jarvis is an intelligent AI assistant with comprehensive system integration capabilities, featuring voice interaction, command execution, learning capabilities, and enterprise-grade security controls.

## 🌟 Features

- **🤖 Multi-Provider AI Integration**: Support for OpenAI, Anthropic, Ollama, and more
- **🎙️ Voice Interaction**: Speech-to-text and text-to-speech with wake word detection
- **🛡️ Enterprise Security**: Comprehensive command validation and audit logging
- **🧠 Learning System**: Adaptive behavior based on user interactions and preferences
- **💾 Advanced Memory**: Contextual conversation memory and task tracking
- **⚙️ System Integration**: Safe system command execution with security controls
- **📱 Multiple Interfaces**: CLI, voice, daemon, and interactive modes
- **🔧 Professional CLI**: Command-line management interface with subcommands

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Optional: Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/jarvis-ai-assistant.git
   cd jarvis-ai-assistant
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys** (optional but recommended):
   ```bash
   # Copy example configuration
   cp config/jarvis.json.example config/jarvis.json
   
   # Edit configuration with your API keys
   nano config/jarvis.json
   ```

### Basic Usage

#### Interactive CLI Mode
```bash
python3 jarvis.py --mode cli
```

#### Single Command Execution
```bash
python3 jarvis_cli.py exec "What's the weather like today?"
```

#### Voice Mode
```bash
python3 jarvis.py --mode voice
```

#### System Status
```bash
python3 jarvis_cli.py status --health --metrics
```

## 📋 Operation Modes

### 1. CLI Mode (Default)
Interactive command-line interface for ongoing conversations:
```bash
python3 jarvis.py --mode cli
# or simply
python3 jarvis.py
```

### 2. Voice Mode
Voice-controlled interaction with wake word detection:
```bash
python3 jarvis.py --mode voice
# or
python3 jarvis_cli.py voice --continuous
```

### 3. Interactive Mode
Enhanced CLI with optional voice integration:
```bash
python3 jarvis.py --mode interactive
# or
python3 jarvis_cli.py shell --voice
```

### 4. Daemon Mode
Background service for scheduled tasks and system monitoring:
```bash
python3 jarvis.py --mode daemon
# or
python3 jarvis_cli.py run --mode daemon --background
```

## 🛠️ Management Interface

The `jarvis_cli.py` provides professional command-line management:

### Configuration Management
```bash
# View configuration
python3 jarvis_cli.py config show --section ai

# Set configuration values
python3 jarvis_cli.py config set ai.primary_provider openai
python3 jarvis_cli.py config set ai.openai.api_key "your-key-here"

# Validate configuration
python3 jarvis_cli.py config validate
```

### System Monitoring
```bash
# System status
python3 jarvis_cli.py status --health --metrics

# Continuous monitoring
python3 jarvis_cli.py status --watch 5

# JSON output for scripting
python3 jarvis_cli.py status --json
```

### System Management
```bash
# Install dependencies
python3 jarvis_cli.py system install

# Clean logs and data
python3 jarvis_cli.py system clean --logs

# Backup system data
python3 jarvis_cli.py system backup backup.tar.gz
```

## 🔧 Configuration

### Main Configuration (`config/jarvis.json`)

```json
{
  "ai": {
    "primary_provider": "ollama",
    "fallback_providers": ["openai", "mock"],
    "openai": {
      "api_key": "your-openai-key",
      "model": "gpt-3.5-turbo"
    },
    "anthropic": {
      "api_key": "your-anthropic-key", 
      "model": "claude-3-sonnet-20240229"
    },
    "ollama": {
      "model": "llama2",
      "base_url": "http://localhost:11434"
    }
  },
  "voice": {
    "wake_word": "jarvis",
    "language": "en-US",
    "engine": "default"
  },
  "security": {
    "enabled": true,
    "safe_mode": true,
    "require_confirmation": true
  },
  "learning": {
    "enabled": true,
    "learning_interval_hours": 6
  }
}
```

### Security Configuration (`config/security.json`)

Automatically created with secure defaults. See [Security Documentation](docs/SECURITY.md) for details.

## 🛡️ Security Features

Jarvis includes enterprise-grade security controls:

- **Command Validation**: All system commands are validated before execution
- **Threat Detection**: Pattern-based detection of dangerous operations
- **Audit Logging**: Comprehensive logging of all security events
- **Path Protection**: Prevents unauthorized file system access
- **Rate Limiting**: Prevents command flooding attacks
- **User Confirmation**: Required for potentially dangerous operations

```bash
# Security status
python3 jarvis_cli.py status --health

# Validate a command
python3 security.py "rm important_file"  # Will be blocked

# Safe execution
python3 security.py --execute "ls -la"  # Will execute safely
```

## 🧠 Learning System

Jarvis learns from your interactions to provide better assistance:

- **Pattern Recognition**: Learns command usage patterns
- **Preference Extraction**: Adapts to your communication style
- **Proactive Suggestions**: Offers helpful suggestions based on context
- **Feedback Integration**: Improves responses based on your feedback

## 📚 Documentation

- [API Documentation](docs/API.md) - Detailed API reference
- [Security Guide](docs/SECURITY.md) - Security features and configuration
- [Development Setup](docs/DEVELOPMENT.md) - Setup for contributors
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Examples](docs/EXAMPLES.md) - Usage examples and scenarios

## 🔍 Project Structure

```
jarvis-ai-assistant/
├── jarvis.py                 # Main application orchestrator
├── jarvis_cli.py            # Professional CLI management interface
├── security.py              # Security validation and audit system
├── requirements.txt         # Python dependencies
├── config/
│   ├── jarvis.json         # Main configuration
│   └── security.json       # Security configuration
├── src/jarvis/
│   ├── ai_integration/      # AI provider integrations
│   ├── interfaces/          # User interfaces (CLI, etc.)
│   ├── learning/           # Learning and adaptation system
│   ├── memory/             # Memory and conversation management
│   ├── system_tools/       # System integration tools
│   ├── voice/              # Voice processing
│   └── utils/              # Utilities and helpers
├── logs/
│   ├── jarvis.log          # Application logs
│   └── audit/              # Security audit logs
├── docs/                   # Documentation
└── tests/                  # Test suite
```

## 🧪 Testing

Run the test suite:
```bash
python3 -m pytest tests/
```

Test specific components:
```bash
# Test security module
python3 security.py "echo 'test'"

# Test CLI management
python3 jarvis_cli.py exec "Hello Jarvis"

# Test system status
python3 jarvis_cli.py status --health
```

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](docs/DEVELOPMENT.md) for setup instructions.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python3 -m pytest`
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/jarvis-ai-assistant.git
cd jarvis-ai-assistant

# Create development environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run in development mode
python3 jarvis.py --debug
```

## 🔧 Troubleshooting

### Common Issues

**Installation Issues**:
```bash
# On macOS, you might need:
brew install portaudio  # For voice features

# On Ubuntu/Debian:
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Voice Recognition Not Working**:
```bash
# Install optional voice dependencies
python3 jarvis_cli.py system install --optional
```

**AI Provider Connection Issues**:
```bash
# Check configuration
python3 jarvis_cli.py config validate

# Test AI provider status
python3 jarvis_cli.py status --ai
```

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more detailed solutions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](docs/)
- [Issues](https://github.com/your-org/jarvis-ai-assistant/issues)
- [Discussions](https://github.com/your-org/jarvis-ai-assistant/discussions)
- [Wiki](https://github.com/your-org/jarvis-ai-assistant/wiki)

## 📞 Support

- **Documentation**: Check the [docs](docs/) directory
- **Issues**: Report bugs via [GitHub Issues](https://github.com/your-org/jarvis-ai-assistant/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/your-org/jarvis-ai-assistant/discussions)
- **Security**: Report security issues privately via email

## 🏆 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- Ollama for local LLM support
- All contributors and the open source community

---

**Built with ❤️ for developers who want an intelligent, secure, and extensible AI assistant.**