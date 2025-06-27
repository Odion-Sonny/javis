"""
Memory System Module for Jarvis AI Assistant

Provides comprehensive memory management including:
- Conversation history storage and retrieval
- User preferences and settings learning
- Task history and patterns
- Context-aware responses based on past interactions
- SQLite database operations for local storage
- Interaction pattern analysis

Handles long-term memory, user learning, and contextual understanding.
"""

import logging
import sqlite3
import json
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import re


class InteractionType(Enum):
    """Types of user interactions."""
    CONVERSATION = "conversation"
    TASK_REQUEST = "task_request"
    QUESTION = "question"
    COMMAND = "command"
    FEEDBACK = "feedback"
    PREFERENCE_SETTING = "preference_setting"


class TaskStatus(Enum):
    """Task execution status."""
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PreferenceCategory(Enum):
    """Categories of user preferences."""
    VOICE = "voice"
    INTERFACE = "interface"
    BEHAVIOR = "behavior"
    SYSTEM = "system"
    PRIVACY = "privacy"
    AUTOMATION = "automation"


@dataclass
class ConversationEntry:
    """Represents a single conversation entry."""
    id: Optional[int] = None
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    user_input: str = ""
    assistant_response: str = ""
    interaction_type: InteractionType = InteractionType.CONVERSATION
    context_summary: str = ""
    sentiment_score: float = 0.0
    confidence_score: float = 0.0
    tokens_used: int = 0
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRecord:
    """Represents a task execution record."""
    id: Optional[int] = None
    task_id: str = ""
    user_request: str = ""
    task_type: str = ""
    status: TaskStatus = TaskStatus.REQUESTED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    user_feedback: Optional[str] = None
    feedback_score: Optional[int] = None  # 1-5 rating


