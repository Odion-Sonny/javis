# Jarvis AI Assistant - Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Jarvis AI Assistant.

## Quick Diagnostics

### Health Check
```bash
# Quick system health check
python3 jarvis_cli.py status --health

# Detailed diagnostics
python3 jarvis_cli.py status --health --metrics --ai --memory
```

### Configuration Validation
```bash
# Validate configuration
python3 jarvis_cli.py config validate

# Check specific configuration section
python3 jarvis_cli.py config show --section ai
```

### Log Analysis
```bash
# Check recent logs
tail -f logs/jarvis.log

# Check security audit logs
tail -f logs/audit/security_audit_*.log

# Search for specific errors
grep -i error logs/jarvis.log
```

---

## Installation Issues

### Python Version Issues

**Problem**: `python3: command not found` or version conflicts

**Solution**:
```bash
# Check Python version
python3 --version
# Should be 3.8 or higher

# On macOS with Homebrew
brew install python@3.11

# On Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip

# On CentOS/RHEL
sudo yum install python39 python39-pip
```

### Dependency Installation Failures

**Problem**: `pip install` fails with compilation errors

**Solution for macOS**:
```bash
# Install system dependencies
brew install portaudio
brew install ffmpeg

# Install Xcode command line tools
xcode-select --install

# Reinstall with verbose output
pip install -r requirements.txt -v
```

**Solution for Linux**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install portaudio19-dev python3-pyaudio
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install portaudio-devel
sudo yum install ffmpeg
```

**Solution for Windows**:
```powershell
# Install Visual C++ Build Tools
# Download from Microsoft website

# Install with conda (recommended)
conda install pyaudio
conda install -c conda-forge ffmpeg
```

### Virtual Environment Issues

**Problem**: Virtual environment not working or conflicts

**Solution**:
```bash
# Remove existing virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration Issues

### API Key Problems

**Problem**: AI providers not working, API key errors

**Symptoms**:
```
OpenAI API key not provided
Anthropic authentication failed
```

**Solution**:
```bash
# Set via configuration file
python3 jarvis_cli.py config set ai.openai.api_key "sk-your-key-here"
python3 jarvis_cli.py config set ai.anthropic.api_key "sk-ant-your-key"

# Set via environment variables
export JARVIS_AI_OPENAI_API_KEY="sk-your-key-here"
export JARVIS_AI_ANTHROPIC_API_KEY="sk-ant-your-key"

# Validate configuration
python3 jarvis_cli.py config validate

# Test AI provider
python3 jarvis_cli.py status --ai
```

### Configuration File Corruption

**Problem**: Configuration file is corrupted or invalid JSON

**Symptoms**:
```
JSON decode error in configuration
Configuration validation failed
```

**Solution**:
```bash
# Backup current config
cp config/jarvis.json config/jarvis.json.backup

# Reset to defaults
python3 jarvis_cli.py config reset --confirm

# Or manually recreate
rm config/jarvis.json
python3 jarvis.py  # Will create default config

# Validate new configuration
python3 jarvis_cli.py config validate
```

### Permission Issues

**Problem**: Cannot write to configuration or log files

**Symptoms**:
```
Permission denied: config/jarvis.json
Cannot create log directory
```

**Solution**:
```bash
# Fix file permissions
chmod 644 config/jarvis.json
chmod 755 config/
chmod 755 logs/

# Fix directory ownership
sudo chown -R $USER:$USER .

# Run with proper permissions
python3 jarvis.py
```

---

## Runtime Issues

### Memory Issues

**Problem**: High memory usage or out of memory errors

**Symptoms**:
```
MemoryError
Process killed due to memory usage
System becomes unresponsive
```

**Diagnostics**:
```bash
# Check memory usage
python3 jarvis_cli.py status --metrics

# Monitor memory over time
python3 jarvis_cli.py status --watch 5
```

