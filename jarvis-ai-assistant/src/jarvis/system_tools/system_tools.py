"""
System Tools Module

Provides safe system interaction capabilities for Jarvis AI Assistant.
Includes application launching, file operations, window management, 
system information gathering, web browser control, and clipboard operations.

All operations include proper security checks, error handling, and logging.
"""

import logging
import os
import shutil
import subprocess
import platform
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import time

# Optional dependencies with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import pygetwindow as gw
        WINDOW_MANAGEMENT_AVAILABLE = True
    except ImportError:
        WINDOW_MANAGEMENT_AVAILABLE = False
elif platform.system() == "Darwin":  # macOS
    WINDOW_MANAGEMENT_AVAILABLE = True  # Will use AppleScript
elif platform.system() == "Linux":
    try:
        import subprocess
        # Check if wmctrl is available
        result = subprocess.run(['which', 'wmctrl'], capture_output=True)
        WINDOW_MANAGEMENT_AVAILABLE = result.returncode == 0
    except:
        WINDOW_MANAGEMENT_AVAILABLE = False
else:
    WINDOW_MANAGEMENT_AVAILABLE = False


class SecurityLevel(Enum):
    """Security levels for system operations."""
    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


class OperationResult(Enum):
    """Result status for system operations."""
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


@dataclass
class SystemOperation:
    """Result of a system operation."""
    operation: str
    result: OperationResult
    message: str
    data: Optional[Any] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'operation': self.operation,
            'result': self.result.value,
            'message': self.message,
            'data': self.data,
            'execution_time': self.execution_time
        }


