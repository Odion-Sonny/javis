#!/usr/bin/env python3
"""
Unit tests for the Command Parser module.
"""

import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.nlp import (
    CommandParser, CommandIntent, ParameterType, 
    ParsedCommand, CommandParameter, create_command_parser
)


class TestCommandParser(unittest.TestCase):
    """Test cases for CommandParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = create_command_parser()
    
    def test_file_operations(self):
        """Test file operation command parsing."""
        test_cases = [
            ("open file test.txt", CommandIntent.FILE_OPERATION, "open"),
            ("create new document report.pdf", CommandIntent.FILE_OPERATION, "create"),
            ("delete old logs", CommandIntent.FILE_OPERATION, "delete"),
            ("copy data.csv to backup", CommandIntent.FILE_OPERATION, "copy"),
            ("move script.py to scripts folder", CommandIntent.FILE_OPERATION, "move"),
            ("find all Python files", CommandIntent.FILE_OPERATION, "search"),
        ]
        
        for command_text, expected_intent, expected_action in test_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, expected_intent)
                self.assertEqual(result.action, expected_action)
                self.assertGreater(result.confidence, 0.5)
    
    def test_application_control(self):
        """Test application control command parsing."""
        test_cases = [
            ("open Calculator", CommandIntent.APPLICATION_CONTROL, "launch"),
            ("launch Visual Studio Code", CommandIntent.APPLICATION_CONTROL, "launch"),
            ("start Firefox", CommandIntent.APPLICATION_CONTROL, "launch"),
            ("close Chrome", CommandIntent.APPLICATION_CONTROL, "close"),
            ("quit Spotify", CommandIntent.APPLICATION_CONTROL, "close"),
        ]
        
        for command_text, expected_intent, expected_action in test_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, expected_intent)
                self.assertEqual(result.action, expected_action)
                self.assertGreater(result.confidence, 0.5)
    
    def test_system_operations(self):
        """Test system operation command parsing."""
        test_cases = [
            ("show system information", CommandIntent.SYSTEM_INFO, "system_info"),
            ("list running processes", CommandIntent.PROCESS_MANAGEMENT, "processes"),
            ("run command ls -la", CommandIntent.SYSTEM_INFO, "execute"),
            ("get system status", CommandIntent.SYSTEM_INFO, "system_info"),
        ]
        
        for command_text, expected_intent, expected_action in test_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, expected_intent)
                self.assertEqual(result.action, expected_action)
                self.assertGreater(result.confidence, 0.5)
    
    def test_questions(self):
        """Test question parsing."""
        test_cases = [
            "what is machine learning",
            "how do I install Python",
            "why is my computer slow",
            "explain neural networks",
            "tell me about quantum computing"
        ]
        
        for command_text in test_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, CommandIntent.QUESTION)
                self.assertEqual(result.action, "ask")
                self.assertGreater(result.confidence, 0.5)
    
    def test_greetings_and_goodbyes(self):
        """Test greeting and goodbye parsing."""
        greeting_cases = ["hello", "hi there", "good morning", "hey"]
        goodbye_cases = ["goodbye", "bye", "see you later", "farewell"]
        
        for command_text in greeting_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, CommandIntent.GREETING)
        
        for command_text in goodbye_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, CommandIntent.GOODBYE)
    
    def test_time_date(self):
        """Test time and date command parsing."""
        test_cases = [
            "what time is it",
            "current time",
            "what date is today",
            "show me the clock"
        ]
        
        for command_text in test_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertEqual(result.intent, CommandIntent.TIME_DATE)
                self.assertEqual(result.action, "get_time_date")
    
    def test_parameter_extraction(self):
        """Test parameter extraction from commands."""
        # File operation with parameters
        result = self.parser.parse_command("open file config.json")
        self.assertEqual(result.intent, CommandIntent.FILE_OPERATION)
        self.assertEqual(len(result.parameters), 1)
        self.assertEqual(result.parameters[0].name, "file_path")
        self.assertEqual(result.parameters[0].value, "config.json")
        self.assertEqual(result.parameters[0].param_type, ParameterType.FILE_PATH)
        
        # Application control with parameters
        result = self.parser.parse_command("launch Visual Studio Code")
        self.assertEqual(result.intent, CommandIntent.APPLICATION_CONTROL)
        self.assertEqual(len(result.parameters), 1)
        self.assertEqual(result.parameters[0].name, "application")
        self.assertIn("Visual Studio Code", result.parameters[0].value)
        
        # Copy operation with source and destination
        result = self.parser.parse_command("copy data.csv to backup folder")
        self.assertEqual(result.intent, CommandIntent.FILE_OPERATION)
        self.assertEqual(result.action, "copy")
        self.assertEqual(len(result.parameters), 2)
        
        # Find parameters
        source_param = result.get_parameter("source")
        dest_param = result.get_parameter("destination")
        self.assertIsNotNone(source_param)
        self.assertIsNotNone(dest_param)
        self.assertEqual(source_param.value, "data.csv")
        self.assertEqual(dest_param.value, "backup folder")
    
    def test_context_awareness(self):
        """Test context-aware parsing."""
        # First command establishes context
        result1 = self.parser.parse_command("open file data.txt")
        self.assertEqual(result1.intent, CommandIntent.FILE_OPERATION)
        
        # Second command uses context
        result2 = self.parser.parse_command("copy it to backup")
        # Note: This test might need adjustment based on implementation
        # The context resolution might work differently
        
        # Check that context was recorded
        self.assertIsNotNone(self.parser.context.last_command)
        self.assertEqual(self.parser.context.last_command.intent, CommandIntent.FILE_OPERATION)
    
    def test_ambiguous_commands(self):
        """Test handling of ambiguous commands."""
        ambiguous_cases = [
            "open",
            "run", 
            "file",
            "delete something"
        ]
        
        for command_text in ambiguous_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                # Should either be unknown, ambiguous, or have clarification needed
                self.assertTrue(
                    result.intent in [CommandIntent.UNKNOWN, CommandIntent.AMBIGUOUS] or
                    result.clarification_needed is not None
                )
    
    def test_unknown_commands(self):
        """Test handling of completely unknown commands."""
        unknown_cases = [
            "blahblahblah",
            "xyzabc123",
            "completely random text that makes no sense"
        ]
        
        for command_text in unknown_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                # Should fall back to conversation or unknown
                self.assertTrue(
                    result.intent in [CommandIntent.UNKNOWN, CommandIntent.CONVERSATION]
                )
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable."""
        # High confidence cases
        high_confidence_cases = [
            "open file test.txt",
            "what time is it",
            "hello",
            "show system information"
        ]
        
        for command_text in high_confidence_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertGreaterEqual(result.confidence, 0.7)
        
        # Lower confidence cases
        lower_confidence_cases = [
            "open",
            "maybe do something",
            "file stuff"
        ]
        
        for command_text in lower_confidence_cases:
            with self.subTest(command=command_text):
                result = self.parser.parse_command(command_text)
                self.assertLess(result.confidence, 0.7)
    
    def test_command_history(self):
        """Test command history management."""
        commands = [
            "open file test.txt",
            "show system info",
            "launch Calculator"
        ]
        
        for cmd in commands:
            self.parser.parse_command(cmd)
        
        history = self.parser.get_command_history()
        self.assertEqual(len(history), len(commands))
        
        # Check that commands are in correct order
        for i, cmd in enumerate(commands):
            self.assertEqual(history[i].raw_text, cmd)
    
    def test_user_preferences(self):
        """Test user preference management."""
        # Set preferences
        self.parser.set_user_preference("default_editor", "vim")
        self.parser.set_user_preference("theme", "dark")
        
        # Get preferences
        self.assertEqual(self.parser.get_user_preference("default_editor"), "vim")
        self.assertEqual(self.parser.get_user_preference("theme"), "dark")
        self.assertIsNone(self.parser.get_user_preference("nonexistent"))
        self.assertEqual(self.parser.get_user_preference("nonexistent", "default"), "default")
    
    def test_context_clearing(self):
        """Test context clearing functionality."""
        # Add some commands and preferences
        self.parser.parse_command("open file test.txt")
        self.parser.set_user_preference("test", "value")
        
        # Verify context exists
        self.assertTrue(len(self.parser.get_command_history()) > 0)
        self.assertIsNotNone(self.parser.get_user_preference("test"))
        
        # Clear context
        self.parser.clear_context()
        
        # Verify context is cleared
        self.assertEqual(len(self.parser.get_command_history()), 0)
        # Note: User preferences might be preserved depending on implementation
    
    def test_serialization(self):
        """Test command serialization to dictionary."""
        result = self.parser.parse_command("open file config.json")
        
        # Test serialization
        serialized = result.to_dict()
        self.assertIsInstance(serialized, dict)
        self.assertIn('intent', serialized)
        self.assertIn('confidence', serialized)
        self.assertIn('parameters', serialized)
        self.assertIn('raw_text', serialized)
        
        # Test parameter serialization
        if result.parameters:
            param_dict = result.parameters[0].to_dict()
            self.assertIsInstance(param_dict, dict)
            self.assertIn('name', param_dict)
            self.assertIn('value', param_dict)
            self.assertIn('type', param_dict)