**Solution**:
```bash
# Clean memory data
python3 jarvis_cli.py system clean --memory

# Reduce memory configuration
python3 jarvis_cli.py config set memory.max_context_length 2000
python3 jarvis_cli.py config set memory.context_window_hours 12

# Restart Jarvis
python3 jarvis.py
```

### Performance Issues

**Problem**: Slow response times or high CPU usage

**Symptoms**:
```
Response times > 5 seconds
High CPU usage (>80%)
System lag during operation
```

**Diagnostics**:
```bash
# Check performance metrics
python3 jarvis_cli.py status --metrics

# Profile specific command
time python3 jarvis_cli.py exec "test command"
```

**Solution**:
```bash
# Optimize AI configuration
python3 jarvis_cli.py config set ai.ollama.temperature 0.5
python3 jarvis_cli.py config set ai.context_window 5

# Disable learning temporarily
python3 jarvis_cli.py config set learning.enabled false

# Use faster AI model
python3 jarvis_cli.py config set ai.ollama.model "llama2:7b"
```

### Database Issues

**Problem**: Database corruption or access errors

**Symptoms**:
```
Database is locked
SQLite error: database disk image is malformed
Memory system initialization failed
```

**Solution**:
```bash
# Check database integrity
sqlite3 data/jarvis_memory.db "PRAGMA integrity_check;"

# Backup and recreate database
cp data/jarvis_memory.db data/jarvis_memory.db.backup
rm data/jarvis_memory.db

# Restart Jarvis (will create new database)
python3 jarvis.py

# If needed, restore from backup
# (Use database recovery tools)
```

---

## AI Provider Issues

### OpenAI Issues

**Problem**: OpenAI API errors or rate limiting

**Common Errors**:
```
Rate limit exceeded
Invalid API key
Model not available
```

**Solution**:
```bash
# Check API key
python3 jarvis_cli.py config get ai.openai.api_key

# Test with different model
python3 jarvis_cli.py config set ai.openai.model "gpt-3.5-turbo"

# Add retry logic (automatic in newer versions)
python3 jarvis_cli.py config set ai.openai.max_retries 3

# Check quota and billing at https://platform.openai.com/usage
```

### Anthropic/Claude Issues

**Problem**: Claude API connection issues

**Solution**:
```bash
# Verify API key format
python3 jarvis_cli.py config get ai.anthropic.api_key
# Should start with "sk-ant-"

# Test different model
python3 jarvis_cli.py config set ai.anthropic.model "claude-3-haiku-20240307"

# Check API status at https://status.anthropic.com/
```

### Ollama Issues

**Problem**: Local Ollama not responding

**Symptoms**:
```
Connection refused to localhost:11434
Ollama service not running
Model not found
```

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama service
ollama serve

# Pull required model
ollama pull llama2

# Test model
ollama run llama2 "Hello"

# Update Jarvis configuration
python3 jarvis_cli.py config set ai.ollama.base_url "http://localhost:11434"
python3 jarvis_cli.py config set ai.ollama.model "llama2"
```

---

## Voice Recognition Issues

### Microphone Not Working

**Problem**: Voice input not detected

**Symptoms**:
```
No audio input detected
Microphone permission denied
PyAudio error
```

**Solution for macOS**:
```bash
# Check microphone permissions
# System Preferences > Security & Privacy > Privacy > Microphone

# Install/reinstall PyAudio
brew install portaudio
pip uninstall pyaudio
pip install pyaudio

# Test microphone
python3 -c "import pyaudio; p=pyaudio.PyAudio(); print('Microphone available')"
```

**Solution for Linux**:
```bash
# Check audio devices
arecord -l

# Install ALSA development files
sudo apt-get install libasound2-dev

# Test recording
arecord -d 5 test.wav
aplay test.wav

# Reinstall PyAudio
pip install --force-reinstall pyaudio
```

### Speech Recognition Not Working

**Problem**: Speech not being converted to text

**Solution**:
```bash
# Install optional voice dependencies
python3 jarvis_cli.py system install --optional