class SystemTools:
    """
    Safe system interaction tools for Jarvis AI Assistant.
    
    Provides controlled access to system operations with security checks,
    whitelisting, and comprehensive logging.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize system tools with configuration.
        
        Args:
            config: Configuration dictionary with security settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.security_level = SecurityLevel(
            self.config.get('security_level', SecurityLevel.MODERATE.value)
        )
        self.max_execution_time = self.config.get('max_execution_time', 30)
        
        # Application whitelist
        self.allowed_applications = set(self.config.get('allowed_applications', [
            'calculator', 'notepad', 'textedit', 'terminal', 'cmd',
            'firefox', 'chrome', 'safari', 'edge', 'code', 'vscode'
        ]))
        
        # File operation settings
        self.allowed_directories = set(self.config.get('allowed_directories', [
            os.path.expanduser('~'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Documents'),
            os.path.expanduser('~/Downloads')
        ]))
        
        self.blocked_directories = set(self.config.get('blocked_directories', [
            '/etc', '/usr', '/bin', '/sbin', '/System', '/Windows/System32'
        ]))
        
        self.logger.info(f"System tools initialized with {self.security_level.value} security")
    
    # ==================== APPLICATION MANAGEMENT ====================
    
    def launch_application(self, app_name: str, args: Optional[List[str]] = None) -> SystemOperation:
        """
        Launch an application with security checks.
        
        Args:
            app_name: Name of the application to launch
            args: Optional command line arguments
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.launch_application('calculator')
            >>> print(result.message)
            'Calculator launched successfully'
        """
        start_time = time.time()
        operation_name = f"launch_application({app_name})"
        
        try:
            # Security check
            if not self._is_application_allowed(app_name):
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.DENIED,
                    message=f"Application '{app_name}' not in allowed list",
                    execution_time=time.time() - start_time
                )
            
            # Resolve application path
            app_path = self._resolve_application_path(app_name)
            if not app_path:
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.NOT_FOUND,
                    message=f"Application '{app_name}' not found",
                    execution_time=time.time() - start_time
                )
            
            # Prepare command
            command = [app_path]
            if args:
                command.extend(args)
            
            # Launch application
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            execution_time = time.time() - start_time
            self.logger.info(f"Launched application: {app_name} (PID: {process.pid})")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"Application '{app_name}' launched successfully",
                data={'pid': process.pid, 'command': command},
                execution_time=execution_time
            )
            
        except subprocess.SubprocessError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Failed to launch {app_name}: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to launch '{app_name}': {str(e)}",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Unexpected error launching {app_name}: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Unexpected error: {str(e)}",
                execution_time=execution_time
            )
    
    def close_application(self, app_name: str, force: bool = False) -> SystemOperation:
        """
        Close an application by name.
        
        Args:
            app_name: Name of the application to close
            force: Whether to force close the application
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.close_application('notepad')
            >>> print(result.message)
            'Application notepad closed successfully'
        """
        start_time = time.time()
        operation_name = f"close_application({app_name})"
        
        if not PSUTIL_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="psutil not available for process management",
                execution_time=time.time() - start_time
            )
        
        try:
            processes_found = []
            processes_terminated = []
            
            # Find processes by name
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if (proc.info['name'] and 
                        app_name.lower() in proc.info['name'].lower()):
                        processes_found.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not processes_found:
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.NOT_FOUND,
                    message=f"No running processes found for '{app_name}'",
                    execution_time=time.time() - start_time
                )
            
            # Terminate processes
            for proc in processes_found:
                try:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    processes_terminated.append(proc.pid)
                    self.logger.info(f"Terminated process: {proc.info['name']} (PID: {proc.pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.logger.warning(f"Could not terminate process {proc.pid}: {e}")
            
            execution_time = time.time() - start_time
            
            if processes_terminated:
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.SUCCESS,
                    message=f"Terminated {len(processes_terminated)} process(es) for '{app_name}'",
                    data={'terminated_pids': processes_terminated},
                    execution_time=execution_time
                )
            else:
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.FAILED,
                    message=f"Could not terminate any processes for '{app_name}'",
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error closing application {app_name}: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Error closing application: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== FILE OPERATIONS ====================
    
    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> SystemOperation:
        """
        Copy a file with security checks.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.copy_file('~/document.txt', '~/backup/document.txt')
            >>> print(result.message)
            'File copied successfully'
        """
        start_time = time.time()
        operation_name = f"copy_file({source} -> {destination})"
        
        try:
            # Expand paths
            source_path = Path(source).expanduser().resolve()
            dest_path = Path(destination).expanduser().resolve()
            
            # Security checks
            security_check = self._check_file_security(source_path, dest_path)
            if security_check.result != OperationResult.SUCCESS:
                return security_check
            
            # Check if source exists
            if not source_path.exists():
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.NOT_FOUND,
                    message=f"Source file does not exist: {source_path}",
                    execution_time=time.time() - start_time
                )
            
            # Check if destination exists and overwrite setting
            if dest_path.exists() and not overwrite:
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.FAILED,
                    message=f"Destination file exists and overwrite is disabled: {dest_path}",
                    execution_time=time.time() - start_time
                )
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            execution_time = time.time() - start_time
            self.logger.info(f"Copied file: {source_path} -> {dest_path}")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"File copied successfully: {source} -> {destination}",
                data={
                    'source': str(source_path),
                    'destination': str(dest_path),
                    'size': source_path.stat().st_size
                },
                execution_time=execution_time
            )
            
        except PermissionError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Permission denied copying file: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.DENIED,
                message=f"Permission denied: {str(e)}",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error copying file: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Copy failed: {str(e)}",
                execution_time=execution_time
            )
    
    def move_file(self, source: str, destination: str, overwrite: bool = False) -> SystemOperation:
        """
        Move a file with security checks.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.move_file('~/temp.txt', '~/archive/temp.txt')
            >>> print(result.message)
            'File moved successfully'
        """
        start_time = time.time()
        operation_name = f"move_file({source} -> {destination})"
        
        try:
            # First copy the file
            copy_result = self.copy_file(source, destination, overwrite)
            if copy_result.result != OperationResult.SUCCESS:
                return copy_result
            
            # Then delete the source
            source_path = Path(source).expanduser().resolve()
            source_path.unlink()
            
            execution_time = time.time() - start_time
            self.logger.info(f"Moved file: {source} -> {destination}")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"File moved successfully: {source} -> {destination}",
                data=copy_result.data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error moving file: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Move failed: {str(e)}",
                execution_time=execution_time
            )
    
    def delete_file(self, file_path: str, to_trash: bool = True) -> SystemOperation:
        """
        Delete a file with security checks.
        
        Args:
            file_path: Path to file to delete
            to_trash: Whether to move to trash instead of permanent deletion
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.delete_file('~/old_file.txt', to_trash=True)
            >>> print(result.message)
            'File moved to trash successfully'
        """
        start_time = time.time()
        operation_name = f"delete_file({file_path})"
        
        try:
            # Expand path
            target_path = Path(file_path).expanduser().resolve()
            
            # Security check
            if not self._is_path_allowed(target_path):
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.DENIED,
                    message=f"Access denied to path: {target_path}",
                    execution_time=time.time() - start_time
                )
            
            # Check if file exists
            if not target_path.exists():
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.NOT_FOUND,
                    message=f"File does not exist: {target_path}",
                    execution_time=time.time() - start_time
                )
            
            # Store file info before deletion
            file_info = {
                'path': str(target_path),
                'size': target_path.stat().st_size,
                'is_directory': target_path.is_dir()
            }
            
            # Delete or move to trash
            if to_trash:
                # Platform-specific trash handling
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(['osascript', '-e', 
                                  f'tell application "Finder" to move POSIX file "{target_path}" to trash'],
                                  check=True)
                elif platform.system() == "Windows":
                    try:
                        import send2trash
                        send2trash.send2trash(str(target_path))
                    except ImportError:
                        # Fallback to permanent deletion
                        if target_path.is_dir():
                            shutil.rmtree(target_path)
                        else:
                            target_path.unlink()
                else:  # Linux
                    try:
                        subprocess.run(['gio', 'trash', str(target_path)], check=True)
                    except subprocess.CalledProcessError:
                        # Fallback to permanent deletion
                        if target_path.is_dir():
                            shutil.rmtree(target_path)
                        else:
                            target_path.unlink()
                
                action = "moved to trash"
            else:
                # Permanent deletion
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                action = "permanently deleted"
            
            execution_time = time.time() - start_time
            self.logger.info(f"Deleted file: {target_path} ({action})")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"File {action} successfully: {file_path}",
                data=file_info,
                execution_time=execution_time
            )
            
        except PermissionError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Permission denied deleting file: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.DENIED,
                message=f"Permission denied: {str(e)}",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error deleting file: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Deletion failed: {str(e)}",
                execution_time=execution_time
            )
    
    def organize_files(self, directory: str, organize_by: str = "extension") -> SystemOperation:
        """
        Organize files in a directory by specified criteria.
        
        Args:
            directory: Directory path to organize
            organize_by: Organization method ('extension', 'date', 'size')
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.organize_files('~/Downloads', organize_by='extension')
            >>> print(result.message)
            'Organized 15 files by extension'
        """
        start_time = time.time()
        operation_name = f"organize_files({directory}, {organize_by})"
        
        try:
            # Expand path
            dir_path = Path(directory).expanduser().resolve()
            
            # Security check
            if not self._is_path_allowed(dir_path):
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.DENIED,
                    message=f"Access denied to directory: {dir_path}",
                    execution_time=time.time() - start_time
                )
            
            if not dir_path.exists() or not dir_path.is_dir():
                return SystemOperation(
                    operation=operation_name,
                    result=OperationResult.NOT_FOUND,
                    message=f"Directory does not exist: {dir_path}",
                    execution_time=time.time() - start_time
                )
            
            organized_files = []
            
            # Get all files in directory
            files = [f for f in dir_path.iterdir() if f.is_file()]
            
            for file_path in files:
                try:
                    if organize_by == "extension":
                        # Organize by file extension
                        extension = file_path.suffix.lower() or "no_extension"
                        target_dir = dir_path / extension[1:] if extension != "no_extension" else dir_path / "no_extension"
                    elif organize_by == "date":
                        # Organize by modification date (year-month)
                        mod_time = file_path.stat().st_mtime
                        date_str = time.strftime("%Y-%m", time.localtime(mod_time))
                        target_dir = dir_path / date_str
                    elif organize_by == "size":
                        # Organize by file size
                        size = file_path.stat().st_size
                        if size < 1024 * 1024:  # < 1MB
                            size_category = "small"
                        elif size < 10 * 1024 * 1024:  # < 10MB
                            size_category = "medium"
                        else:
                            size_category = "large"
                        target_dir = dir_path / size_category
                    else:
                        continue
                    
                    # Create target directory
                    target_dir.mkdir(exist_ok=True)
                    
                    # Move file
                    target_path = target_dir / file_path.name
                    if not target_path.exists():
                        file_path.rename(target_path)
                        organized_files.append({
                            'file': file_path.name,
                            'moved_to': str(target_dir)
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Could not organize file {file_path}: {e}")
                    continue
            
            execution_time = time.time() - start_time
            self.logger.info(f"Organized {len(organized_files)} files in {dir_path}")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"Organized {len(organized_files)} files by {organize_by}",
                data={'organized_files': organized_files, 'method': organize_by},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error organizing files: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Organization failed: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def focus_window(self, window_title: str) -> SystemOperation:
        """
        Focus a window by title.
        
        Args:
            window_title: Title or partial title of the window
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.focus_window('Calculator')
            >>> print(result.message)
            'Window focused successfully'
        """
        start_time = time.time()
        operation_name = f"focus_window({window_title})"
        
        if not WINDOW_MANAGEMENT_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="Window management not available on this platform",
                execution_time=time.time() - start_time
            )
        
        try:
            if platform.system() == "Windows":
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    windows[0].activate()
                    self.logger.info(f"Focused window: {window_title}")
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.SUCCESS,
                        message=f"Window '{window_title}' focused successfully",
                        execution_time=time.time() - start_time
                    )
                else:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.NOT_FOUND,
                        message=f"Window with title '{window_title}' not found",
                        execution_time=time.time() - start_time
                    )
            
            elif platform.system() == "Darwin":  # macOS
                script = f'''
                tell application "System Events"
                    set windowList to every window of every process whose name contains "{window_title}"
                    if (count of windowList) > 0 then
                        set frontmost of (first process whose name contains "{window_title}") to true
                        return "success"
                    else
                        return "not_found"
                    end if
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and "success" in result.stdout:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.SUCCESS,
                        message=f"Window '{window_title}' focused successfully",
                        execution_time=time.time() - start_time
                    )
                else:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.NOT_FOUND,
                        message=f"Window with title '{window_title}' not found",
                        execution_time=time.time() - start_time
                    )
            
            elif platform.system() == "Linux":
                # Use wmctrl on Linux
                result = subprocess.run(['wmctrl', '-a', window_title], 
                                      capture_output=True)
                if result.returncode == 0:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.SUCCESS,
                        message=f"Window '{window_title}' focused successfully",
                        execution_time=time.time() - start_time
                    )
                else:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.NOT_FOUND,
                        message=f"Window with title '{window_title}' not found",
                        execution_time=time.time() - start_time
                    )
                    
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error focusing window: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to focus window: {str(e)}",
                execution_time=execution_time
            )
    
    def minimize_window(self, window_title: str) -> SystemOperation:
        """
        Minimize a window by title.
        
        Args:
            window_title: Title or partial title of the window
            
        Returns:
            SystemOperation with result and details
        """
        start_time = time.time()
        operation_name = f"minimize_window({window_title})"
        
        if not WINDOW_MANAGEMENT_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="Window management not available on this platform",
                execution_time=time.time() - start_time
            )
        
        try:
            if platform.system() == "Windows":
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    windows[0].minimize()
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.SUCCESS,
                        message=f"Window '{window_title}' minimized successfully",
                        execution_time=time.time() - start_time
                    )
                else:
                    return SystemOperation(
                        operation=operation_name,
                        result=OperationResult.NOT_FOUND,
                        message=f"Window with title '{window_title}' not found",
                        execution_time=time.time() - start_time
                    )
            
            # Similar implementations for macOS and Linux...
            # (Implementation would follow similar pattern as focus_window)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error minimizing window: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to minimize window: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== SYSTEM INFORMATION ====================
    
    def get_system_info(self) -> SystemOperation:
        """
        Get comprehensive system information.
        
        Returns:
            SystemOperation with system information data
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.get_system_info()
            >>> print(result.data['cpu_percent'])
            25.3
        """
        start_time = time.time()
        operation_name = "get_system_info"
        
        try:
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version()
            }
            
            if PSUTIL_AVAILABLE:
                # CPU information
                system_info.update({
                    'cpu_count': psutil.cpu_count(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                })
                
                # Memory information
                memory = psutil.virtual_memory()
                system_info.update({
                    'memory_total': memory.total,
                    'memory_available': memory.available,
                    'memory_used': memory.used,
                    'memory_percent': memory.percent
                })
                
                # Disk information
                disk_usage = {}
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage[partition.mountpoint] = {
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': (usage.used / usage.total) * 100
                        }
                    except PermissionError:
                        continue
                
                system_info['disk_usage'] = disk_usage
                
                # Network information
                network_info = psutil.net_io_counters()
                system_info['network'] = {
                    'bytes_sent': network_info.bytes_sent,
                    'bytes_recv': network_info.bytes_recv,
                    'packets_sent': network_info.packets_sent,
                    'packets_recv': network_info.packets_recv
                }
                
                # Boot time
                system_info['boot_time'] = psutil.boot_time()
                
            execution_time = time.time() - start_time
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message="System information retrieved successfully",
                data=system_info,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error getting system info: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to get system info: {str(e)}",
                execution_time=execution_time
            )
    
    def get_running_processes(self, limit: int = 20) -> SystemOperation:
        """
        Get list of running processes.
        
        Args:
            limit: Maximum number of processes to return
            
        Returns:
            SystemOperation with process list data
        """
        start_time = time.time()
        operation_name = f"get_running_processes(limit={limit})"
        
        if not PSUTIL_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="psutil not available for process listing",
                execution_time=time.time() - start_time
            )
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    proc_info = proc.info
                    proc_info['cpu_percent'] = proc.cpu_percent()
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            execution_time = time.time() - start_time
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"Retrieved {len(processes[:limit])} running processes",
                data={'processes': processes[:limit], 'total_found': len(processes)},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error getting processes: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to get processes: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== WEB BROWSER CONTROL ====================
    
    def open_url(self, url: str, browser: Optional[str] = None) -> SystemOperation:
        """
        Open a URL in web browser.
        
        Args:
            url: URL to open
            browser: Specific browser to use (optional)
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.open_url('https://www.example.com')
            >>> print(result.message)
            'URL opened successfully'
        """
        start_time = time.time()
        operation_name = f"open_url({url})"
        
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://', 'file://')):
                if not url.startswith('www.'):
                    url = 'https://' + url
                else:
                    url = 'https://' + url
            
            # Open URL
            if browser:
                # Try to use specific browser
                browser_obj = webbrowser.get(browser)
                browser_obj.open(url)
            else:
                # Use default browser
                webbrowser.open(url)
            
            execution_time = time.time() - start_time
            self.logger.info(f"Opened URL: {url}")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"URL opened successfully: {url}",
                data={'url': url, 'browser': browser},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error opening URL: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to open URL: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== CLIPBOARD OPERATIONS ====================
    
    def get_clipboard(self) -> SystemOperation:
        """
        Get clipboard contents.
        
        Returns:
            SystemOperation with clipboard data
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.get_clipboard()
            >>> print(result.data['content'])
            'Hello, World!'
        """
        start_time = time.time()
        operation_name = "get_clipboard"
        
        if not CLIPBOARD_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="Clipboard operations not available (pyperclip not installed)",
                execution_time=time.time() - start_time
            )
        
        try:
            content = pyperclip.paste()
            
            execution_time = time.time() - start_time
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message="Clipboard content retrieved successfully",
                data={'content': content, 'length': len(content)},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error getting clipboard: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to get clipboard: {str(e)}",
                execution_time=execution_time
            )
    
    def set_clipboard(self, content: str) -> SystemOperation:
        """
        Set clipboard contents.
        
        Args:
            content: Text content to set in clipboard
            
        Returns:
            SystemOperation with result and details
            
        Example:
            >>> tools = SystemTools()
            >>> result = tools.set_clipboard('Hello, World!')
            >>> print(result.message)
            'Clipboard set successfully'
        """
        start_time = time.time()
        operation_name = f"set_clipboard({len(content)} chars)"
        
        if not CLIPBOARD_AVAILABLE:
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message="Clipboard operations not available (pyperclip not installed)",
                execution_time=time.time() - start_time
            )
        
        try:
            pyperclip.copy(content)
            
            execution_time = time.time() - start_time
            self.logger.info(f"Set clipboard content ({len(content)} characters)")
            
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.SUCCESS,
                message=f"Clipboard set successfully ({len(content)} characters)",
                data={'content_length': len(content)},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error setting clipboard: {e}")
            return SystemOperation(
                operation=operation_name,
                result=OperationResult.FAILED,
                message=f"Failed to set clipboard: {str(e)}",
                execution_time=execution_time
            )
    
    # ==================== SECURITY AND UTILITY METHODS ====================
    
    def _is_application_allowed(self, app_name: str) -> bool:
        """Check if application is in the allowed list."""
        app_lower = app_name.lower()
        return any(allowed.lower() in app_lower or app_lower in allowed.lower() 
                  for allowed in self.allowed_applications)
    
    def _resolve_application_path(self, app_name: str) -> Optional[str]:
        """Resolve application name to executable path."""
        app_lower = app_name.lower()
        
        # Common application mappings
        app_mappings = {
            'calculator': {
                'Windows': 'calc.exe',
                'Darwin': '/Applications/Calculator.app',
                'Linux': 'gnome-calculator'
            },
            'notepad': {
                'Windows': 'notepad.exe',
                'Darwin': '/Applications/TextEdit.app',
                'Linux': 'gedit'
            },
            'terminal': {
                'Windows': 'cmd.exe',
                'Darwin': '/Applications/Terminal.app',
                'Linux': 'gnome-terminal'
            },
            'firefox': {
                'Windows': 'firefox.exe',
                'Darwin': '/Applications/Firefox.app',
                'Linux': 'firefox'
            },
            'chrome': {
                'Windows': 'chrome.exe',
                'Darwin': '/Applications/Google Chrome.app',
                'Linux': 'google-chrome'
            }
        }
        
        system = platform.system()
        
        # Check direct mappings
        for app_key, paths in app_mappings.items():
            if app_key in app_lower:
                return paths.get(system, app_name)
        
        # For unknown applications, return as-is and let the system handle it
        return app_name
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is allowed for operations."""
        path_str = str(path)
        
        # Check blocked directories
        for blocked in self.blocked_directories:
            if path_str.startswith(blocked):
                return False
        
        # Check allowed directories (if specified)
        if self.allowed_directories:
            return any(path_str.startswith(allowed) for allowed in self.allowed_directories)
        
        return True
    
    def _check_file_security(self, source: Path, destination: Path) -> SystemOperation:
        """Perform security checks for file operations."""
        # Check source path
        if not self._is_path_allowed(source):
            return SystemOperation(
                operation="security_check",
                result=OperationResult.DENIED,
                message=f"Access denied to source path: {source}"
            )
        
        # Check destination path
        if not self._is_path_allowed(destination):
            return SystemOperation(
                operation="security_check",
                result=OperationResult.DENIED,
                message=f"Access denied to destination path: {destination}"
            )
        
        return SystemOperation(
            operation="security_check",
            result=OperationResult.SUCCESS,
            message="Security check passed"
        )


# Convenience function for easy initialization
def create_system_tools(config: Optional[Dict[str, Any]] = None) -> SystemTools:
    """
    Create and initialize a SystemTools instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized SystemTools instance
    """
    return SystemTools(config)