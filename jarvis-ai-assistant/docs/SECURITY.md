# Jarvis AI Assistant - Security Guide

This document provides comprehensive information about Jarvis's security features, configuration, and best practices.

## Overview

Jarvis implements enterprise-grade security controls to ensure safe operation in any environment. Security is built into every layer of the system, from command validation to audit logging.

## Security Features

### 🛡️ Command Validation

All system commands are validated before execution using multiple security layers:

1. **Pattern-based Detection**: Regex patterns detect dangerous command structures
2. **Whitelist/Blacklist**: Commands are checked against known safe/dangerous lists
3. **Path Validation**: File system access is restricted to safe directories
4. **Input Sanitization**: All inputs are sanitized to prevent injection attacks

### 🔍 Threat Detection

The security system classifies threats into five levels:

| Level | Description | Action |
|-------|-------------|--------|
| **NONE** | Safe operation | Allow execution |
| **LOW** | Minor concern | Allow with logging |
| **MEDIUM** | Suspicious pattern | Allow with warning |
| **HIGH** | Dangerous operation | Require confirmation |
| **CRITICAL** | Extremely dangerous | Block completely |

### 📝 Audit Logging

All security events are logged to `logs/audit/security_audit_YYYYMMDD.log`:

```
2025-06-27 10:27:00 - AUDIT - WARNING - VIOLATION: Dangerous command detected: sudo | Command: sudo rm file | Threat: high | Blocked: True
2025-06-27 10:27:05 - AUDIT - INFO - AUDIT: ALLOWED | execute | ls -la | Threat: none | Time: 0.005s | User: admin
```

### 🚫 Access Control

- **Blocked Commands**: System-critical commands like `rm`, `sudo`, `dd`
- **Blocked Paths**: System directories like `/etc`, `/usr`, `/bin`
- **Rate Limiting**: Maximum 60 commands per minute per user
- **User Confirmation**: Required for high-risk operations

## Configuration

### Security Configuration File

Location: `config/security.json`

```json
{
  "enabled": true,
  "safe_mode": true,
  "require_confirmation": true,
  "dangerous_commands": [
    "rm", "rmdir", "del", "format", "fdisk", "mkfs",
    "dd", "sudo", "su", "passwd", "chmod", "chown",
    "kill", "killall", "pkill", "reboot", "shutdown"
  ],
  "allowed_commands": [
    "ls", "dir", "pwd", "cd", "cat", "more", "less",
    "head", "tail", "grep", "find", "which", "date"
  ],
  "blocked_paths": [
    "/etc", "/usr", "/bin", "/sbin", "/boot", "/proc",
    "/sys", "/dev", "/root", "/var/log", "/var/run"
  ],
  "allowed_paths": [
    "~/", "./", "/home/$USER", "/Users/$USER",
    "/tmp", "/var/tmp"
  ]
}
```

### Security Modes

#### Safe Mode (Default)

```python
# All dangerous operations are blocked
security.safe_mode = True
```

- Dangerous commands are completely blocked
- No user confirmation is possible for critical threats
- Maximum security, minimal risk

#### Confirmation Mode

```python
# Dangerous operations require user confirmation
security.safe_mode = False
security.require_confirmation = True
```

- Dangerous commands require explicit user confirmation
- Critical threats are still blocked
- Balanced security and functionality

#### Disabled Mode (Not Recommended)

```python
# Security validation is disabled
security.enabled = False
```

⚠️ **Warning**: Only disable security in completely trusted environments.

## Dangerous Patterns

### Critical Threat Patterns

These patterns are always blocked:

```regex
\brm\s+-rf\s+/                    # rm -rf /
\bdd\s+if=.*of=/                  # dd operations on root
\bchmod\s+777                     # Dangerous permissions
\b(wget|curl).*\|\s*(sh|bash)     # Download and execute
\$\(.*\)                          # Command substitution
:\(\)\{.*:\|:&\};:                # Fork bombs
```

### High Threat Commands

- `sudo` - Privilege escalation
- `su` - User switching
- `passwd` - Password changes
- `kill` - Process termination
- `mount`/`umount` - File system operations
- `crontab` - Scheduled tasks

### Suspicious Patterns

- `password`, `secret`, `key` - Potential credential exposure
- IP addresses - Network operations
- Base64 strings - Potential encoded payloads
- Binary analysis tools - `gdb`, `strace`, `strings`

## Usage Examples

### Basic Validation

```python
from security import SecurityManager

security = SecurityManager()

# Safe command
is_safe, reason, threat_level = security.validate_command("ls -la")
print(f"Safe: {is_safe}, Threat: {threat_level.value_name}")
# Output: Safe: True, Threat: none

# Dangerous command
is_safe, reason, threat_level = security.validate_command("rm -rf /")
print(f"Safe: {is_safe}, Reason: {reason}")
# Output: Safe: False, Reason: Dangerous pattern detected
```

### Secure Execution

```python
# Execute with full security validation
success, message, result = security.execute_with_security("echo 'Hello World'")
if success:
    print(f"Result: {result}")
else:
    print(f"Blocked: {message}")
```

### Command Line Validation

```bash
# Validate a command
python3 security.py "ls -la"
# Output: Safe: True, Reason: Command allowed, Threat Level: none

# Test dangerous command
python3 security.py "sudo rm important_file"
# Output: Safe: False, Reason: Dangerous command detected: sudo, Threat Level: high

# Execute with security
python3 security.py --execute "date"
# Output: Success: True, Message: Command executed successfully, Result: [current date]
```

## Security Monitoring

### Real-time Status