# Test with different engine
python3 jarvis_cli.py config set voice.stt.engine "speech_recognition"

# Check internet connection (for online services)
curl -I https://www.google.com

# Use local Whisper model
python3 jarvis_cli.py config set voice.stt.engine "whisper_local"
pip install openai-whisper
```

### Text-to-Speech Issues

**Problem**: No audio output or TTS errors

**Solution**:
```bash
# Check audio output
# macOS: System Preferences > Sound > Output
# Linux: pulseaudio --check -v

# Test system TTS
# macOS: say "Hello World"
# Linux: espeak "Hello World"

# Configure TTS engine
python3 jarvis_cli.py config set voice.tts.engine "system"

# List available voices
python3 -c "import pyttsx3; engine=pyttsx3.init(); voices=engine.getProperty('voices'); [print(v.name) for v in voices]"
```

---

## Security Issues

### Commands Being Blocked Incorrectly

**Problem**: Legitimate commands are being blocked

**Symptoms**:
```
Command blocked: Dangerous command detected
Security violation: ls -la
False positive security warning
```

**Diagnostics**:
```bash
# Check why command is blocked
python3 security.py "your_command_here"

# Check security configuration
python3 jarvis_cli.py config show --section security

# Review security logs
grep "VIOLATION" logs/audit/security_audit_*.log
```

**Solution**:
```bash
# Add command to allowed list
python3 jarvis_cli.py config set security.allowed_commands '["ls", "cat", "your_command"]'

# Temporarily disable safe mode (not recommended)
python3 jarvis_cli.py config set security.safe_mode false

# Create custom security rule
# (See Security Guide for advanced configuration)
```

### Security Validation Too Slow

**Problem**: Security checks causing performance issues

**Solution**:
```bash
# Optimize security patterns
# Edit config/security.json to remove unnecessary patterns

# Disable learning for security (if enabled)
python3 jarvis_cli.py config set security.learning_enabled false

# Increase rate limits if needed
python3 jarvis_cli.py config set security.max_commands_per_minute 120
```

### Audit Logs Growing Too Large

**Problem**: Disk space issues due to large audit logs

**Solution**:
```bash
# Clean old logs
python3 jarvis_cli.py system clean --logs

# Configure log rotation
# Add to crontab:
# 0 0 * * * find /path/to/jarvis/logs -name "*.log" -mtime +30 -delete

# Reduce log verbosity
python3 jarvis_cli.py config set logging.level "WARNING"
```

---

## Network Issues

### Connection Timeouts

**Problem**: Network requests timing out

**Symptoms**:
```
Connection timeout
SSL certificate verification failed
DNS resolution failed
```

**Solution**:
```bash
# Check internet connectivity
ping google.com
curl -I https://api.openai.com

# Check DNS resolution
nslookup api.openai.com

# Test with different network
# (Try mobile hotspot or different WiFi)

# Configure proxy if needed
export https_proxy=http://proxy.company.com:8080
export http_proxy=http://proxy.company.com:8080
```

### SSL/TLS Issues

**Problem**: SSL certificate errors

**Solution**:
```bash
# Update certificates
# macOS: brew install ca-certificates
# Linux: sudo apt-get update && sudo apt-get install ca-certificates

# Python certificates
pip install --upgrade certifi

# Test SSL connection
python3 -c "import ssl; import urllib.request; urllib.request.urlopen('https://api.openai.com')"
```

---

## Development Issues

### Import Errors

**Problem**: Module import failures

**Symptoms**:
```
ModuleNotFoundError: No module named 'jarvis'
ImportError: cannot import name 'Config'
```

**Solution**:
```bash
# Check Python path
echo $PYTHONPATH

# Run from correct directory
cd /path/to/jarvis-ai-assistant
python3 jarvis.py

# Install in development mode
pip install -e .

