"""
System Tools Manager
Manages execution of system commands and tools.
"""

import logging
import subprocess
import os
import shutil
import psutil
from typing import Dict, Any, Optional, List
import json
import re


class SystemToolsManager:
    """Manages system tools and command execution."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize system tools manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Security settings
        self.allowed_commands = config.get("allowed_commands", [
            "ls", "pwd", "date", "whoami", "uname", "df", "free", "ps"
        ])
        self.blocked_commands = config.get("blocked_commands", [
            "rm", "sudo", "su", "chmod", "chown", "passwd", "dd"
        ])
        
        self.max_execution_time = config.get("max_execution_time", 30)
        
        self.logger.info("System tools manager initialized")
    
    def should_execute(self, response: str) -> bool:
        """
        Determine if the response contains system tool execution requests.
        
        Args:
            response: AI response text
            
        Returns:
            True if system tools should be executed
        """
        # Look for command patterns in the response
        command_patterns = [
            r"```bash\n(.*?)\n```",
            r"```shell\n(.*?)\n```",
            r"`([^`]+)`",
            r"execute:\s*(.+)",
            r"run:\s*(.+)"
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, response, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    async def execute(self, response: str) -> Optional[str]:
        """
        Execute system tools based on AI response.
        
        Args:
            response: AI response containing tool execution requests
            
        Returns:
            Tool execution results
        """
        try:
            commands = self._extract_commands(response)
            results = []
            
            for command in commands:
                if self._is_safe_command(command):
                    result = await self._execute_command(command)
                    results.append(f"Command: {command}\nResult: {result}")
                else:
                    results.append(f"Command: {command}\nResult: BLOCKED - Unsafe command")
            
            return "\n\n".join(results) if results else None
            
        except Exception as e:
            self.logger.error(f"Error executing system tools: {e}")
            return f"Error: {str(e)}"
    
    def _extract_commands(self, text: str) -> List[str]:
        """Extract commands from text."""
        commands = []
        
        # Extract from code blocks
        code_patterns = [
            r"```(?:bash|shell|sh)\n(.*?)\n```",
            r"`([^`\n]+)`"
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split multi-line commands
                lines = [line.strip() for line in match.split('\n') if line.strip()]
                commands.extend(lines)
        
        return commands
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        command_lower = command.lower().strip()
        
        # Check for blocked commands
        for blocked in self.blocked_commands:
            if command_lower.startswith(blocked.lower()):
                return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r"rm\s+-rf",
            r">\s*/dev/",
            r"sudo",
            r"su\s+",
            r"passwd",
            r"chmod\s+777",
            r"dd\s+if=",
            r"mkfs",
            r"fdisk"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False
        
        return True
    
    async def _execute_command(self, command: str) -> str:
        """Execute a single command safely."""
        try:
            # Use subprocess with timeout and security restrictions
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
                cwd=os.path.expanduser("~")  # Run in home directory
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nError: {result.stderr}"
            
            return output.strip() or "Command executed successfully (no output)"
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {self.max_execution_time} seconds"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            info = {
                "platform": os.name,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": {},
                "current_directory": os.getcwd(),
                "user": os.getlogin() if hasattr(os, 'getlogin') else "unknown"
            }
            
            # Get disk usage for common mount points
            common_paths = ["/", "/home", "C:\\", "D:\\"]
            for path in common_paths:
                if os.path.exists(path):
                    usage = shutil.disk_usage(path)
                    info["disk_usage"][path] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free
                    }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    def list_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return processes[:20]  # Return top 20 processes
            
        except Exception as e:
            self.logger.error(f"Error listing processes: {e}")
            return []
    
    def search_files(self, pattern: str, directory: str = ".", max_results: int = 50) -> List[str]:
        """Search for files matching a pattern."""
        try:
            matches = []
            directory = os.path.expanduser(directory)
            
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                
                for file in files:
                    if pattern.lower() in file.lower():
                        matches.append(os.path.join(root, file))
                        if len(matches) >= max_results:
                            break
                
                if len(matches) >= max_results:
                    break
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error searching files: {e}")
            return []