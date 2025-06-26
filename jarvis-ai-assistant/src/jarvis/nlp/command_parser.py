"""
Command Parser Module for Jarvis AI Assistant

This module analyzes user input to determine intent, extract parameters,
and map commands to appropriate system actions. It provides intelligent
parsing of natural language commands with context awareness.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime
import json


class CommandIntent(Enum):
    """Supported command intents."""
    # System operations
    SYSTEM_INFO = "system_info"
    PROCESS_MANAGEMENT = "process_management"
    FILE_OPERATION = "file_operation"
    APPLICATION_CONTROL = "application_control"
    NETWORK_OPERATION = "network_operation"
    
    # Information requests
    QUESTION = "question"
    SEARCH = "search"
    CALCULATION = "calculation"
    TIME_DATE = "time_date"
    WEATHER = "weather"
    
    # Communication
    GREETING = "greeting"
    GOODBYE = "goodbye"
    CONVERSATION = "conversation"
    
    # Jarvis control
    JARVIS_CONTROL = "jarvis_control"
    CONFIGURATION = "configuration"
    HELP = "help"
    
    # Unknown/ambiguous
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class ParameterType(Enum):
    """Types of parameters that can be extracted."""
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    APPLICATION_NAME = "application_name"
    PROCESS_NAME = "process_name"
    URL = "url"
    NUMBER = "number"
    TEXT = "text"
    BOOLEAN = "boolean"
    TIME = "time"
    DATE = "date"
    COMMAND = "command"


@dataclass
class CommandParameter:
    """Represents a parsed command parameter."""
    name: str
    value: Any
    param_type: ParameterType
    confidence: float = 1.0
    source_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.param_type.value,
            'confidence': self.confidence,
            'source_text': self.source_text
        }


@dataclass
class ParsedCommand:
    """Represents a fully parsed command."""
    intent: CommandIntent
    confidence: float
    parameters: List[CommandParameter] = field(default_factory=list)
    raw_text: str = ""
    action: Optional[str] = None
    clarification_needed: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    context_used: bool = False
    
    def get_parameter(self, name: str) -> Optional[CommandParameter]:
        """Get a parameter by name."""
        return next((p for p in self.parameters if p.name == name), None)
    
    def get_parameter_value(self, name: str, default: Any = None) -> Any:
        """Get a parameter value by name."""
        param = self.get_parameter(name)
        return param.value if param else default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'intent': self.intent.value,
            'confidence': self.confidence,
            'parameters': [p.to_dict() for p in self.parameters],
            'raw_text': self.raw_text,
            'action': self.action,
            'clarification_needed': self.clarification_needed,
            'suggestions': self.suggestions,
            'context_used': self.context_used
        }


@dataclass
class CommandContext:
    """Maintains context for command parsing."""
    last_command: Optional[ParsedCommand] = None
    last_directory: Optional[str] = None
    last_application: Optional[str] = None
    last_file: Optional[str] = None
    current_task: Optional[str] = None
    history: List[ParsedCommand] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def add_command(self, command: ParsedCommand):
        """Add a command to history and update context."""
        self.history.append(command)
        self.last_command = command
        
        # Update context based on command
        if command.intent == CommandIntent.FILE_OPERATION:
            file_param = command.get_parameter('file_path')
            if file_param:
                self.last_file = file_param.value
                # Extract directory from file path
                import os
                self.last_directory = os.path.dirname(file_param.value)
        
        elif command.intent == CommandIntent.APPLICATION_CONTROL:
            app_param = command.get_parameter('application')
            if app_param:
                self.last_application = app_param.value
        
        # Keep history limited
        if len(self.history) > 50:
            self.history = self.history[-25:]


class CommandPatterns:
    """Command pattern definitions for intent recognition."""
    
    # File operations
    FILE_OPERATIONS = {
        'open': [
            r'open\s+(?:file\s+)?(.+)',
            r'show\s+(?:me\s+)?(?:file\s+)?([^s]\w*\.?\w*)',  # Avoid "system"
            r'display\s+(?:file\s+)?(.+)',
            r'view\s+(?:file\s+)?(.+)'
        ],
        'create': [
            r'create\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?(.+)',
            r'make\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?(.+)',
            r'touch\s+(.+)'
        ],
        'delete': [
            r'delete\s+(?:file\s+)?(.+)',
            r'remove\s+(?:file\s+)?(.+)',
            r'rm\s+(.+)'
        ],
        'copy': [
            r'copy\s+(.+?)\s+to\s+(.+)',
            r'cp\s+(.+?)\s+(.+)'
        ],
        'move': [
            r'move\s+(.+?)\s+to\s+(.+)',
            r'mv\s+(.+?)\s+(.+)'
        ],
        'search': [
            r'find\s+(?:file\s+)?(.+)',
            r'search\s+for\s+(?:file\s+)?(.+)',
            r'locate\s+(.+)'
        ]
    }
    
    # Application control
    APPLICATION_OPERATIONS = {
        'launch': [
            r'(?:open|launch|start)\s+(?:application\s+)?([a-zA-Z][a-zA-Z0-9\s]+)(?:\s+app|\s+application)?$',
            r'run\s+([a-zA-Z][a-zA-Z0-9\s]+)(?:\s+app|\s+application)$'
        ],
        'close': [
            r'(?:close|quit|exit|kill)\s+([a-zA-Z][a-zA-Z0-9\s]+)(?:\s+app|\s+application)?$'
        ]
    }
    
    # System commands
    SYSTEM_OPERATIONS = {
        'execute': [
            r'run\s+command\s+(.+)',
            r'execute\s+command\s+(.+)',
            r'cmd\s+(.+)',
            r'execute\s+(.+)'
        ],
        'system_info': [
            r'(?:show\s+)?system\s+(?:info(?:rmation)?|status)',
            r'(?:get\s+)?system\s+(?:info(?:rmation)?|status)',
            r'hardware\s+(?:info(?:rmation)?)',
            r'computer\s+specs'
        ],
        'processes': [
            r'(?:show\s+)?(?:running\s+)?processes',
            r'list\s+(?:running\s+)?processes',
            r'task\s+manager',
            r'\bps\b'
        ]
    }
    
    # Questions and information
    QUESTION_PATTERNS = [
        r'what\s+is\s+(.+)',
        r'how\s+(?:do\s+i|to)\s+(.+)',
        r'why\s+(.+)',
        r'when\s+(.+)',
        r'where\s+(.+)',
        r'who\s+(.+)',
        r'explain\s+(.+)',
        r'tell\s+me\s+about\s+(.+)'
    ]
    
    # Time and date
    TIME_DATE_PATTERNS = [
        r'what\s+time\s+is\s+it',
        r'current\s+time',
        r'what\s+(?:day|date)\s+is\s+it',
        r'today\'?s\s+date',
        r'show\s+(?:me\s+)?(?:the\s+)?(?:time|date|clock)'
    ]
    
    # Greetings
    GREETING_PATTERNS = [
        r'hello',
        r'hi\b',
        r'hey',
        r'good\s+(?:morning|afternoon|evening)',
        r'greetings',
        r'howdy'
    ]
    
    # Goodbyes
    GOODBYE_PATTERNS = [
        r'goodbye',
        r'bye',
        r'see\s+you',
        r'farewell',
        r'exit',
        r'quit'
    ]


class CommandParser:
    """
    Advanced command parser for natural language input.
    
    This parser analyzes user input to determine intent, extract parameters,
    and provide structured command representation for execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the command parser."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Parser settings
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.ambiguity_threshold = self.config.get('ambiguity_threshold', 0.3)
        self.max_suggestions = self.config.get('max_suggestions', 3)
        
        # Context management
        self.context = CommandContext()
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        self.logger.info("Command parser initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = {}
        
        # Order matters - more specific patterns first
        
        # Time/Date (specific patterns first)
        self.compiled_patterns['time_date'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in CommandPatterns.TIME_DATE_PATTERNS
        ]
        
        # Greetings
        self.compiled_patterns['greetings'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in CommandPatterns.GREETING_PATTERNS
        ]
        
        # Goodbyes
        self.compiled_patterns['goodbyes'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in CommandPatterns.GOODBYE_PATTERNS
        ]
        
        # Questions (specific "what/how/why" patterns)
        self.compiled_patterns['questions'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in CommandPatterns.QUESTION_PATTERNS
        ]
        
        # System operations (before file operations to avoid conflicts)
        for operation, patterns in CommandPatterns.SYSTEM_OPERATIONS.items():
            self.compiled_patterns[f'system_{operation}'] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Application operations
        for operation, patterns in CommandPatterns.APPLICATION_OPERATIONS.items():
            self.compiled_patterns[f'app_{operation}'] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # File operations (more general patterns last)
        for operation, patterns in CommandPatterns.FILE_OPERATIONS.items():
            self.compiled_patterns[f'file_{operation}'] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def parse_command(self, text: str, use_context: bool = True) -> ParsedCommand:
        """
        Parse a command from natural language text.
        
        Args:
            text: The input text to parse
            use_context: Whether to use command history context
            
        Returns:
            ParsedCommand object with intent and parameters
        """
        try:
            text = text.strip()
            if not text:
                return self._create_unknown_command(text, "Empty input")
            
            self.logger.debug(f"Parsing command: '{text}'")
            
            # Try different parsing strategies
            candidates = []
            
            # 1. Direct pattern matching
            pattern_result = self._parse_with_patterns(text)
            if pattern_result:
                candidates.append(pattern_result)
            
            # 2. Context-aware parsing
            if use_context and self.context.last_command:
                context_result = self._parse_with_context(text)
                if context_result:
                    candidates.append(context_result)
            
            # 3. Keyword-based parsing
            keyword_result = self._parse_with_keywords(text)
            if keyword_result:
                candidates.append(keyword_result)
            
            # 4. Fallback to conversation
            if not candidates:
                candidates.append(self._create_conversation_command(text))
            
            # Select best candidate
            best_command = self._select_best_candidate(candidates, text)
            
            # Add to context
            if best_command.confidence >= self.confidence_threshold:
                self.context.add_command(best_command)
            
            return best_command
            
        except Exception as e:
            self.logger.error(f"Error parsing command '{text}': {e}")
            return self._create_unknown_command(text, f"Parsing error: {str(e)}")
    
    def _parse_with_patterns(self, text: str) -> Optional[ParsedCommand]:
        """Parse using compiled regex patterns."""
        matches = []
        
        for pattern_type, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                match = pattern.search(text)
                if match:
                    confidence = self._calculate_pattern_confidence(match, text)
                    matches.append((pattern_type, match, confidence))
        
        if not matches:
            return None
        
        # Sort by confidence and take the best match
        matches.sort(key=lambda x: x[2], reverse=True)
        pattern_type, match, confidence = matches[0]
        
        return self._create_command_from_pattern(pattern_type, match, text, confidence)
    
    def _parse_with_context(self, text: str) -> Optional[ParsedCommand]:
        """Parse using command history context."""
        if not self.context.last_command:
            return None
        
        last_cmd = self.context.last_command
        
        # Handle follow-up commands
        followup_patterns = {
            'it': ['open it', 'delete it', 'copy it', 'move it'],
            'that': ['open that', 'delete that', 'show that'],
            'same': ['same directory', 'same folder', 'same file'],
            'there': ['go there', 'list there', 'open there']
        }
        
        text_lower = text.lower()
        
        for pronoun, patterns in followup_patterns.items():
            if pronoun in text_lower:
                # Try to resolve pronoun based on last command
                resolved_command = self._resolve_pronoun_reference(text, last_cmd)
                if resolved_command:
                    resolved_command.context_used = True
                    return resolved_command
        
        # Handle relative commands (open another file, etc.)
        if any(word in text_lower for word in ['another', 'different', 'other']):
            return self._handle_relative_command(text, last_cmd)
        
        return None
    
    def _parse_with_keywords(self, text: str) -> Optional[ParsedCommand]:
        """Parse using keyword analysis."""
        text_lower = text.lower()
        words = text_lower.split()
        
        # File operation keywords
        file_keywords = {
            'open': ['open', 'show', 'display', 'view'],
            'create': ['create', 'make', 'new', 'touch'],
            'delete': ['delete', 'remove', 'rm'],
            'copy': ['copy', 'cp', 'duplicate'],
            'move': ['move', 'mv', 'relocate'],
            'search': ['find', 'search', 'locate', 'look']
        }
        
        # System keywords
        system_keywords = {
            'system_info': ['system', 'info', 'specs', 'hardware'],
            'processes': ['processes', 'tasks', 'running'],
            'execute': ['run', 'execute', 'command']
        }
        
        # Application keywords
        app_keywords = {
            'launch': ['open', 'launch', 'start', 'run'],
            'close': ['close', 'quit', 'exit', 'kill']
        }
        
        # Check for file operations
        for operation, keywords in file_keywords.items():
            if any(keyword in words for keyword in keywords):
                return self._create_file_operation_command(text, operation)
        
        # Check for system operations
        for operation, keywords in system_keywords.items():
            if any(keyword in words for keyword in keywords):
                return self._create_system_command(text, operation)
        
        # Check for application operations
        for operation, keywords in app_keywords.items():
            if any(keyword in words for keyword in keywords):
                return self._create_app_command(text, operation)
        
        return None
    
    def _create_command_from_pattern(
        self, 
        pattern_type: str, 
        match: re.Match, 
        text: str, 
        confidence: float
    ) -> ParsedCommand:
        """Create a command from a pattern match."""
        
        if pattern_type.startswith('file_'):
            operation = pattern_type[5:]  # Remove 'file_' prefix
            return self._create_file_command_from_match(operation, match, text, confidence)
        
        elif pattern_type.startswith('app_'):
            operation = pattern_type[4:]  # Remove 'app_' prefix
            return self._create_app_command_from_match(operation, match, text, confidence)
        
        elif pattern_type.startswith('system_'):
            operation = pattern_type[7:]  # Remove 'system_' prefix
            return self._create_system_command_from_match(operation, match, text, confidence)
        
        elif pattern_type == 'questions':
            return self._create_question_command(match, text, confidence)
        
        elif pattern_type == 'time_date':
            return self._create_time_date_command(text, confidence)
        
        elif pattern_type == 'greetings':
            return self._create_greeting_command(text, confidence)
        
        elif pattern_type == 'goodbyes':
            return self._create_goodbye_command(text, confidence)
        
        else:
            return self._create_unknown_command(text, f"Unknown pattern type: {pattern_type}")
    
    def _create_file_command_from_match(
        self, 
        operation: str, 
        match: re.Match, 
        text: str, 
        confidence: float
    ) -> ParsedCommand:
        """Create a file operation command from regex match."""
        parameters = []
        
        if operation in ['copy', 'move'] and len(match.groups()) >= 2:
            # Two parameters: source and destination
            source = match.group(1).strip()
            dest = match.group(2).strip()
            
            parameters.extend([
                CommandParameter('source', source, ParameterType.FILE_PATH, confidence, source),
                CommandParameter('destination', dest, ParameterType.FILE_PATH, confidence, dest)
            ])
        
        elif len(match.groups()) >= 1:
            # Single file parameter
            file_path = match.group(1).strip()
            parameters.append(
                CommandParameter('file_path', file_path, ParameterType.FILE_PATH, confidence, file_path)
            )
        
        return ParsedCommand(
            intent=CommandIntent.FILE_OPERATION,
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action=operation
        )
    
    def _create_app_command_from_match(
        self, 
        operation: str, 
        match: re.Match, 
        text: str, 
        confidence: float
    ) -> ParsedCommand:
        """Create an application command from regex match."""
        parameters = []
        
        if len(match.groups()) >= 1:
            app_name = match.group(1).strip()
            parameters.append(
                CommandParameter('application', app_name, ParameterType.APPLICATION_NAME, confidence, app_name)
            )
        
        return ParsedCommand(
            intent=CommandIntent.APPLICATION_CONTROL,
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action=operation
        )
    
    def _create_system_command_from_match(
        self, 
        operation: str, 
        match: re.Match, 
        text: str, 
        confidence: float
    ) -> ParsedCommand:
        """Create a system command from regex match."""
        parameters = []
        
        if operation == 'execute' and len(match.groups()) >= 1:
            command = match.group(1).strip()
            parameters.append(
                CommandParameter('command', command, ParameterType.COMMAND, confidence, command)
            )
        
        intent_map = {
            'execute': CommandIntent.SYSTEM_INFO,
            'system_info': CommandIntent.SYSTEM_INFO,
            'processes': CommandIntent.PROCESS_MANAGEMENT
        }
        
        return ParsedCommand(
            intent=intent_map.get(operation, CommandIntent.SYSTEM_INFO),
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action=operation
        )
    
    def _create_question_command(self, match: re.Match, text: str, confidence: float) -> ParsedCommand:
        """Create a question command."""
        parameters = []
        
        if len(match.groups()) >= 1:
            question_subject = match.group(1).strip()
            parameters.append(
                CommandParameter('subject', question_subject, ParameterType.TEXT, confidence, question_subject)
            )
        
        return ParsedCommand(
            intent=CommandIntent.QUESTION,
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action='ask'
        )
    
    def _create_time_date_command(self, text: str, confidence: float) -> ParsedCommand:
        """Create a time/date command."""
        return ParsedCommand(
            intent=CommandIntent.TIME_DATE,
            confidence=confidence,
            parameters=[],
            raw_text=text,
            action='get_time_date'
        )
    
    def _create_greeting_command(self, text: str, confidence: float) -> ParsedCommand:
        """Create a greeting command."""
        return ParsedCommand(
            intent=CommandIntent.GREETING,
            confidence=confidence,
            parameters=[],
            raw_text=text,
            action='greet'
        )
    
    def _create_goodbye_command(self, text: str, confidence: float) -> ParsedCommand:
        """Create a goodbye command."""
        return ParsedCommand(
            intent=CommandIntent.GOODBYE,
            confidence=confidence,
            parameters=[],
            raw_text=text,
            action='goodbye'
        )
    
    def _create_conversation_command(self, text: str) -> ParsedCommand:
        """Create a general conversation command."""
        return ParsedCommand(
            intent=CommandIntent.CONVERSATION,
            confidence=0.5,
            parameters=[
                CommandParameter('message', text, ParameterType.TEXT, 1.0, text)
            ],
            raw_text=text,
            action='chat'
        )
    
    def _create_unknown_command(self, text: str, reason: str) -> ParsedCommand:
        """Create an unknown command with suggestions."""
        suggestions = self._generate_suggestions(text)
        
        return ParsedCommand(
            intent=CommandIntent.UNKNOWN,
            confidence=0.0,
            parameters=[],
            raw_text=text,
            clarification_needed=f"I didn't understand: {reason}",
            suggestions=suggestions
        )
    
    def _calculate_pattern_confidence(self, match: re.Match, text: str) -> float:
        """Calculate confidence score for a pattern match."""
        # Base confidence from match quality
        match_length = len(match.group(0))
        text_length = len(text)
        coverage = match_length / text_length
        
        # Adjust based on exact vs partial matches
        if match_length == text_length:
            return min(0.95, 0.7 + coverage * 0.25)
        else:
            return min(0.85, 0.5 + coverage * 0.35)
    
    def _select_best_candidate(self, candidates: List[ParsedCommand], text: str) -> ParsedCommand:
        """Select the best command candidate."""
        if not candidates:
            return self._create_unknown_command(text, "No candidates found")
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Remove duplicates based on intent and action
        unique_candidates = []
        seen = set()
        for candidate in candidates:
            key = (candidate.intent, candidate.action)
            if key not in seen:
                unique_candidates.append(candidate)
                seen.add(key)
        
        # Sort by confidence
        unique_candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        if len(unique_candidates) == 1:
            return unique_candidates[0]
        
        best = unique_candidates[0]
        second_best = unique_candidates[1] if len(unique_candidates) > 1 else None
        
        # Check for ambiguity only if there are genuinely different commands
        if (second_best and 
            best.confidence - second_best.confidence < self.ambiguity_threshold and
            best.intent != second_best.intent):
            return self._create_ambiguous_command(text, unique_candidates[:self.max_suggestions])
        
        return best
    
    def _create_ambiguous_command(self, text: str, candidates: List[ParsedCommand]) -> ParsedCommand:
        """Create an ambiguous command that needs clarification."""
        suggestions = []
        for i, candidate in enumerate(candidates[:self.max_suggestions]):
            suggestion = f"{i+1}. {candidate.intent.value}"
            if candidate.action:
                suggestion += f" ({candidate.action})"
            suggestions.append(suggestion)
        
        return ParsedCommand(
            intent=CommandIntent.AMBIGUOUS,
            confidence=0.0,
            parameters=[],
            raw_text=text,
            clarification_needed="Your command could mean several things. Did you mean:",
            suggestions=suggestions
        )
    
    def _generate_suggestions(self, text: str) -> List[str]:
        """Generate helpful suggestions for unknown commands."""
        suggestions = []
        text_lower = text.lower()
        
        # Common suggestions based on keywords
        if any(word in text_lower for word in ['file', 'document', 'folder']):
            suggestions.extend([
                "open file <filename>",
                "create file <filename>",
                "search for <filename>"
            ])
        
        elif any(word in text_lower for word in ['app', 'program', 'application']):
            suggestions.extend([
                "open <application_name>",
                "close <application_name>"
            ])
        
        elif any(word in text_lower for word in ['system', 'computer', 'info']):
            suggestions.extend([
                "show system info",
                "list processes"
            ])
        
        else:
            suggestions.extend([
                "Try: 'open file <name>' to open a file",
                "Try: 'what is <topic>' to ask a question",
                "Try: 'help' to see available commands"
            ])
        
        return suggestions[:self.max_suggestions]
    
    def _resolve_pronoun_reference(self, text: str, last_command: ParsedCommand) -> Optional[ParsedCommand]:
        """Resolve pronoun references using context."""
        # This is a simplified implementation
        # In a real system, this would be more sophisticated
        
        if last_command.intent == CommandIntent.FILE_OPERATION:
            last_file = last_command.get_parameter_value('file_path')
            if last_file:
                # Replace pronouns with actual file reference
                resolved_text = text.replace('it', last_file).replace('that', last_file)
                return self.parse_command(resolved_text, use_context=False)
        
        return None
    
    def _handle_relative_command(self, text: str, last_command: ParsedCommand) -> Optional[ParsedCommand]:
        """Handle relative commands based on context."""
        # Simplified implementation
        if 'another' in text.lower() and last_command.intent == CommandIntent.FILE_OPERATION:
            # User wants to perform similar operation on another file
            return ParsedCommand(
                intent=CommandIntent.FILE_OPERATION,
                confidence=0.7,
                parameters=[],
                raw_text=text,
                clarification_needed="Which file would you like to work with?",
                suggestions=["Please specify the filename"]
            )
        
        return None
    
    def _create_file_operation_command(self, text: str, operation: str) -> ParsedCommand:
        """Create a file operation command from keywords."""
        # Extract potential file names from text
        words = text.split()
        potential_files = []
        
        for word in words:
            if '.' in word or '/' in word or '\\' in word:
                potential_files.append(word)
        
        parameters = []
        if potential_files:
            parameters.append(
                CommandParameter('file_path', potential_files[0], ParameterType.FILE_PATH, 0.7, potential_files[0])
            )
        
        confidence = 0.8 if parameters else 0.4
        
        return ParsedCommand(
            intent=CommandIntent.FILE_OPERATION,
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action=operation,
            clarification_needed=None if parameters else "Which file would you like to work with?"
        )
    
    def _create_system_command(self, text: str, operation: str) -> ParsedCommand:
        """Create a system command from keywords."""
        intent_map = {
            'system_info': CommandIntent.SYSTEM_INFO,
            'processes': CommandIntent.PROCESS_MANAGEMENT,
            'execute': CommandIntent.SYSTEM_INFO
        }
        
        return ParsedCommand(
            intent=intent_map.get(operation, CommandIntent.SYSTEM_INFO),
            confidence=0.7,
            parameters=[],
            raw_text=text,
            action=operation
        )
    
    def _create_app_command(self, text: str, operation: str) -> ParsedCommand:
        """Create an application command from keywords."""
        # Try to extract application name
        words = text.split()
        app_keywords = ['open', 'launch', 'start', 'run', 'close', 'quit', 'exit', 'kill']
        
        app_name = None
        for i, word in enumerate(words):
            if word.lower() in app_keywords and i + 1 < len(words):
                app_name = words[i + 1]
                break
        
        parameters = []
        if app_name:
            parameters.append(
                CommandParameter('application', app_name, ParameterType.APPLICATION_NAME, 0.7, app_name)
            )
        
        confidence = 0.8 if parameters else 0.4
        
        return ParsedCommand(
            intent=CommandIntent.APPLICATION_CONTROL,
            confidence=confidence,
            parameters=parameters,
            raw_text=text,
            action=operation,
            clarification_needed=None if parameters else "Which application would you like to work with?"
        )
    
    def get_command_history(self, limit: int = 10) -> List[ParsedCommand]:
        """Get recent command history."""
        return self.context.history[-limit:] if self.context.history else []
    
    def clear_context(self):
        """Clear command context and history."""
        self.context = CommandContext()
        self.logger.info("Command parser context cleared")
    
    def set_user_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.context.user_preferences[key] = value
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.context.user_preferences.get(key, default)


# Example usage and testing
def create_command_parser(config: Optional[Dict[str, Any]] = None) -> CommandParser:
    """Create and initialize a command parser."""
    return CommandParser(config)


# Example command patterns for testing
EXAMPLE_COMMANDS = {
    "File Operations": [
        "open file config.json",
        "create a new file called test.txt",
        "delete the log file",
        "copy data.csv to backup folder",
        "move script.py to scripts directory",
        "find all Python files",
        "search for *.txt files"
    ],
    
    "Application Control": [
        "open calculator",
        "launch Visual Studio Code",
        "start Firefox",
        "close Chrome",
        "quit Spotify",
        "kill that process"
    ],
    
    "System Operations": [
        "show system information",
        "list running processes",
        "run command ls -la",
        "execute top",
        "get system status"
    ],
    
    "Questions": [
        "what is machine learning",
        "how do I install Python",
        "why is my computer slow",
        "when was Python created",
        "explain neural networks"
    ],
    
    "Time and Date": [
        "what time is it",
        "show me the current date",
        "what day is today"
    ],
    
    "Context-Aware": [
        "open it",  # Refers to last mentioned file
        "delete that",  # Refers to previous context
        "open another file",  # Relative to last operation
        "do the same thing"  # Repeat last action
    ],
    
    "Ambiguous": [
        "open",  # Missing target
        "run",  # Missing what to run
        "file"  # Just mentions file without action
    ]
}