# Check file permissions
ls -la src/jarvis/
```

### Testing Issues

**Problem**: Tests failing or not running

**Solution**:
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run specific test
python3 -m pytest tests/test_specific.py -v

# Run with debug output
python3 -m pytest tests/ -v -s

# Check test environment
python3 -c "import jarvis; print('Import successful')"
```

---

## Common Error Messages

### "Config object has no attribute 'learning'"

**Problem**: Missing configuration section

**Solution**:
```bash
# Reset configuration to include all sections
python3 jarvis_cli.py config reset --confirm

# Or add missing section manually
python3 jarvis_cli.py config set learning.enabled true
```

### "Database is locked"

**Problem**: SQLite database access issue

**Solution**:
```bash
# Kill any running Jarvis instances
pkill -f jarvis.py

# Remove lock file if exists
rm -f data/jarvis_memory.db-lock

# Restart Jarvis
python3 jarvis.py
```

### "Rate limit exceeded"

**Problem**: Too many requests to AI provider

**Solution**:
```bash
# Wait for rate limit reset (usually 1 minute)
sleep 60

# Use different AI provider
python3 jarvis_cli.py config set ai.primary_provider "anthropic"

# Reduce request frequency
# (Wait between commands)
```

### "Permission denied"

**Problem**: File system permission issues

**Solution**:
```bash
# Fix permissions
chmod -R 755 .
chown -R $USER:$USER .

# Run with sudo only if necessary (not recommended)
sudo python3 jarvis.py
```

---

## Getting Help

### Diagnostic Information Collection

When reporting issues, include:

```bash
# System information
python3 --version
uname -a
pip list | grep -E "(jarvis|openai|anthropic|ollama)"

# Configuration status
python3 jarvis_cli.py config validate
python3 jarvis_cli.py status --health --json

# Recent logs
tail -50 logs/jarvis.log
tail -20 logs/audit/security_audit_*.log

# Error reproduction
python3 jarvis_cli.py exec "problem command" --debug
```

### Debug Mode

Enable detailed debugging:

```bash
# Run with debug output
python3 jarvis.py --debug

# Verbose CLI output
python3 jarvis_cli.py -vvv exec "command"

# Enable debug logging in code
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Log Analysis

```bash
# Find errors in logs
grep -i "error\|exception\|failed" logs/jarvis.log

# Check security violations
grep "VIOLATION" logs/audit/security_audit_*.log

# Monitor real-time logs
tail -f logs/jarvis.log | grep -i error
```

### Community Support

1. **Check Documentation**: Review [API docs](API.md) and [examples](EXAMPLES.md)
2. **Search Issues**: Look for similar problems in GitHub issues
3. **Discord/Forums**: Join community discussions
4. **Create Issue**: Report bugs with diagnostic information

### Professional Support

For enterprise users:
- Include system specifications
- Provide reproduction steps
- Share sanitized configuration
- Include relevant log excerpts

---

## Prevention

### Regular Maintenance

```bash
# Weekly health check
python3 jarvis_cli.py status --health --metrics

# Monthly cleanup
python3 jarvis_cli.py system clean --logs
python3 jarvis_cli.py system clean --memory

# Quarterly backup
python3 jarvis_cli.py system backup "quarterly-backup-$(date +%Y%m%d).tar.gz"
```

### Monitoring

```bash
# Set up monitoring script
#!/bin/bash
while true; do
    if ! python3 jarvis_cli.py status --health --json | jq -e '.health.overall_healthy'; then
        echo "Jarvis health check failed at $(date)" >> health_failures.log
    fi
    sleep 300  # Check every 5 minutes
done
```

### Best Practices

1. **Keep backups** of working configurations
2. **Test changes** in development environment first
3. **Monitor logs** regularly for issues
4. **Update dependencies** periodically
5. **Follow security** guidelines

---

Still having issues? See the [API Documentation](API.md) for detailed technical information or create an issue on GitHub with your diagnostic information.