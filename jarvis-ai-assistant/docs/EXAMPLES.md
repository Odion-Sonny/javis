# Jarvis AI Assistant - Usage Examples

This document provides comprehensive examples of using Jarvis AI Assistant in various scenarios.

## Table of Contents

- [Basic Usage](#basic-usage)
- [AI Integration Examples](#ai-integration-examples)
- [Voice Interaction](#voice-interaction)
- [Security Examples](#security-examples)
- [Memory and Learning](#memory-and-learning)
- [System Management](#system-management)
- [CLI Management](#cli-management)
- [Advanced Scenarios](#advanced-scenarios)

---

## Basic Usage

### Starting Jarvis

#### Interactive CLI Mode
```bash
# Start basic CLI mode
python3 jarvis.py

# Or explicitly specify CLI mode
python3 jarvis.py --mode cli

# With debug output
python3 jarvis.py --debug
```

Example interaction:
```
🤖 Jarvis AI Assistant - Interactive CLI
Type 'help' for commands or just start chatting!
Press Ctrl+C to exit
--------------------------------------------------
You: Hello Jarvis, how are you?
Jarvis: Hello! I'm doing well and ready to assist you. How can I help you today?

You: What time is it?
Jarvis: The current time is 2:30 PM on June 27, 2025.

You: help
Available Commands:
  help        - Show this help message
  exit/quit   - Exit the application
  status      - Show system status
  health      - Show component health status
  ...
```

#### Single Command Execution
```bash
# Execute one command and exit
python3 jarvis_cli.py exec "What's the weather like today?"

# With JSON output
python3 jarvis_cli.py exec "List files in current directory" --output-format json

# With timeout
python3 jarvis_cli.py exec "Complex analysis task" --timeout 60
```

Example output:
```bash
$ python3 jarvis_cli.py exec "What's 2+2?"
The answer is 4.

$ python3 jarvis_cli.py exec "List files" --output-format json
{
  "command": "List files",
  "response": "Here are the files in the current directory:\n- jarvis.py\n- jarvis_cli.py\n- requirements.txt\n...",
  "timestamp": "2025-06-27T14:30:00"
}
```

---

## AI Integration Examples

### Multi-Provider Setup

#### Configuration
```json
{
  "ai": {
    "primary_provider": "openai",
    "fallback_providers": ["anthropic", "ollama"],
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4",
      "temperature": 0.7
    },
    "anthropic": {
      "api_key": "sk-ant-...",
      "model": "claude-3-sonnet-20240229"
    },
    "ollama": {
      "model": "llama2",
      "base_url": "http://localhost:11434"
    }
  }
}
```

#### Using Different Providers
```python
from jarvis import JarvisApplication

# Initialize with configuration
with JarvisApplication(config_path="config/jarvis.json") as jarvis:
    # This will use the primary provider (OpenAI)
    response = await jarvis.process_command("Explain quantum computing")
    print(response)
    
    # Check provider status
    health = jarvis.get_health_status()
    print(f"AI providers status: {health.components}")
```

#### Provider Fallback Example
```bash
# Check AI provider status
python3 jarvis_cli.py status --ai

# Output shows provider availability
{
  "ai_providers": {
    "openai": {"available": false, "error": "API key not provided"},
    "anthropic": {"available": true, "model_info": {"name": "claude-3-sonnet"}},
    "ollama": {"available": true, "model_info": {"name": "llama2"}}
  }
}
```

### Context and Memory Integration

```python
# Example with context
response = await jarvis.process_command(
    "Continue our discussion about machine learning",
    context={"topic": "AI", "previous_context": "neural networks"}
)

# Memory integration is automatic
# Jarvis remembers previous conversations
response1 = await jarvis.process_command("My name is Alice")
response2 = await jarvis.process_command("What's my name?")
# Response2 will include "Alice" from memory
```

---

## Voice Interaction

### Basic Voice Mode

```bash
# Start voice mode
python3 jarvis.py --mode voice

# Or with custom settings
python3 jarvis_cli.py voice --wake-word "computer" --continuous
```

Example voice interaction:
```
🎙️ Voice mode active. Say 'Jarvis' to get attention.
[User says: "Jarvis"]
🔊 Yes? How can I help you?
[User says: "What's the weather like?"]
🔊 The current weather is sunny with a temperature of 72°F.
```

### Advanced Voice Configuration

```json
{
  "voice": {
    "wake_word": "jarvis",
    "language": "en-US",
    "engine": "default",
    "stt": {
      "engine": "whisper_local",
      "model_size": "base"
    },
    "tts": {
      "engine": "pyttsx3",
      "voice_config": {
        "rate": 200,
        "volume": 0.9
      }
    }
  }
}
```

### Interactive Mode with Voice

```bash
# Enhanced interactive mode
python3 jarvis.py --mode interactive

# CLI with voice support
python3 jarvis_cli.py shell --voice --history
```

Example interaction:
```
🤖 Jarvis AI Assistant - Interactive Mode
You can type messages or speak (if voice is available)
Type 'help' for commands, or 'exit' to quit
--------------------------------------------------

[Type or speak your message]
You: Hello Jarvis
Jarvis: Hello! I'm here to help. What can I do for you?
🔊 [Speaks the response aloud]

You: [Speaks: "What time is it?"]
Jarvis: The current time is 2:45 PM.
🔊 [Speaks the response aloud]
```

---

## Security Examples

### Command Validation

```bash
# Safe commands are allowed
python3 security.py "ls -la"
# Output: Safe: True, Reason: Command allowed, Threat Level: none

# Dangerous commands are blocked
python3 security.py "rm -rf /"
# Output: Safe: False, Reason: Dangerous pattern detected, Threat Level: critical

# Suspicious commands get warnings
python3 security.py "grep password /etc/passwd"
# Output: Safe: True, Reason: Suspicious patterns detected, Threat Level: medium
```

### Secure Command Execution

```bash
# Execute with security validation
python3 security.py --execute "echo 'Hello World'"
# Output: Success: True, Message: Command executed successfully, Result: Hello World

# Dangerous command blocked
python3 security.py --execute "sudo rm important_file"
# Output: Success: False, Message: Security violation: Dangerous command detected: sudo
```

### Security Monitoring

```bash
# Real-time security status
python3 jarvis_cli.py status --health
```

Example output:
```json
{
  "health": {
    "overall_healthy": true,
    "components": {
      "memory_system": true,
      "ai_brain": true,
      "security_manager": true
    },
    "errors": [],
    "warnings": []
  }
}
```

### User Confirmation Example

When a dangerous command requires confirmation:
```
========================================================
🚨 SECURITY WARNING 🚨
========================================================
Command: sudo systemctl restart important-service
Threat Level: HIGH
Reason: Dangerous command detected: sudo
========================================================
⚠️  This operation may be dangerous. Are you sure you want to proceed?
Type 'yes' to confirm, or anything else to cancel:
Confirm (yes/N): yes
✅ Operation confirmed by user
```

---

## Memory and Learning

### Conversation Memory

```python
# Jarvis automatically maintains conversation context
with JarvisApplication() as jarvis:
    # First interaction
    response1 = await jarvis.process_command("My favorite color is blue")
    
    # Later interaction - Jarvis remembers
    response2 = await jarvis.process_command("What's my favorite color?")
    # Response: "Your favorite color is blue."
```

### Learning from Interactions

```bash
# Check learning status
python3 jarvis_cli.py status --memory
```

Example output:
```
🧠 Memory Summary:
  • Total conversations: 156
  • Recent conversations (7 days): 23
  • Total tasks: 45
  • Task success rate: 89.2%
  • Total preferences: 12
  • Avg preference confidence: 0.85
```

### Proactive Suggestions

```python
# Get suggestions based on patterns
suggestions = jarvis.get_proactive_suggestions()
for suggestion in suggestions:
    print(f"💡 {suggestion['content']}")
    print(f"   Confidence: {suggestion['confidence']:.2f}")
```

Example suggestions:
```
💡 Based on your recent activity, would you like me to check your calendar?
   Confidence: 0.78

💡 You often ask about weather around this time. Today's forecast: Sunny, 75°F
   Confidence: 0.65
```

### User Feedback Integration

```bash
# Give feedback on responses
You: status
Jarvis: [Shows system status]

You: feedback
📝 Feedback System:
Rate the last response (1-5, or 'skip'):
Rating: 5
Any specific comments? (optional, press Enter to skip):
Comment: Very helpful and detailed
✅ Thank you for your feedback!
```

---

## System Management

### System Information

```bash
# Get comprehensive system status
python3 jarvis_cli.py status --health --metrics --memory
```

Example output:
```
📊 Performance Metrics:
  • Uptime: 2:15:30
  • Total interactions: 47
  • Successful interactions: 45
  • Success rate: 95.7%
  • Average response time: 0.85s
  • Memory usage: 245.7 MB
  • CPU usage: 3.2%

🏥 Health Status:
  • Overall: ✅ Healthy
  • Last check: 2025-06-27 14:45:12
  
📦 Components:
  ✅ Memory System
  ✅ AI Brain
  ✅ Voice Processor
  ✅ System Tools
  ✅ Learning Module
```

### Configuration Management

```bash
# View current configuration
python3 jarvis_cli.py config show

# View specific section
python3 jarvis_cli.py config show --section ai --json

# Update configuration
python3 jarvis_cli.py config set ai.primary_provider anthropic
python3 jarvis_cli.py config set ai.anthropic.api_key "your-key"

# Validate configuration
python3 jarvis_cli.py config validate
```

### System Maintenance

```bash
# Install dependencies
python3 jarvis_cli.py system install

# Install optional dependencies
python3 jarvis_cli.py system install --optional

# Clean system data
python3 jarvis_cli.py system clean --logs
python3 jarvis_cli.py system clean --memory
python3 jarvis_cli.py system clean --all

# Backup system
python3 jarvis_cli.py system backup jarvis-backup-$(date +%Y%m%d).tar.gz
```

---

## CLI Management

### Professional CLI Usage

```bash
# Help system
python3 jarvis_cli.py --help
python3 jarvis_cli.py config --help
python3 jarvis_cli.py status --help

# Verbose output
python3 jarvis_cli.py -v status --health
python3 jarvis_cli.py -vv config show  # More verbose
python3 jarvis_cli.py -vvv exec "command"  # Maximum verbosity

# Quiet mode (errors only)
python3 jarvis_cli.py -q exec "command"

# Custom log file
python3 jarvis_cli.py --log-file custom.log exec "command"
```

### Scripting with CLI

```bash
#!/bin/bash
# Example automation script

# Check if Jarvis is healthy
if python3 jarvis_cli.py status --health --json | jq -r '.health.overall_healthy' | grep -q true; then
    echo "Jarvis is healthy, proceeding with tasks"
    
    # Execute commands
    python3 jarvis_cli.py exec "Generate daily report"
    python3 jarvis_cli.py exec "Check system resources"
    
    # Backup data
    python3 jarvis_cli.py system backup "daily-backup-$(date +%Y%m%d).tar.gz"
else
    echo "Jarvis health check failed"
    exit 1
fi
```

### Continuous Monitoring

```bash
# Watch system status (refresh every 5 seconds)
python3 jarvis_cli.py status --watch 5

# Monitor specific metrics
python3 jarvis_cli.py status --metrics --watch 10

# JSON output for monitoring tools
python3 jarvis_cli.py status --json | jq '.health.overall_healthy'
```

---

## Advanced Scenarios

### Daemon Mode Setup

```bash
# Start as background daemon
python3 jarvis_cli.py run --mode daemon --background --pid-file /var/run/jarvis.pid

# Check daemon status
ps aux | grep jarvis
cat /var/run/jarvis.pid

# Stop daemon
kill $(cat /var/run/jarvis.pid)
```

### Custom Workflow Integration

```python
#!/usr/bin/env python3
"""
Custom Jarvis integration example
"""
import asyncio
from jarvis import JarvisApplication

async def automated_workflow():
    """Example automated workflow using Jarvis."""
    
    with JarvisApplication(debug=False) as jarvis:
        # Morning routine
        tasks = [
            "Check system health",
            "Review overnight logs",
            "Generate status report",
            "Check weather forecast",
            "Summarize calendar for today"
        ]
        
        results = []
        for task in tasks:
            print(f"🤖 Processing: {task}")
            response = await jarvis.process_command(task)
            results.append(f"✅ {task}: {response[:100]}...")
            
        # Generate summary
        summary_prompt = f"Summarize these morning checks:\n" + "\n".join(results)
        summary = await jarvis.process_command(summary_prompt)
        
        print("\n📋 Morning Summary:")
        print(summary)

if __name__ == "__main__":
    asyncio.run(automated_workflow())
```

### Multi-User Environment

```bash
# User-specific configuration
export JARVIS_CONFIG="/home/alice/.jarvis/config.json"
python3 jarvis_cli.py config show

# User-specific logs
export JARVIS_LOG_DIR="/home/alice/.jarvis/logs"
python3 jarvis.py --mode cli

# Separate security policies per user
export JARVIS_SECURITY_CONFIG="/home/alice/.jarvis/security.json"
```

### Development and Testing

```python
#!/usr/bin/env python3
"""
Development testing example
"""
from security import SecurityManager
from jarvis import JarvisApplication

def test_security_scenarios():
    """Test various security scenarios."""
    security = SecurityManager()
    
    test_commands = [
        "ls -la",  # Should be safe
        "rm important_file",  # Should be blocked
        "grep secret /etc/passwd",  # Should warn
        "echo 'hello world'"  # Should be safe
    ]
    
    for cmd in test_commands:
        is_safe, reason, threat = security.validate_command(cmd)
        print(f"Command: {cmd}")
        print(f"  Safe: {is_safe}")
        print(f"  Reason: {reason}")
        print(f"  Threat: {threat.value_name}")
        print()

async def test_ai_responses():
    """Test AI response quality."""
    test_questions = [
        "What is machine learning?",
        "How do I sort a list in Python?",
        "What's the weather like?",
        "Explain quantum computing"
    ]
    
    with JarvisApplication() as jarvis:
        for question in test_questions:
            response = await jarvis.process_command(question)
            print(f"Q: {question}")
            print(f"A: {response[:200]}...")
            print()

if __name__ == "__main__":
    print("🔒 Testing Security...")
    test_security_scenarios()
    
    print("🤖 Testing AI Responses...")
    asyncio.run(test_ai_responses())
```

### Performance Monitoring

```bash
# Performance testing script
#!/bin/bash

echo "🚀 Jarvis Performance Test"
echo "========================="

# Test response times
for i in {1..10}; do
    echo "Test $i/10"
    time python3 jarvis_cli.py exec "What is 2+2?" > /dev/null
done

# Memory usage over time
echo "📊 Memory Usage Test"
for i in {1..5}; do
    python3 jarvis_cli.py status --metrics | grep "Memory usage"
    sleep 5
done

# Load testing
echo "⚡ Load Testing"
for i in {1..20}; do
    python3 jarvis_cli.py exec "Test command $i" &
done
wait

echo "✅ Performance test completed"
```

### Integration with External Tools

```python
#!/usr/bin/env python3
"""
Integration with external monitoring tools
"""
import json
import requests
from jarvis import JarvisApplication

def send_to_monitoring(data):
    """Send metrics to external monitoring system."""
    # Example: Send to Prometheus/Grafana
    response = requests.post(
        "http://monitoring-server/api/metrics",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    return response.status_code == 200

async def monitor_jarvis():
    """Monitor Jarvis and send metrics to external system."""
    with JarvisApplication() as jarvis:
        # Get system metrics
        metrics = jarvis.get_system_metrics()
        health = jarvis.get_health_status()
        
        # Convert to monitoring format
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "service": "jarvis-ai",
            "metrics": {
                "uptime_seconds": metrics.uptime.total_seconds(),
                "total_interactions": metrics.total_interactions,
                "success_rate": metrics.successful_interactions / max(metrics.total_interactions, 1),
                "avg_response_time": metrics.avg_response_time,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "healthy": health.overall_healthy
            }
        }
        
        # Send to monitoring system
        if send_to_monitoring(monitoring_data):
            print("✅ Metrics sent to monitoring system")
        else:
            print("❌ Failed to send metrics")

if __name__ == "__main__":
    asyncio.run(monitor_jarvis())
```

---

## Common Use Cases

### 1. Daily Assistant
```bash
# Morning routine
python3 jarvis_cli.py exec "Good morning! What's on my schedule today?"
python3 jarvis_cli.py exec "Check the weather forecast"
python3 jarvis_cli.py exec "Any important news updates?"
```

### 2. Development Helper
```bash
# Code assistance
python3 jarvis_cli.py exec "Explain this Python error: AttributeError"
python3 jarvis_cli.py exec "How do I reverse a string in Python?"
python3 jarvis_cli.py exec "What's the best practice for error handling?"
```

### 3. System Administration
```bash
# System monitoring
python3 jarvis_cli.py status --health --metrics
python3 jarvis_cli.py exec "Check disk usage"
python3 jarvis_cli.py exec "Monitor system performance"
```

### 4. Research Assistant
```bash
# Research queries
python3 jarvis_cli.py exec "Summarize the latest developments in AI"
python3 jarvis_cli.py exec "Compare different machine learning algorithms"
python3 jarvis_cli.py exec "Explain blockchain technology"
```

### 5. Security Auditing
```bash
# Security checks
python3 security.py "sudo cat /etc/shadow"  # Test dangerous command
python3 jarvis_cli.py status --health  # Check security status
tail -f logs/audit/security_audit_*.log  # Monitor security events
```

---

For more examples and advanced usage patterns, see:
- [API Documentation](API.md) - Detailed API reference
- [Security Guide](SECURITY.md) - Security examples
- [Development Guide](DEVELOPMENT.md) - Development examples
- [Troubleshooting](TROUBLESHOOTING.md) - Problem-solving examples