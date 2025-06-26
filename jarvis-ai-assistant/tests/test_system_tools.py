#!/usr/bin/env python3
"""
Unit tests for the System Tools module.
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.system_tools import SystemTools, OperationResult, SecurityLevel, create_system_tools


class TestSystemTools(unittest.TestCase):
    """Test cases for SystemTools class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tools = create_system_tools({
            'security_level': 'moderate',
            'allowed_applications': ['calculator', 'notepad', 'test_app'],
            'max_execution_time': 10
        })
        
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_application_whitelist(self):
        """Test application whitelist functionality."""
        # Test allowed application
        self.assertTrue(self.tools._is_application_allowed('calculator'))
        self.assertTrue(self.tools._is_application_allowed('notepad'))
        
        # Test blocked application
        self.assertFalse(self.tools._is_application_allowed('dangerous_app'))
        self.assertFalse(self.tools._is_application_allowed('unknown_tool'))
    
    def test_launch_application_security(self):
        """Test application launch security checks."""
        # Test launching allowed application
        result = self.tools.launch_application('calculator')
        # Note: This might fail if calculator is not available, but should not be DENIED
        self.assertNotEqual(result.result, OperationResult.DENIED)
        
        # Test launching blocked application
        result = self.tools.launch_application('blocked_app')
        self.assertEqual(result.result, OperationResult.DENIED)
        self.assertIn("not in allowed list", result.message)
    
    def test_file_operations_security(self):
        """Test file operation security checks."""
        # Create tools with restricted directories
        restricted_tools = create_system_tools({
            'allowed_directories': [self.temp_dir],
            'blocked_directories': ['/etc', '/usr', '/bin']
        })
        
        # Test allowed directory operation
        dest_file = os.path.join(self.temp_dir, 'copy.txt')
        result = restricted_tools.copy_file(self.test_file, dest_file)
        self.assertEqual(result.result, OperationResult.SUCCESS)
        
        # Test blocked directory operation
        result = restricted_tools.copy_file(self.test_file, '/etc/test_copy')
        self.assertEqual(result.result, OperationResult.DENIED)
    
    def test_file_copy(self):
        """Test file copying functionality."""
        dest_file = os.path.join(self.temp_dir, 'copied.txt')
        
        # Test successful copy
        result = self.tools.copy_file(self.test_file, dest_file)
        self.assertEqual(result.result, OperationResult.SUCCESS)
        self.assertTrue(os.path.exists(dest_file))
        
        # Test copy without overwrite when file exists
        result = self.tools.copy_file(self.test_file, dest_file, overwrite=False)
        self.assertEqual(result.result, OperationResult.FAILED)
        self.assertIn("exists and overwrite is disabled", result.message)
        
        # Test copy with overwrite
        result = self.tools.copy_file(self.test_file, dest_file, overwrite=True)
        self.assertEqual(result.result, OperationResult.SUCCESS)
    
    def test_file_move(self):
        """Test file moving functionality."""
        # Create a file to move
        move_source = os.path.join(self.temp_dir, 'move_test.txt')
        with open(move_source, 'w') as f:
            f.write("Move test content")
        
        move_dest = os.path.join(self.temp_dir, 'moved.txt')
        
        # Test successful move
        result = self.tools.move_file(move_source, move_dest)
        self.assertEqual(result.result, OperationResult.SUCCESS)
        self.assertFalse(os.path.exists(move_source))
        self.assertTrue(os.path.exists(move_dest))
    
    def test_file_delete(self):
        """Test file deletion functionality."""
        # Create a file to delete
        delete_file = os.path.join(self.temp_dir, 'delete_test.txt')
        with open(delete_file, 'w') as f:
            f.write("Delete test content")
        
        # Test deletion
        result = self.tools.delete_file(delete_file, to_trash=False)
        self.assertEqual(result.result, OperationResult.SUCCESS)
        self.assertFalse(os.path.exists(delete_file))
        
        # Test deleting non-existent file
        result = self.tools.delete_file(delete_file)
        self.assertEqual(result.result, OperationResult.NOT_FOUND)
    
    def test_organize_files(self):
        """Test file organization functionality."""
        # Create test files with different extensions
        test_files = [
            ('test1.txt', 'text content'),
            ('test2.pdf', 'pdf content'),
            ('test3.txt', 'more text'),
            ('test4.jpg', 'image content')
        ]
        
        for filename, content in test_files:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write(content)
        
        # Test organization by extension
        result = self.tools.organize_files(self.temp_dir, organize_by='extension')
        self.assertEqual(result.result, OperationResult.SUCCESS)
        
        # Check that directories were created
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'txt')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'pdf')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'jpg')))
    
    def test_system_info(self):
        """Test system information gathering."""
        result = self.tools.get_system_info()
        self.assertEqual(result.result, OperationResult.SUCCESS)
        self.assertIsInstance(result.data, dict)
        
        # Check for basic system info
        self.assertIn('platform', result.data)
        self.assertIn('architecture', result.data)
        self.assertIn('hostname', result.data)
    
    def test_url_opening(self):
        """Test URL opening functionality."""
        # Test with full URL
        result = self.tools.open_url('https://www.example.com')
        self.assertEqual(result.result, OperationResult.SUCCESS)
        
        # Test with auto-protocol
        result = self.tools.open_url('example.com')
        self.assertEqual(result.result, OperationResult.SUCCESS)
        self.assertTrue(result.data['url'].startswith('https://'))
    
    def test_path_security_checks(self):
        """Test path security validation."""
        # Test with allowed paths
        allowed_path = Path(self.temp_dir) / "test.txt"
        self.assertTrue(self.tools._is_path_allowed(allowed_path))
        
        # Create tools with specific restrictions
        restricted_tools = create_system_tools({
            'blocked_directories': ['/etc', '/usr', '/bin']
        })
        
        # Test with blocked paths
        blocked_path = Path('/etc/passwd')
        self.assertFalse(restricted_tools._is_path_allowed(blocked_path))
    
    def test_operation_result_serialization(self):
        """Test SystemOperation serialization."""
        result = self.tools.get_system_info()
        
        # Test to_dict method
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn('operation', result_dict)
        self.assertIn('result', result_dict)
        self.assertIn('message', result_dict)
        self.assertIn('execution_time', result_dict)
    
    def test_security_levels(self):
        """Test different security levels."""
        # Test strict security
        strict_tools = create_system_tools({
            'security_level': 'strict',
            'allowed_applications': ['calculator']
        })
        
        self.assertEqual(strict_tools.security_level, SecurityLevel.STRICT)
        
        # Test moderate security
        moderate_tools = create_system_tools({
            'security_level': 'moderate'
        })
        
        self.assertEqual(moderate_tools.security_level, SecurityLevel.MODERATE)
    
    def test_application_path_resolution(self):
        """Test application path resolution."""
        # Test common applications
        calc_path = self.tools._resolve_application_path('calculator')
        self.assertIsNotNone(calc_path)
        
        # Test unknown application
        unknown_path = self.tools._resolve_application_path('unknown_app_12345')
        self.assertEqual(unknown_path, 'unknown_app_12345')
    
    def test_error_handling(self):
        """Test error handling in various operations."""
        # Test copying non-existent file
        result = self.tools.copy_file('/nonexistent/file.txt', '/tmp/copy.txt')
        self.assertEqual(result.result, OperationResult.NOT_FOUND)
        
        # Test moving non-existent file
        result = self.tools.move_file('/nonexistent/file.txt', '/tmp/moved.txt')
        self.assertEqual(result.result, OperationResult.NOT_FOUND)
    
    def test_execution_time_tracking(self):
        """Test that execution time is tracked."""
        result = self.tools.get_system_info()
        self.assertGreater(result.execution_time, 0)
        self.assertLess(result.execution_time, 10)  # Should be reasonably fast


class TestSystemToolsCreation(unittest.TestCase):
    """Test system tools creation and configuration."""
    
    def test_create_system_tools(self):
        """Test system tools creation with different configs."""
        # Test with default config
        tools = create_system_tools()
        self.assertIsInstance(tools, SystemTools)
        
        # Test with custom config
        config = {
            'security_level': 'strict',
            'allowed_applications': ['test_app'],
            'max_execution_time': 5
        }
        tools = create_system_tools(config)
        self.assertEqual(tools.security_level, SecurityLevel.STRICT)
        self.assertEqual(tools.max_execution_time, 5)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid security levels
        for level in ['strict', 'moderate', 'permissive']:
            tools = create_system_tools({'security_level': level})
            self.assertEqual(tools.security_level.value, level)
        
        # Test default values
        tools = create_system_tools({})
        self.assertEqual(tools.security_level, SecurityLevel.MODERATE)
        self.assertEqual(tools.max_execution_time, 30)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()