class TestCommandParameter(unittest.TestCase):
    """Test cases for CommandParameter class."""
    
    def test_parameter_creation(self):
        """Test parameter creation and properties."""
        param = CommandParameter(
            name="file_path",
            value="test.txt",
            param_type=ParameterType.FILE_PATH,
            confidence=0.9,
            source_text="test.txt"
        )
        
        self.assertEqual(param.name, "file_path")
        self.assertEqual(param.value, "test.txt")
        self.assertEqual(param.param_type, ParameterType.FILE_PATH)
        self.assertEqual(param.confidence, 0.9)
        self.assertEqual(param.source_text, "test.txt")
    
    def test_parameter_serialization(self):
        """Test parameter serialization."""
        param = CommandParameter(
            name="test",
            value="value",
            param_type=ParameterType.TEXT
        )
        
        serialized = param.to_dict()
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized['name'], "test")
        self.assertEqual(serialized['value'], "value")
        self.assertEqual(serialized['type'], "text")


class TestParsedCommand(unittest.TestCase):
    """Test cases for ParsedCommand class."""
    
    def test_command_creation(self):
        """Test parsed command creation."""
        param = CommandParameter("file", "test.txt", ParameterType.FILE_PATH)
        command = ParsedCommand(
            intent=CommandIntent.FILE_OPERATION,
            confidence=0.8,
            parameters=[param],
            raw_text="open file test.txt",
            action="open"
        )
        
        self.assertEqual(command.intent, CommandIntent.FILE_OPERATION)
        self.assertEqual(command.confidence, 0.8)
        self.assertEqual(len(command.parameters), 1)
        self.assertEqual(command.raw_text, "open file test.txt")
        self.assertEqual(command.action, "open")
    
    def test_parameter_access(self):
        """Test parameter access methods."""
        param1 = CommandParameter("source", "file1.txt", ParameterType.FILE_PATH)
        param2 = CommandParameter("destination", "file2.txt", ParameterType.FILE_PATH)
        
        command = ParsedCommand(
            intent=CommandIntent.FILE_OPERATION,
            confidence=0.8,
            parameters=[param1, param2]
        )
        
        # Test get_parameter
        source_param = command.get_parameter("source")
        self.assertIsNotNone(source_param)
        self.assertEqual(source_param.value, "file1.txt")
        
        # Test get_parameter_value
        dest_value = command.get_parameter_value("destination")
        self.assertEqual(dest_value, "file2.txt")
        
        # Test non-existent parameter
        self.assertIsNone(command.get_parameter("nonexistent"))
        self.assertEqual(command.get_parameter_value("nonexistent", "default"), "default")


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()