```python
# Get security status
status = security.get_security_status()
print(f"Enabled: {status['enabled']}")
print(f"Safe Mode: {status['safe_mode']}")
print(f"Recent Violations: {status['recent_violations_24h']}")
```

### CLI Monitoring

```bash
# Security health check
python3 jarvis_cli.py status --health

# Watch security events
python3 jarvis_cli.py status --watch 5

# View recent violations
tail -f logs/audit/security_audit_*.log
```

### Violation Analysis

```python
# Get recent violations
violations = security.get_recent_violations(hours=24)
for violation in violations:
    print(f"{violation.timestamp}: {violation.reason}")
    print(f"  Command: {violation.command}")
    print(f"  Threat: {violation.threat_level.value_name}")
    print(f"  Blocked: {violation.blocked}")
```

## Advanced Security Configuration

### Custom Security Rules

```python
from security import SecurityRule, ThreatLevel, OperationType

# Create custom rule
rule = SecurityRule(
    rule_id="custom_001",
    name="Block PowerShell",
    description="Block PowerShell execution",
    pattern=r"\bpowershell\b",
    threat_level=ThreatLevel.HIGH,
    operation_type=OperationType.EXECUTE,
    action="block"
)

# Add to security manager
security.add_security_rule(rule)
```

### Path Access Control

```python
# Add blocked path
security.blocked_paths.add("/sensitive/directory")

# Add allowed path
security.allowed_paths.add("/safe/workspace")

# Save configuration
security.save_configuration()
```

### Rate Limiting Configuration

```python
# Adjust rate limits
security.max_commands_per_minute = 30  # Reduce from default 60

# Check rate limit status
if not security._check_rate_limit():
    print("Rate limit exceeded")
```

## Security Best Practices

### For Administrators

1. **Enable Safe Mode** in production environments
2. **Monitor audit logs** regularly for suspicious activity
3. **Review security configuration** periodically
4. **Update blocked patterns** based on new threats
5. **Train users** on security warnings and confirmations

### For Developers

1. **Always validate commands** before execution
2. **Use appropriate operation types** for different actions
3. **Handle security exceptions** gracefully
4. **Test security rules** thoroughly
5. **Document security decisions** in code

### For Users

1. **Read security warnings** carefully before confirming
2. **Report false positives** to administrators
3. **Avoid bypassing security** controls
4. **Use specific commands** rather than broad patterns
5. **Keep software updated**

## Security Incident Response

### When a Command is Blocked

1. **Review the reason** for blocking
2. **Check if the command is necessary**
3. **Use alternative safe commands** if possible
4. **Contact administrator** if legitimate command is blocked

### Reporting Security Issues

1. **Document the issue** with full context
2. **Include command and error message**
3. **Provide system configuration**
4. **Report through appropriate channels**

### Security Violations

All violations are automatically logged. For investigation:

```bash
# View violation details
grep "VIOLATION" logs/audit/security_audit_*.log

# Check user activity
grep "User: username" logs/audit/security_audit_*.log

# Analyze threat patterns
grep "Threat: critical" logs/audit/security_audit_*.log
```

## Security Updates

### Updating Security Rules

```python
# Load current rules
security = SecurityManager()

# Add new dangerous pattern
security.dangerous_patterns.append(re.compile(r'\bnew_threat_pattern\b'))

# Save updated configuration
security.save_configuration()
```

### Updating Command Lists

```bash
# Add commands via CLI
python3 jarvis_cli.py config set security.dangerous_commands '["rm", "sudo", "new_dangerous_cmd"]'

# Validate updated configuration
python3 jarvis_cli.py config validate
```

## Compliance and Auditing

### Audit Log Format

```
TIMESTAMP - AUDIT - LEVEL - EVENT_TYPE: details | Command: command | Threat: level | Additional: metadata
```

### Compliance Features

- **Immutable audit logs** with timestamps
- **User attribution** for all actions
- **Threat level classification**
- **Command validation trails**
- **Configuration change tracking**

### Audit Analysis

```python
# Generate security report
audit_entries = security.get_audit_log(hours=24)
violations = security.get_recent_violations(hours=24)

report = {
    'total_commands': len(audit_entries),
    'violations': len(violations),
    'threat_distribution': {
        level.value_name: len([v for v in violations if v.threat_level == level])
        for level in ThreatLevel
    }
}
```

## Troubleshooting

### Common Issues

**Q: Legitimate command is being blocked**
```bash
# Check why command is blocked
python3 security.py "your_command"

# Check if command is in blocked list
python3 jarvis_cli.py config show --section security

# Request whitelist addition from administrator
```

**Q: Security validation is too slow**
```bash
# Check if too many patterns are configured
python3 jarvis_cli.py status --metrics

# Optimize security rules
# Review and remove unnecessary patterns
```

**Q: Audit logs are growing too large**
```bash
# Clean old logs
python3 jarvis_cli.py system clean --logs

# Configure log rotation in system settings
```

### Debug Mode

```python
# Enable debug logging for security
security = SecurityManager()
security.logger.setLevel(logging.DEBUG)

# Detailed validation output
is_safe, reason, threat_level = security.validate_command("command", debug=True)
```

## Security Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Input Sanitizer │───▶│ Pattern Matcher │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐           ▼
│   Audit Logger  │◀───│ Security Manager │◀───┌─────────────────┐
└─────────────────┘    └──────────────────┘    │ Threat Assessor │
                                │               └─────────────────┘
                                ▼
                       ┌──────────────────┐
                       │ Access Controller│
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Command Executor │
                       └──────────────────┘
```

This security system provides defense-in-depth protection while maintaining usability and transparency.

---

For more information, see:
- [API Documentation](API.md) - Security module API reference
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common security issues
- [Development Guide](DEVELOPMENT.md) - Security development practices