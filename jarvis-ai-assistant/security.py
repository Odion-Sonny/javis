#!/usr/bin/env python3
"""
Jarvis AI Assistant - Security Module

This module implements comprehensive security controls including:
- Command validation and sanitization
- Whitelist/blacklist management for system operations
- Dangerous command detection and blocking
- User confirmation for sensitive operations
- Audit logging of all system actions
- Input sanitization and validation
- Path traversal protection
- Command injection prevention

Security is the top priority - all operations are validated and logged.
"""

import os
import re
import sys
import json
import hashlib
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import shlex
import fnmatch
import getpass
import platform

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from jarvis.config import Config
    from jarvis.utils.logger import setup_logger
except ImportError:
    # Fallback logging if Jarvis modules not available
    logging.basicConfig(level=logging.INFO)


class SecurityLevel(Enum):
    """Security levels for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OperationType(Enum):
    """Types of operations that can be performed."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"
    ADMIN = "admin"


class ThreatLevel(Enum):
    """Threat levels for detected risks."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    @property
    def value_name(self):
        """Get the string name of the threat level."""
        names = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}
        return names[self.value]


@dataclass
class SecurityViolation:
    """Represents a security violation or threat."""
    violation_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    operation_type: OperationType
    command: str
    reason: str
    blocked: bool
    user_confirmed: bool = False
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityRule:
    """Represents a security rule."""
    rule_id: str
    name: str
    description: str
    pattern: str
    threat_level: ThreatLevel
    operation_type: OperationType
    action: str  # "block", "warn", "confirm"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""
    entry_id: str
    timestamp: datetime
    operation_type: OperationType
    command: str
    user: str
    result: str  # "allowed", "blocked", "confirmed"
    threat_level: ThreatLevel
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityManager:
    """
    Comprehensive security manager for Jarvis AI Assistant.
    
    Provides command validation, threat detection, access control,
    and audit logging for all system operations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the security manager.
        
        Args:
            config_path: Path to security configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "config/security.json"
        
        # Security state
        self.enabled = True
        self.safe_mode = True
        self.require_confirmation = True
        
        # Security rules and patterns
        self.dangerous_commands: Set[str] = set()
        self.allowed_commands: Set[str] = set()
        self.blocked_paths: Set[str] = set()
        self.allowed_paths: Set[str] = set()
        self.security_rules: List[SecurityRule] = []
        
        # Pattern matching
        self.dangerous_patterns: List[re.Pattern] = []
        self.suspicious_patterns: List[re.Pattern] = []
        
        # Audit logging
        self.audit_log: List[AuditLogEntry] = []
        self.max_audit_entries = 10000
        self.violations: List[SecurityViolation] = []
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_commands_per_minute = 60
        
        # Initialize security configuration
        self._load_security_config()
        self._initialize_default_rules()
        self._setup_audit_logging()
        
        self.logger.info("Security manager initialized")
    
    def _load_security_config(self):
        """Load security configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                self.enabled = config.get('enabled', True)
                self.safe_mode = config.get('safe_mode', True)
                self.require_confirmation = config.get('require_confirmation', True)
                
                # Load command lists
                self.dangerous_commands.update(config.get('dangerous_commands', []))
                self.allowed_commands.update(config.get('allowed_commands', []))
                self.blocked_paths.update(config.get('blocked_paths', []))
                self.allowed_paths.update(config.get('allowed_paths', []))
                
                # Load security rules
                for rule_data in config.get('security_rules', []):
                    rule = SecurityRule(
                        rule_id=rule_data['rule_id'],
                        name=rule_data['name'],
                        description=rule_data['description'],
                        pattern=rule_data['pattern'],
                        threat_level=ThreatLevel(rule_data['threat_level']),
                        operation_type=OperationType(rule_data['operation_type']),
                        action=rule_data['action'],
                        enabled=rule_data.get('enabled', True),
                        metadata=rule_data.get('metadata', {})
                    )
                    self.security_rules.append(rule)
                
                self.logger.info(f"Security configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Security config file not found: {self.config_path}")
                self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load security configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default security configuration."""
        default_config = {
            "enabled": True,
            "safe_mode": True,
            "require_confirmation": True,
            "dangerous_commands": [
                "rm", "rmdir", "del", "format", "fdisk", "mkfs",
                "dd", "sudo", "su", "passwd", "chmod", "chown",
                "kill", "killall", "pkill", "reboot", "shutdown",
                "halt", "poweroff", "init", "systemctl", "service",
                "mount", "umount", "crontab", "at", "batch",
                "nc", "netcat", "telnet", "ssh", "scp", "rsync",
                "wget", "curl", "ftp", "sftp", "python", "python3",
                "perl", "ruby", "node", "npm", "pip", "gem",
                "docker", "podman", "kubectl", "helm"
            ],
            "allowed_commands": [
                "ls", "dir", "pwd", "cd", "cat", "more", "less",
                "head", "tail", "grep", "find", "which", "whereis",
                "date", "time", "whoami", "id", "groups", "uptime",
                "df", "du", "free", "ps", "top", "htop", "who",
                "w", "last", "history", "uname", "hostname",
                "echo", "printf", "wc", "sort", "uniq", "cut",
                "awk", "sed", "tr", "tee", "diff", "cmp"
            ],
            "blocked_paths": [
                "/etc", "/usr", "/bin", "/sbin", "/boot", "/proc",
                "/sys", "/dev", "/root", "/var/log", "/var/run",
                "/tmp/.*\\.sh$", "/tmp/.*\\.py$", "/tmp/.*\\.exe$",
                "C:\\Windows", "C:\\Program Files", "C:\\System32"
            ],
            "allowed_paths": [
                "~/", "./", "/home/$USER", "/Users/$USER",
                "/tmp", "/var/tmp", "/usr/local/share"
            ],
            "security_rules": []
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self.logger.info(f"Default security configuration created: {self.config_path}")
            
            # Load the default configuration
            self._load_security_config()
            
        except Exception as e:
            self.logger.error(f"Failed to create default security configuration: {e}")
    
    def _initialize_default_rules(self):
        """Initialize default security rules and patterns."""
        # Dangerous command patterns
        dangerous_patterns = [
            r'\brm\s+-rf\s+/',  # rm -rf /
            r'\bdd\s+if=.*of=/',  # dd operations on root
            r'\bfork\s*\(\s*\)\s*while\s*\(\s*1\s*\)',  # Fork bombs
            r':\(\)\{.*:\|:&\};:',  # Classic fork bomb
            r'\beval\s*\(',  # Code evaluation
            r'\bexec\s*\(',  # Code execution
            r'\b(wget|curl).*\|\s*(sh|bash|python)',  # Download and execute
            r'\bsudo\s+.*\s+/.*',  # Sudo with paths
            r'\bchmod\s+777',  # Dangerous permissions
            r'\>\s*/dev/(sda|hda|nvme)',  # Writing to disk devices
            r'\bmount.*--bind',  # Bind mounts
            r'\biptables.*ACCEPT.*0\.0\.0\.0',  # Firewall bypass
            r'\bnetcat.*-l.*-e',  # Reverse shells
            r'/bin/(sh|bash).*-c.*',  # Shell command injection
            r'\$\(.*\)',  # Command substitution
            r'`.*`',  # Backtick command execution
            r'\|\s*nc\s+',  # Pipe to netcat
            r'\bmkfifo.*\|\s*nc',  # Named pipe attacks
            r'\becho.*>\s*/etc/',  # Writing to system configs
            r'\bcat.*>\s*/etc/',  # Overwriting system files
        ]
        
        self.dangerous_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in dangerous_patterns]
        
        # Suspicious patterns (warn but don't block)
        suspicious_patterns = [
            r'\b(password|passwd|secret|key|token)\b',
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'\b[a-f0-9]{32,}\b',  # Potential hashes
            r'\bbase64\s+',  # Base64 encoding
            r'\bhexdump\s+',  # Hex dumps
            r'\bstrings\s+',  # Binary analysis
            r'\bgdb\s+',  # Debugger
            r'\bstrace\s+',  # System call tracing
            r'\bltrace\s+',  # Library call tracing
        ]
        
        self.suspicious_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in suspicious_patterns]
        
        self.logger.info("Default security rules initialized")
    
    def _setup_audit_logging(self):
        """Setup audit logging."""
        try:
            # Create audit log directory
            audit_dir = "logs/audit"
            os.makedirs(audit_dir, exist_ok=True)
            
            # Setup audit file handler
            audit_file = os.path.join(audit_dir, f"security_audit_{datetime.now().strftime('%Y%m%d')}.log")
            
            self.audit_logger = logging.getLogger('security_audit')
            self.audit_logger.setLevel(logging.INFO)
            
            # Remove existing handlers
            for handler in self.audit_logger.handlers[:]:
                self.audit_logger.removeHandler(handler)
            
            # Add file handler
            file_handler = logging.FileHandler(audit_file)
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            self.audit_logger.addHandler(file_handler)
            self.audit_logger.propagate = False
            
            self.logger.info(f"Audit logging setup: {audit_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup audit logging: {e}")
    
    def validate_command(self, command: str, operation_type: OperationType = OperationType.EXECUTE) -> Tuple[bool, str, ThreatLevel]:
        """
        Validate a command for security threats.
        
        Args:
            command: Command to validate
            operation_type: Type of operation being performed
            
        Returns:
            Tuple of (is_safe, reason, threat_level)
        """
        if not self.enabled:
            return True, "Security disabled", ThreatLevel.NONE
        
        start_time = time.time()
        
        try:
            # Sanitize input
            sanitized_command = self._sanitize_input(command)
            
            # Check rate limiting
            if not self._check_rate_limit():
                self._log_violation(
                    command, "Rate limit exceeded", ThreatLevel.HIGH, 
                    operation_type, blocked=True
                )
                return False, "Rate limit exceeded", ThreatLevel.HIGH
            
            # Check for dangerous patterns first (highest priority)
            for pattern in self.dangerous_patterns:
                if pattern.search(sanitized_command):
                    threat_level = ThreatLevel.CRITICAL
                    reason = f"Dangerous pattern detected: {pattern.pattern}"
                    self._log_violation(command, reason, threat_level, operation_type, blocked=True)
                    return False, reason, threat_level
            
            # Check against dangerous commands
            first_word = sanitized_command.split()[0] if sanitized_command.split() else ""
            
            if first_word in self.dangerous_commands:
                threat_level = ThreatLevel.HIGH
                reason = f"Dangerous command detected: {first_word}"
                
                if self.safe_mode:
                    self._log_violation(command, reason, threat_level, operation_type, blocked=True)
                    return False, reason, threat_level
                elif self.require_confirmation:
                    # Will be handled by confirmation system
                    return False, f"Confirmation required for: {first_word}", ThreatLevel.HIGH
            
            # Check if command is explicitly allowed
            if first_word in self.allowed_commands:
                # Still check for suspicious patterns
                threat_level = self._check_suspicious_patterns(sanitized_command)
                if threat_level == ThreatLevel.NONE:
                    self._log_audit(command, operation_type, "allowed", threat_level, time.time() - start_time)
                    return True, "Command allowed", threat_level
                else:
                    reason = "Suspicious patterns detected in allowed command"
                    self._log_violation(command, reason, threat_level, operation_type, blocked=False)
                    return True, reason, threat_level
            
            # Check security rules
            for rule in self.security_rules:
                if not rule.enabled:
                    continue
                
                if rule.operation_type != operation_type:
                    continue
                
                pattern = re.compile(rule.pattern, re.IGNORECASE)
                if pattern.search(sanitized_command):
                    if rule.action == "block":
                        self._log_violation(command, rule.description, rule.threat_level, operation_type, blocked=True)
                        return False, rule.description, rule.threat_level
                    elif rule.action == "confirm":
                        return False, f"Confirmation required: {rule.description}", rule.threat_level
                    elif rule.action == "warn":
                        self._log_violation(command, rule.description, rule.threat_level, operation_type, blocked=False)
                        # Continue checking other rules
            
            # Check for suspicious patterns
            threat_level = self._check_suspicious_patterns(sanitized_command)
            
            # Path validation for file operations
            if operation_type in [OperationType.READ, OperationType.WRITE, OperationType.DELETE]:
                path_valid, path_reason, path_threat = self._validate_path_access(sanitized_command)
                if not path_valid:
                    self._log_violation(command, path_reason, path_threat, operation_type, blocked=True)
                    return False, path_reason, path_threat
                if path_threat.value > threat_level.value:
                    threat_level = path_threat
            
            # Final decision
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] and self.safe_mode:
                reason = f"Command blocked due to {threat_level.value_name} threat level"
                self._log_violation(command, reason, threat_level, operation_type, blocked=True)
                return False, reason, threat_level
            
            # Command appears safe
            self._log_audit(command, operation_type, "allowed", threat_level, time.time() - start_time)
            return True, "Command validated", threat_level
            
        except Exception as e:
            self.logger.error(f"Error validating command: {e}")
            # Fail secure - block on error
            self._log_violation(command, f"Validation error: {e}", ThreatLevel.HIGH, operation_type, blocked=True)
            return False, f"Validation error: {e}", ThreatLevel.HIGH
    
    def _sanitize_input(self, input_str: str) -> str:
        """
        Sanitize input string to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())
        
        # Decode common encoding attempts
        try:
            # Handle URL encoding
            import urllib.parse
            sanitized = urllib.parse.unquote(sanitized)
        except:
            pass
        
        # Remove potentially dangerous characters in certain contexts
        # Note: This is basic sanitization - more context-specific sanitization may be needed
        
        return sanitized
    
    def _check_rate_limit(self) -> bool:
        """
        Check if current request is within rate limits.
        
        Returns:
            True if within limits, False otherwise
        """
        current_time = datetime.now()
        user = getpass.getuser()
        
        # Initialize user rate limit tracking
        if user not in self.rate_limits:
            self.rate_limits[user] = []
        
        # Remove old entries (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        self.rate_limits[user] = [
            timestamp for timestamp in self.rate_limits[user] 
            if timestamp > cutoff_time
        ]
        
        # Check if under limit
        if len(self.rate_limits[user]) >= self.max_commands_per_minute:
            return False
        
        # Add current request
        self.rate_limits[user].append(current_time)
        return True
    
    def _check_suspicious_patterns(self, command: str) -> ThreatLevel:
        """
        Check for suspicious patterns in command.
        
        Args:
            command: Command to check
            
        Returns:
            Highest threat level found
        """
        threat_level = ThreatLevel.NONE
        
        for pattern in self.suspicious_patterns:
            if pattern.search(command):
                if ThreatLevel.MEDIUM.value > threat_level.value:
                    threat_level = ThreatLevel.MEDIUM
        
        return threat_level
    
    def _validate_path_access(self, command: str) -> Tuple[bool, str, ThreatLevel]:
        """
        Validate file path access in command.
        
        Args:
            command: Command containing file paths
            
        Returns:
            Tuple of (is_valid, reason, threat_level)
        """
        # Extract potential file paths from command
        paths = self._extract_paths_from_command(command)
        
        for path in paths:
            # Normalize path
            try:
                normalized_path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
            except:
                # Invalid path
                return False, f"Invalid path: {path}", ThreatLevel.MEDIUM
            
            # Check against blocked paths
            for blocked_pattern in self.blocked_paths:
                if fnmatch.fnmatch(normalized_path, blocked_pattern) or normalized_path.startswith(blocked_pattern):
                    return False, f"Access denied to blocked path: {path}", ThreatLevel.HIGH
            
            # Check for path traversal attempts
            if '..' in path or path.startswith('/') and not any(
                fnmatch.fnmatch(normalized_path, allowed) for allowed in self.allowed_paths
            ):
                # Check if it's an allowed system path
                allowed = False
                for allowed_pattern in self.allowed_paths:
                    # Expand environment variables in allowed patterns
                    expanded_pattern = os.path.expandvars(allowed_pattern)
                    if fnmatch.fnmatch(normalized_path, expanded_pattern):
                        allowed = True
                        break
                
                if not allowed:
                    return False, f"Path traversal or unauthorized access attempt: {path}", ThreatLevel.HIGH
        
        return True, "Path access validated", ThreatLevel.NONE
    
    def _extract_paths_from_command(self, command: str) -> List[str]:
        """
        Extract file paths from a command string.
        
        Args:
            command: Command string to analyze
            
        Returns:
            List of potential file paths
        """
        paths = []
        
        try:
            # Use shlex to parse command properly
            tokens = shlex.split(command)
            
            for token in tokens:
                # Look for tokens that look like file paths
                if ('/' in token or '\\' in token or 
                    token.startswith('./') or token.startswith('../') or
                    token.startswith('~/')):
                    paths.append(token)
                
                # Look for file extensions
                if '.' in token and any(token.endswith(ext) for ext in [
                    '.txt', '.log', '.conf', '.cfg', '.ini', '.json', '.xml',
                    '.sh', '.py', '.pl', '.rb', '.js', '.exe', '.bat', '.ps1'
                ]):
                    paths.append(token)
        
        except ValueError:
            # If shlex fails, do basic parsing
            tokens = command.split()
            for token in tokens:
                if '/' in token or '\\' in token:
                    paths.append(token)
        
        return paths
    
    def request_user_confirmation(self, command: str, reason: str, threat_level: ThreatLevel) -> bool:
        """
        Request user confirmation for a potentially dangerous operation.
        
        Args:
            command: Command requiring confirmation
            reason: Reason for requiring confirmation
            threat_level: Threat level of the operation
            
        Returns:
            True if user confirmed, False otherwise
        """
        if not self.require_confirmation:
            return True
        
        try:
            print("\n" + "="*60)
            print("🚨 SECURITY WARNING 🚨")
            print("="*60)
            print(f"Command: {command}")
            print(f"Threat Level: {threat_level.value_name.upper()}")
            print(f"Reason: {reason}")
            print("="*60)
            
            if threat_level == ThreatLevel.CRITICAL:
                print("❌ CRITICAL THREAT: This operation is extremely dangerous!")
                print("This command has been blocked for your security.")
                return False
            
            print("⚠️  This operation may be dangerous. Are you sure you want to proceed?")
            print("Type 'yes' to confirm, or anything else to cancel:")
            
            response = input("Confirm (yes/N): ").strip().lower()
            confirmed = response == 'yes'
            
            # Log the confirmation attempt
            self._log_audit(
                command, OperationType.ADMIN, 
                "confirmed" if confirmed else "denied", 
                threat_level, 0.0,
                metadata={"confirmation_reason": reason}
            )
            
            if confirmed:
                print("✅ Operation confirmed by user")
            else:
                print("❌ Operation cancelled by user")
            
            return confirmed
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operation cancelled")
            return False
        except Exception as e:
            self.logger.error(f"Error requesting confirmation: {e}")
            return False
    
    def execute_with_security(self, command: str, operation_type: OperationType = OperationType.EXECUTE) -> Tuple[bool, str, Any]:
        """
        Execute a command with full security validation.
        
        Args:
            command: Command to execute
            operation_type: Type of operation
            
        Returns:
            Tuple of (success, message, result)
        """
        start_time = time.time()
        
        # Validate command
        is_safe, reason, threat_level = self.validate_command(command, operation_type)
        
        if not is_safe:
            if "Confirmation required" in reason:
                # Request user confirmation
                if self.request_user_confirmation(command, reason, threat_level):
                    # User confirmed, proceed with execution
                    pass
                else:
                    # User denied or confirmation failed
                    return False, "Operation cancelled by user", None
            else:
                # Command is blocked
                return False, f"Security violation: {reason}", None
        
        # Command is safe or confirmed, proceed with execution
        try:
            # Log the execution attempt
            self.audit_logger.info(f"EXECUTING: {command} [Type: {operation_type.value}, Threat: {threat_level.value_name}]")
            
            # Execute the command (this is a placeholder - actual execution would depend on the operation type)
            if operation_type == OperationType.EXECUTE:
                result = self._safe_execute(command)
            else:
                result = f"Mock execution of {operation_type.value} operation: {command}"
            
            execution_time = time.time() - start_time
            
            # Log successful execution
            self._log_audit(command, operation_type, "executed", threat_level, execution_time)
            
            return True, "Command executed successfully", result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Execution failed: {e}"
            
            # Log execution failure
            self._log_audit(command, operation_type, "failed", threat_level, execution_time, 
                          metadata={"error": str(e)})
            
            return False, error_msg, None
    
    def _safe_execute(self, command: str) -> str:
        """
        Safely execute a system command.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output
        """
        try:
            # Use subprocess with safety measures
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.getcwd(),  # Set working directory explicitly
                env=os.environ.copy()  # Use current environment
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Command failed with exit code {result.returncode}: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Execution error: {e}"
    
    def _log_violation(self, command: str, reason: str, threat_level: ThreatLevel, 
                      operation_type: OperationType, blocked: bool):
        """Log a security violation."""
        violation = SecurityViolation(
            violation_id=self._generate_id(),
            timestamp=datetime.now(),
            threat_level=threat_level,
            operation_type=operation_type,
            command=command,
            reason=reason,
            blocked=blocked,
            metadata={
                "user": getpass.getuser(),
                "platform": platform.system(),
                "pid": os.getpid()
            }
        )
        
        self.violations.append(violation)
        
        # Log to audit logger
        self.audit_logger.warning(
            f"VIOLATION: {reason} | Command: {command} | Threat: {threat_level.value_name} | Blocked: {blocked}"
        )
        
        # Log to main logger
        if blocked:
            self.logger.warning(f"Security violation blocked: {reason}")
        else:
            self.logger.info(f"Security warning: {reason}")
    
    def _log_audit(self, command: str, operation_type: OperationType, result: str, 
                   threat_level: ThreatLevel, execution_time: float, metadata: Optional[Dict] = None):
        """Log an audit entry."""
        entry = AuditLogEntry(
            entry_id=self._generate_id(),
            timestamp=datetime.now(),
            operation_type=operation_type,
            command=command,
            user=getpass.getuser(),
            result=result,
            threat_level=threat_level,
            execution_time=execution_time,
            metadata=metadata or {}
        )
        
        self.audit_log.append(entry)
        
        # Trim audit log if it gets too large
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries//2:]
        
        # Log to audit logger
        self.audit_logger.info(
            f"AUDIT: {result.upper()} | {operation_type.value} | {command} | "
            f"Threat: {threat_level.value_name} | Time: {execution_time:.3f}s | User: {getpass.getuser()}"
        )
    
    def _generate_id(self) -> str:
        """Generate a unique ID for violations and audit entries."""
        timestamp = datetime.now().isoformat()
        data = f"{timestamp}_{os.getpid()}_{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get current security status and statistics.
        
        Returns:
            Security status dictionary
        """
        recent_violations = [v for v in self.violations if v.timestamp > datetime.now() - timedelta(hours=24)]
        
        return {
            "enabled": self.enabled,
            "safe_mode": self.safe_mode,
            "require_confirmation": self.require_confirmation,
            "total_violations": len(self.violations),
            "recent_violations_24h": len(recent_violations),
            "total_audit_entries": len(self.audit_log),
            "security_rules_count": len(self.security_rules),
            "dangerous_commands_count": len(self.dangerous_commands),
            "allowed_commands_count": len(self.allowed_commands),
            "blocked_paths_count": len(self.blocked_paths),
            "threat_level_counts": {
                level.value_name: len([v for v in recent_violations if v.threat_level == level])
                for level in ThreatLevel
            }
        }
    
    def get_recent_violations(self, hours: int = 24) -> List[SecurityViolation]:
        """
        Get recent security violations.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent violations
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [v for v in self.violations if v.timestamp > cutoff_time]
    
    def get_audit_log(self, hours: int = 24) -> List[AuditLogEntry]:
        """
        Get recent audit log entries.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent audit entries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [entry for entry in self.audit_log if entry.timestamp > cutoff_time]
    
    def add_security_rule(self, rule: SecurityRule) -> bool:
        """
        Add a new security rule.
        
        Args:
            rule: Security rule to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate rule pattern
            re.compile(rule.pattern)
            
            self.security_rules.append(rule)
            self.logger.info(f"Security rule added: {rule.name}")
            return True
            
        except re.error as e:
            self.logger.error(f"Invalid regex pattern in security rule: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to add security rule: {e}")
            return False
    
    def remove_security_rule(self, rule_id: str) -> bool:
        """
        Remove a security rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            True if successful, False otherwise
        """
        for i, rule in enumerate(self.security_rules):
            if rule.rule_id == rule_id:
                removed_rule = self.security_rules.pop(i)
                self.logger.info(f"Security rule removed: {removed_rule.name}")
                return True
        
        self.logger.warning(f"Security rule not found: {rule_id}")
        return False
    
    def save_configuration(self) -> bool:
        """
        Save current security configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config = {
                "enabled": self.enabled,
                "safe_mode": self.safe_mode,
                "require_confirmation": self.require_confirmation,
                "dangerous_commands": list(self.dangerous_commands),
                "allowed_commands": list(self.allowed_commands),
                "blocked_paths": list(self.blocked_paths),
                "allowed_paths": list(self.allowed_paths),
                "security_rules": [
                    {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "description": rule.description,
                        "pattern": rule.pattern,
                        "threat_level": rule.threat_level.value_name,
                        "operation_type": rule.operation_type.value,
                        "action": rule.action,
                        "enabled": rule.enabled,
                        "metadata": rule.metadata
                    }
                    for rule in self.security_rules
                ]
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Security configuration saved: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save security configuration: {e}")
            return False
    
    def enable_safe_mode(self):
        """Enable safe mode (blocks all dangerous operations)."""
        self.safe_mode = True
        self.logger.info("Safe mode enabled")
    
    def disable_safe_mode(self):
        """Disable safe mode (allows dangerous operations with confirmation)."""
        self.safe_mode = False
        self.logger.warning("Safe mode disabled - dangerous operations may be allowed")
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up old audit logs and violations.
        
        Args:
            days: Number of days to keep
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean violations
        old_count = len(self.violations)
        self.violations = [v for v in self.violations if v.timestamp > cutoff_time]
        violations_removed = old_count - len(self.violations)
        
        # Clean audit log
        old_count = len(self.audit_log)
        self.audit_log = [entry for entry in self.audit_log if entry.timestamp > cutoff_time]
        audit_removed = old_count - len(self.audit_log)
        
        self.logger.info(f"Cleaned up {violations_removed} old violations and {audit_removed} old audit entries")


# Convenience functions for easy use
def create_security_manager(config_path: Optional[str] = None) -> SecurityManager:
    """
    Create and initialize a SecurityManager instance.
    
    Args:
        config_path: Path to security configuration file
        
    Returns:
        Initialized SecurityManager instance
    """
    return SecurityManager(config_path)


def validate_command_safety(command: str) -> Tuple[bool, str, str]:
    """
    Quick command safety validation.
    
    Args:
        command: Command to validate
        
    Returns:
        Tuple of (is_safe, reason, threat_level)
    """
    security_manager = SecurityManager()
    is_safe, reason, threat_level = security_manager.validate_command(command)
    return is_safe, reason, threat_level.value_name


if __name__ == "__main__":
    # Command-line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Jarvis Security Manager")
    parser.add_argument("command", help="Command to validate")
    parser.add_argument("--execute", action="store_true", help="Actually execute the command")
    parser.add_argument("--config", help="Security configuration file path")
    
    args = parser.parse_args()
    
    # Create security manager
    security_manager = SecurityManager(args.config)
    
    if args.execute:
        # Execute with security
        success, message, result = security_manager.execute_with_security(args.command)
        print(f"Success: {success}")
        print(f"Message: {message}")
        if result:
            print(f"Result: {result}")
    else:
        # Just validate
        is_safe, reason, threat_level = security_manager.validate_command(args.command)
        print(f"Safe: {is_safe}")
        print(f"Reason: {reason}")
        print(f"Threat Level: {threat_level.value_name}")