@dataclass
class UserPreference:
    """Represents a user preference or learned behavior."""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    category: PreferenceCategory = PreferenceCategory.BEHAVIOR
    confidence: float = 0.0
    learn_count: int = 1
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionPattern:
    """Represents patterns in user interactions."""
    pattern_id: str = ""
    pattern_type: str = ""
    frequency: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_occurrence: datetime = field(default_factory=datetime.now)
    context_clues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Represents a context window for conversation understanding."""
    entries: List[ConversationEntry] = field(default_factory=list)
    summary: str = ""
    topics: List[str] = field(default_factory=list)
    sentiment_trend: List[float] = field(default_factory=list)
    total_tokens: int = 0


class MemorySystem:
    """
    Comprehensive memory system for Jarvis AI Assistant.
    
    Manages conversation history, user preferences, task patterns,
    and provides context-aware responses based on past interactions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize memory system with configuration.
        
        Args:
            config: Configuration dictionary with memory settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration settings
        self.db_path = Path(self.config.get('db_path', 'data/jarvis_memory.db'))
        self.max_context_entries = self.config.get('max_context_entries', 50)
        self.max_context_tokens = self.config.get('max_context_tokens', 4000)
        self.context_window_hours = self.config.get('context_window_hours', 24)
        self.pattern_learning_threshold = self.config.get('pattern_learning_threshold', 3)
        self.preference_confidence_threshold = self.config.get('preference_confidence_threshold', 0.7)
        
        # Session management
        self.session_id = self._generate_session_id()
        self.current_context = ContextWindow()
        
        # Threading for async operations
        self.db_lock = threading.Lock()
        
        # Initialize database
        self._ensure_data_directory()
        self._initialize_database()
        
        # Load recent context
        self._load_recent_context()
        
        self.logger.info(f"Memory system initialized with session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}"
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize SQLite database with all necessary tables."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Conversations table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        assistant_response TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        context_summary TEXT,
                        sentiment_score REAL DEFAULT 0.0,
                        confidence_score REAL DEFAULT 0.0,
                        tokens_used INTEGER DEFAULT 0,
                        response_time REAL DEFAULT 0.0,
                        metadata TEXT
                    )
                """)
                
                # Tasks table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT UNIQUE NOT NULL,
                        user_request TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        duration REAL,
                        success BOOLEAN DEFAULT 0,
                        error_message TEXT,
                        result_data TEXT,
                        user_feedback TEXT,
                        feedback_score INTEGER
                    )
                """)
                
                # User preferences table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        category TEXT NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        learn_count INTEGER DEFAULT 1,
                        last_used TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        context TEXT,
                        metadata TEXT,
                        UNIQUE(key, category)
                    )
                """)
                
                # Interaction patterns table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS interaction_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_id TEXT UNIQUE NOT NULL,
                        pattern_type TEXT NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        success_rate REAL DEFAULT 0.0,
                        avg_response_time REAL DEFAULT 0.0,
                        last_occurrence TEXT NOT NULL,
                        context_clues TEXT,
                        metadata TEXT
                    )
                """)
                
                # Context summaries table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS context_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        summary_text TEXT NOT NULL,
                        topics TEXT,
                        created_at TEXT NOT NULL,
                        entry_count INTEGER DEFAULT 0,
                        token_count INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_conversation(
        self,
        user_input: str,
        assistant_response: str,
        interaction_type: InteractionType = InteractionType.CONVERSATION,
        context_summary: str = "",
        sentiment_score: float = 0.0,
        confidence_score: float = 0.0,
        tokens_used: int = 0,
        response_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a conversation entry.
        
        Args:
            user_input: User's input text
            assistant_response: Assistant's response
            interaction_type: Type of interaction
            context_summary: Summary of conversation context
            sentiment_score: Sentiment analysis score (-1 to 1)
            confidence_score: Confidence in response (0 to 1)
            tokens_used: Number of tokens used
            response_time: Response time in seconds
            metadata: Additional metadata
            
        Returns:
            ID of stored conversation entry
        """
        entry = ConversationEntry(
            session_id=self.session_id,
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type=interaction_type,
            context_summary=context_summary,
            sentiment_score=sentiment_score,
            confidence_score=confidence_score,
            tokens_used=tokens_used,
            response_time=response_time,
            metadata=metadata or {}
        )
        
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO conversations (
                            session_id, timestamp, user_input, assistant_response,
                            interaction_type, context_summary, sentiment_score,
                            confidence_score, tokens_used, response_time, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.session_id,
                        entry.timestamp.isoformat(),
                        entry.user_input,
                        entry.assistant_response,
                        entry.interaction_type.value,
                        entry.context_summary,
                        entry.sentiment_score,
                        entry.confidence_score,
                        entry.tokens_used,
                        entry.response_time,
                        json.dumps(entry.metadata)
                    ))
                    
                    entry.id = cursor.lastrowid
                    conn.commit()
                    
                    # Add to current context
                    self.current_context.entries.append(entry)
                    self.current_context.total_tokens += tokens_used
                    self.current_context.sentiment_trend.append(sentiment_score)
                    
                    # Maintain context window size
                    self._maintain_context_window()
                    
                    # Learn from interaction
                    self._learn_from_interaction(entry)
                    
                    self.logger.debug(f"Stored conversation entry: {entry.id}")
                    return entry.id
                    
            except Exception as e:
                self.logger.error(f"Failed to store conversation: {e}")
                return -1
    
    def store_task_record(
        self,
        task_id: str,
        user_request: str,
        task_type: str,
        status: TaskStatus = TaskStatus.REQUESTED,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        success: bool = False,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
        user_feedback: Optional[str] = None,
        feedback_score: Optional[int] = None
    ) -> int:
        """
        Store a task execution record.
        
        Args:
            task_id: Unique task identifier
            user_request: Original user request
            task_type: Type of task
            status: Current task status
            started_at: Task start time
            completed_at: Task completion time
            success: Whether task succeeded
            error_message: Error message if failed
            result_data: Task result data
            user_feedback: User feedback text
            feedback_score: User rating (1-5)
            
        Returns:
            ID of stored task record
        """
        task = TaskRecord(
            task_id=task_id,
            user_request=user_request,
            task_type=task_type,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            success=success,
            error_message=error_message,
            result_data=result_data or {},
            user_feedback=user_feedback,
            feedback_score=feedback_score
        )
        
        # Calculate duration if both times are available
        if started_at and completed_at:
            task.duration = (completed_at - started_at).total_seconds()
        
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO tasks (
                            task_id, user_request, task_type, status, created_at,
                            started_at, completed_at, duration, success, error_message,
                            result_data, user_feedback, feedback_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task.task_id,
                        task.user_request,
                        task.task_type,
                        task.status.value,
                        task.created_at.isoformat(),
                        task.started_at.isoformat() if task.started_at else None,
                        task.completed_at.isoformat() if task.completed_at else None,
                        task.duration,
                        task.success,
                        task.error_message,
                        json.dumps(task.result_data),
                        task.user_feedback,
                        task.feedback_score
                    ))
                    
                    task.id = cursor.lastrowid
                    conn.commit()
                    
                    # Learn task patterns
                    self._learn_task_patterns(task)
                    
                    self.logger.debug(f"Stored task record: {task.task_id}")
                    return task.id
                    
            except Exception as e:
                self.logger.error(f"Failed to store task record: {e}")
                return -1
    
    def learn_user_preference(
        self,
        key: str,
        value: str,
        category: PreferenceCategory = PreferenceCategory.BEHAVIOR,
        confidence: float = 0.8,
        context: str = ""
    ) -> bool:
        """
        Learn and store a user preference.
        
        Args:
            key: Preference key
            value: Preference value
            category: Preference category
            confidence: Confidence score (0-1)
            context: Context in which preference was observed
            
        Returns:
            True if preference was stored successfully
        """
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Check if preference already exists
                    cursor.execute("""
                        SELECT id, learn_count, confidence FROM user_preferences
                        WHERE key = ? AND category = ?
                    """, (key, category.value))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing preference
                        new_learn_count = existing[1] + 1
                        new_confidence = min(1.0, (existing[2] + confidence) / 2)
                        
                        cursor.execute("""
                            UPDATE user_preferences
                            SET value = ?, confidence = ?, learn_count = ?,
                                last_used = ?, context = ?
                            WHERE id = ?
                        """, (
                            value,
                            new_confidence,
                            new_learn_count,
                            datetime.now().isoformat(),
                            context,
                            existing[0]
                        ))
                    else:
                        # Create new preference
                        cursor.execute("""
                            INSERT INTO user_preferences (
                                key, value, category, confidence, learn_count,
                                last_used, created_at, context, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            key,
                            value,
                            category.value,
                            confidence,
                            1,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                            context,
                            json.dumps({})
                        ))
                    
                    conn.commit()
                    self.logger.debug(f"Learned user preference: {key} = {value}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Failed to learn user preference: {e}")
                return False
    
    def get_user_preference(
        self,
        key: str,
        category: Optional[PreferenceCategory] = None,
        min_confidence: float = 0.5
    ) -> Optional[str]:
        """
        Get a user preference value.
        
        Args:
            key: Preference key
            category: Preference category (if None, searches all)
            min_confidence: Minimum confidence threshold
            
        Returns:
            Preference value if found and meets confidence threshold
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute("""
                        SELECT value, confidence FROM user_preferences
                        WHERE key = ? AND category = ? AND confidence >= ?
                        ORDER BY confidence DESC, last_used DESC
                        LIMIT 1
                    """, (key, category.value, min_confidence))
                else:
                    cursor.execute("""
                        SELECT value, confidence FROM user_preferences
                        WHERE key = ? AND confidence >= ?
                        ORDER BY confidence DESC, last_used DESC
                        LIMIT 1
                    """, (key, min_confidence))
                
                result = cursor.fetchone()
                if result:
                    # Update last_used timestamp
                    cursor.execute("""
                        UPDATE user_preferences
                        SET last_used = ?
                        WHERE key = ? AND value = ?
                    """, (datetime.now().isoformat(), key, result[0]))
                    conn.commit()
                    
                    return result[0]
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get user preference: {e}")
            return None
    
    def get_conversation_context(
        self,
        max_entries: Optional[int] = None,
        max_tokens: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for AI model.
        
        Args:
            max_entries: Maximum number of entries to return
            max_tokens: Maximum tokens to include
            include_metadata: Whether to include metadata
            
        Returns:
            List of conversation entries formatted for AI model
        """
        max_entries = max_entries or self.max_context_entries
        max_tokens = max_tokens or self.max_context_tokens
        
        context = []
        total_tokens = 0
        
        # Use current context window
        for entry in reversed(self.current_context.entries):
            if len(context) >= max_entries:
                break
            
            entry_tokens = entry.tokens_used
            if total_tokens + entry_tokens > max_tokens:
                break
            
            context_entry = {
                "role": "user",
                "content": entry.user_input,
                "timestamp": entry.timestamp.isoformat()
            }
            
            if include_metadata:
                context_entry["metadata"] = entry.metadata
                context_entry["sentiment"] = entry.sentiment_score
                context_entry["confidence"] = entry.confidence_score
            
            context.insert(0, context_entry)
            
            # Add assistant response
            if entry.assistant_response:
                assistant_entry = {
                    "role": "assistant",
                    "content": entry.assistant_response,
                    "timestamp": entry.timestamp.isoformat()
                }
                context.insert(-1, assistant_entry)
            
            total_tokens += entry_tokens
        
        return context
    
    def analyze_interaction_patterns(
        self,
        days_back: int = 30,
        pattern_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze user interaction patterns.
        
        Args:
            days_back: Number of days to analyze
            pattern_types: Specific pattern types to analyze
            
        Returns:
            Dictionary with pattern analysis results
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Get conversation patterns
                cursor.execute("""
                    SELECT interaction_type, COUNT(*) as count,
                           AVG(sentiment_score) as avg_sentiment,
                           AVG(confidence_score) as avg_confidence,
                           AVG(response_time) as avg_response_time
                    FROM conversations
                    WHERE timestamp > ?
                    GROUP BY interaction_type
                """, (cutoff_date.isoformat(),))
                
                conversation_patterns = {}
                for row in cursor.fetchall():
                    conversation_patterns[row[0]] = {
                        'count': row[1],
                        'avg_sentiment': row[2],
                        'avg_confidence': row[3],
                        'avg_response_time': row[4]
                    }
                
                # Get task patterns
                cursor.execute("""
                    SELECT task_type, COUNT(*) as count,
                           AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                           AVG(duration) as avg_duration,
                           AVG(feedback_score) as avg_feedback
                    FROM tasks
                    WHERE created_at > ?
                    GROUP BY task_type
                """, (cutoff_date.isoformat(),))
                
                task_patterns = {}
                for row in cursor.fetchall():
                    task_patterns[row[0]] = {
                        'count': row[1],
                        'success_rate': row[2],
                        'avg_duration': row[3],
                        'avg_feedback': row[4]
                    }
                
                # Get time patterns
                cursor.execute("""
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM conversations
                    WHERE timestamp > ?
                    GROUP BY hour
                    ORDER BY hour
                """, (cutoff_date.isoformat(),))
                
                time_patterns = {f"{row[0]}:00": row[1] for row in cursor.fetchall()}
                
                # Get preference trends
                cursor.execute("""
                    SELECT category, COUNT(*) as count,
                           AVG(confidence) as avg_confidence
                    FROM user_preferences
                    WHERE created_at > ?
                    GROUP BY category
                """, (cutoff_date.isoformat(),))
                
                preference_patterns = {}
                for row in cursor.fetchall():
                    preference_patterns[row[0]] = {
                        'count': row[1],
                        'avg_confidence': row[2]
                    }
                
                return {
                    'analysis_period': f"{days_back} days",
                    'conversation_patterns': conversation_patterns,
                    'task_patterns': task_patterns,
                    'time_patterns': time_patterns,
                    'preference_patterns': preference_patterns,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to analyze interaction patterns: {e}")
            return {}
    
    def get_contextual_suggestions(
        self,
        current_input: str,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get contextual suggestions based on past interactions.
        
        Args:
            current_input: Current user input
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of contextual suggestions
        """
        suggestions = []
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Find similar past interactions
                cursor.execute("""
                    SELECT user_input, assistant_response, confidence_score
                    FROM conversations
                    WHERE user_input LIKE ?
                    ORDER BY confidence_score DESC, timestamp DESC
                    LIMIT ?
                """, (f"%{current_input[:50]}%", max_suggestions))
                
                for row in cursor.fetchall():
                    suggestions.append({
                        'type': 'similar_interaction',
                        'user_input': row[0],
                        'response': row[1],
                        'confidence': row[2],
                        'relevance_score': self._calculate_text_similarity(
                            current_input, row[0]
                        )
                    })
                
                # Find relevant preferences
                cursor.execute("""
                    SELECT key, value, confidence FROM user_preferences
                    WHERE confidence > 0.7
                    ORDER BY confidence DESC, last_used DESC
                    LIMIT 3
                """, ())
                
                for row in cursor.fetchall():
                    if any(word in current_input.lower() 
                           for word in row[0].lower().split()):
                        suggestions.append({
                            'type': 'preference',
                            'key': row[0],
                            'value': row[1],
                            'confidence': row[2]
                        })
                
                # Sort by relevance
                suggestions.sort(
                    key=lambda x: x.get('relevance_score', x.get('confidence', 0)),
                    reverse=True
                )
                
                return suggestions[:max_suggestions]
                
        except Exception as e:
            self.logger.error(f"Failed to get contextual suggestions: {e}")
            return []
    
    def search_memory(
        self,
        query: str,
        search_type: str = "all",
        max_results: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search through stored memory.
        
        Args:
            query: Search query
            search_type: Type of search ('conversations', 'tasks', 'preferences', 'all')
            max_results: Maximum results per category
            
        Returns:
            Dictionary with search results by category
        """
        results = {
            'conversations': [],
            'tasks': [],
            'preferences': []
        }
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                if search_type in ['conversations', 'all']:
                    cursor.execute("""
                        SELECT user_input, assistant_response, timestamp, confidence_score
                        FROM conversations
                        WHERE user_input LIKE ? OR assistant_response LIKE ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", max_results))
                    
                    for row in cursor.fetchall():
                        results['conversations'].append({
                            'user_input': row[0],
                            'assistant_response': row[1],
                            'timestamp': row[2],
                            'confidence': row[3]
                        })
                
                if search_type in ['tasks', 'all']:
                    cursor.execute("""
                        SELECT task_id, user_request, task_type, status, created_at
                        FROM tasks
                        WHERE user_request LIKE ? OR task_type LIKE ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", max_results))
                    
                    for row in cursor.fetchall():
                        results['tasks'].append({
                            'task_id': row[0],
                            'user_request': row[1],
                            'task_type': row[2],
                            'status': row[3],
                            'created_at': row[4]
                        })
                
                if search_type in ['preferences', 'all']:
                    cursor.execute("""
                        SELECT key, value, category, confidence, last_used
                        FROM user_preferences
                        WHERE key LIKE ? OR value LIKE ?
                        ORDER BY confidence DESC, last_used DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", max_results))
                    
                    for row in cursor.fetchall():
                        results['preferences'].append({
                            'key': row[0],
                            'value': row[1],
                            'category': row[2],
                            'confidence': row[3],
                            'last_used': row[4]
                        })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to search memory: {e}")
            return results
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Conversation stats
                cursor.execute("SELECT COUNT(*) FROM conversations")
                total_conversations = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM conversations
                    WHERE timestamp > ?
                """, ((datetime.now() - timedelta(days=7)).isoformat(),))
                recent_conversations = cursor.fetchone()[0]
                
                # Task stats
                cursor.execute("SELECT COUNT(*) FROM tasks")
                total_tasks = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END)
                    FROM tasks
                """)
                task_success_rate = cursor.fetchone()[0] or 0.0
                
                # Preference stats
                cursor.execute("SELECT COUNT(*) FROM user_preferences")
                total_preferences = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT AVG(confidence) FROM user_preferences
                """)
                avg_preference_confidence = cursor.fetchone()[0] or 0.0
                
                # Database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'total_conversations': total_conversations,
                    'recent_conversations': recent_conversations,
                    'total_tasks': total_tasks,
                    'task_success_rate': task_success_rate,
                    'total_preferences': total_preferences,
                    'avg_preference_confidence': avg_preference_confidence,
                    'current_session_entries': len(self.current_context.entries),
                    'current_context_tokens': self.current_context.total_tokens,
                    'database_size_bytes': db_size,
                    'session_id': self.session_id
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get memory statistics: {e}")
            return {}
    
    def _load_recent_context(self):
        """Load recent conversation context."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.context_window_hours)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_input, assistant_response, interaction_type,
                           timestamp, sentiment_score, confidence_score,
                           tokens_used, response_time, metadata
                    FROM conversations
                    WHERE timestamp > ?
                    ORDER BY timestamp
                    LIMIT ?
                """, (cutoff_time.isoformat(), self.max_context_entries))
                
                for row in cursor.fetchall():
                    entry = ConversationEntry(
                        user_input=row[0],
                        assistant_response=row[1],
                        interaction_type=InteractionType(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        sentiment_score=row[4],
                        confidence_score=row[5],
                        tokens_used=row[6],
                        response_time=row[7],
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    
                    self.current_context.entries.append(entry)
                    self.current_context.total_tokens += entry.tokens_used
                    self.current_context.sentiment_trend.append(entry.sentiment_score)
                
                self.logger.debug(f"Loaded {len(self.current_context.entries)} context entries")
                
        except Exception as e:
            self.logger.error(f"Failed to load recent context: {e}")
    
    def _maintain_context_window(self):
        """Maintain context window within limits."""
        # Remove old entries if too many
        while len(self.current_context.entries) > self.max_context_entries:
            removed = self.current_context.entries.pop(0)
            self.current_context.total_tokens -= removed.tokens_used
            if self.current_context.sentiment_trend:
                self.current_context.sentiment_trend.pop(0)
        
        # Remove entries if token limit exceeded
        while self.current_context.total_tokens > self.max_context_tokens:
            if not self.current_context.entries:
                break
            removed = self.current_context.entries.pop(0)
            self.current_context.total_tokens -= removed.tokens_used
            if self.current_context.sentiment_trend:
                self.current_context.sentiment_trend.pop(0)
    
    def _learn_from_interaction(self, entry: ConversationEntry):
        """Learn patterns from interaction."""
        try:
            # Extract potential preferences from user input
            self._extract_preferences_from_text(entry.user_input, entry.timestamp)
            
            # Update interaction patterns
            self._update_interaction_patterns(entry)
            
        except Exception as e:
            self.logger.error(f"Failed to learn from interaction: {e}")
    
    def _extract_preferences_from_text(self, text: str, timestamp: datetime):
        """Extract potential preferences from text."""
        # Simple preference extraction patterns
        preference_patterns = {
            r"i prefer (.+?)(?:\.|$)": PreferenceCategory.BEHAVIOR,
            r"i like (.+?)(?:\.|$)": PreferenceCategory.BEHAVIOR,
            r"i usually (.+?)(?:\.|$)": PreferenceCategory.BEHAVIOR,
            r"i always (.+?)(?:\.|$)": PreferenceCategory.BEHAVIOR,
            r"make it (.+?)(?:\.|$)": PreferenceCategory.INTERFACE,
            r"set (.+?) to (.+?)(?:\.|$)": PreferenceCategory.SYSTEM,
        }
        
        text_lower = text.lower()
        
        for pattern, category in preference_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    key, value = match
                else:
                    key = "behavior_preference"
                    value = match
                
                # Clean up the extracted text
                key = key.strip()
                value = value.strip()
                
                if len(key) > 2 and len(value) > 2:
                    self.learn_user_preference(
                        key=key,
                        value=value,
                        category=category,
                        confidence=0.6,
                        context=f"Extracted from: {text[:100]}..."
                    )
    
    def _update_interaction_patterns(self, entry: ConversationEntry):
        """Update interaction patterns based on new entry."""
        pattern_id = f"{entry.interaction_type.value}_{entry.sentiment_score:.1f}"
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Check if pattern exists
                cursor.execute("""
                    SELECT id, frequency, success_rate, avg_response_time
                    FROM interaction_patterns
                    WHERE pattern_id = ?
                """, (pattern_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing pattern
                    new_frequency = existing[1] + 1
                    new_success_rate = (existing[2] + (1.0 if entry.confidence_score > 0.7 else 0.0)) / 2
                    new_avg_response_time = (existing[3] + entry.response_time) / 2
                    
                    cursor.execute("""
                        UPDATE interaction_patterns
                        SET frequency = ?, success_rate = ?, avg_response_time = ?,
                            last_occurrence = ?
                        WHERE id = ?
                    """, (
                        new_frequency,
                        new_success_rate,
                        new_avg_response_time,
                        entry.timestamp.isoformat(),
                        existing[0]
                    ))
                else:
                    # Create new pattern
                    cursor.execute("""
                        INSERT INTO interaction_patterns (
                            pattern_id, pattern_type, frequency, success_rate,
                            avg_response_time, last_occurrence, context_clues, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pattern_id,
                        entry.interaction_type.value,
                        1,
                        1.0 if entry.confidence_score > 0.7 else 0.0,
                        entry.response_time,
                        entry.timestamp.isoformat(),
                        json.dumps([]),
                        json.dumps({})
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update interaction patterns: {e}")
    
    def _learn_task_patterns(self, task: TaskRecord):
        """Learn patterns from task execution."""
        if task.status == TaskStatus.COMPLETED and task.success:
            # Learn successful task patterns
            pattern_key = f"task_success_{task.task_type}"
            self.learn_user_preference(
                key=pattern_key,
                value="successful",
                category=PreferenceCategory.AUTOMATION,
                confidence=0.8,
                context=f"Task {task.task_id} completed successfully"
            )
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity score."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data from database.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Clean up old conversations
                cursor.execute("""
                    DELETE FROM conversations
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                # Clean up old tasks
                cursor.execute("""
                    DELETE FROM tasks
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                # Clean up old context summaries
                cursor.execute("""
                    DELETE FROM context_summaries
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                # Clean up unused preferences (low confidence, not used recently)
                unused_cutoff = datetime.now() - timedelta(days=30)
                cursor.execute("""
                    DELETE FROM user_preferences
                    WHERE confidence < 0.3 AND last_used < ?
                """, (unused_cutoff.isoformat(),))
                
                conn.commit()
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
                
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def close(self):
        """Close database connections and cleanup resources."""
        try:
            # Store context summary before closing
            if self.current_context.entries:
                self._store_context_summary()
            
            self.logger.info("Memory system closed")
            
        except Exception as e:
            self.logger.error(f"Error during memory system cleanup: {e}")
    
    def _store_context_summary(self):
        """Store a summary of the current context."""
        if not self.current_context.entries:
            return
        
        try:
            # Generate simple summary
            topics = []
            for entry in self.current_context.entries:
                # Extract potential topics from user input
                words = entry.user_input.lower().split()
                topics.extend([word for word in words if len(word) > 4])
            
            # Count topic frequency
            topic_counts = Counter(topics)
            top_topics = [topic for topic, count in topic_counts.most_common(5)]
            
            summary = f"Session with {len(self.current_context.entries)} interactions. "
            summary += f"Main topics: {', '.join(top_topics)}. "
            summary += f"Average sentiment: {sum(self.current_context.sentiment_trend) / len(self.current_context.sentiment_trend):.2f}"
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO context_summaries (
                        session_id, summary_text, topics, created_at,
                        entry_count, token_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.session_id,
                    summary,
                    json.dumps(top_topics),
                    datetime.now().isoformat(),
                    len(self.current_context.entries),
                    self.current_context.total_tokens
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store context summary: {e}")


# Convenience function for easy initialization
def create_memory_system(config: Optional[Dict[str, Any]] = None) -> MemorySystem:
    """
    Create and initialize a Memory System instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized MemorySystem instance
    """
    return MemorySystem(config)