"""
Memory Manager Implementation
Handles conversation history, context, and persistent storage.
"""

import logging
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os


@dataclass
class Interaction:
    """Represents a single interaction (message) in conversation."""
    timestamp: datetime
    role: str  # "user" or "assistant"
    content: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MemoryManager:
    """Manages conversation memory and context."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize memory manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_context_length = config.get("max_context_length", 4000)
        self.context_window_hours = config.get("context_window_hours", 24)
        self.db_path = config.get("db_path", "jarvis_memory.db")
        
        # In-memory storage for current session
        self.current_session: List[Interaction] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize database
        self._init_database()
        
        self.logger.info("Memory manager initialized")
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            self.conn.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    async def add_interaction(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new interaction to memory."""
        try:
            interaction = Interaction(
                timestamp=datetime.now(),
                role=role,
                content=content,
                metadata=metadata or {}
            )
            
            # Add to current session
            self.current_session.append(interaction)
            
            # Persist to database
            await self._persist_interaction(interaction)
            
            # Clean up old interactions if needed
            await self._cleanup_old_interactions()
            
        except Exception as e:
            self.logger.error(f"Error adding interaction: {e}")
    
    async def _persist_interaction(self, interaction: Interaction):
        """Persist interaction to database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO interactions (session_id, timestamp, role, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.session_id,
                interaction.timestamp.isoformat(),
                interaction.role,
                interaction.content,
                json.dumps(interaction.metadata) if interaction.metadata else None
            ))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error persisting interaction: {e}")
    
    async def get_context(self, max_tokens: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation context for AI model.
        
        Args:
            max_tokens: Maximum tokens to include in context
            
        Returns:
            List of interactions formatted for AI model
        """
        try:
            max_tokens = max_tokens or self.max_context_length
            
            # Get recent interactions
            recent_interactions = await self._get_recent_interactions()
            
            # Format for AI model
            context = []
            total_length = 0
            
            # Add interactions in reverse order (most recent first) until we hit token limit
            for interaction in reversed(recent_interactions):
                interaction_dict = {
                    "role": interaction.role,
                    "content": interaction.content,
                    "timestamp": interaction.timestamp.isoformat()
                }
                
                # Rough token estimation (1 token ≈ 4 characters)
                interaction_length = len(interaction.content) // 4
                
                if total_length + interaction_length > max_tokens:
                    break
                
                context.insert(0, interaction_dict)  # Insert at beginning to maintain order
                total_length += interaction_length
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting context: {e}")
            return []
    
    async def _get_recent_interactions(self) -> List[Interaction]:
        """Get recent interactions from current session and database."""
        try:
            # Start with current session
            interactions = list(self.current_session)
            
            # Add recent interactions from database (from other sessions)
            cutoff_time = datetime.now() - timedelta(hours=self.context_window_hours)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT timestamp, role, content, metadata
                FROM interactions
                WHERE session_id != ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (self.session_id, cutoff_time.isoformat()))
            
            for row in cursor.fetchall():
                interaction = Interaction(
                    timestamp=datetime.fromisoformat(row[0]),
                    role=row[1],
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {}
                )
                interactions.append(interaction)
            
            # Sort by timestamp
            interactions.sort(key=lambda x: x.timestamp)
            
            return interactions
            
        except Exception as e:
            self.logger.error(f"Error getting recent interactions: {e}")
            return list(self.current_session)
    
    async def _cleanup_old_interactions(self):
        """Clean up old interactions to manage storage."""
        try:
            # Keep only recent interactions in current session
            if len(self.current_session) > 100:
                self.current_session = self.current_session[-50:]
            
            # Clean up old database entries (keep last 30 days)
            cutoff_time = datetime.now() - timedelta(days=30)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM interactions
                WHERE timestamp < ?
            """, (cutoff_time.isoformat(),))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up interactions: {e}")
    
    async def save_user_preference(self, key: str, value: str):
        """Save a user preference."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now().isoformat()))
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error saving user preference: {e}")
    
    async def get_user_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a user preference."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT value FROM user_preferences WHERE key = ?
            """, (key,))
            
            result = cursor.fetchone()
            return result[0] if result else default
            
        except Exception as e:
            self.logger.error(f"Error getting user preference: {e}")
            return default
    
    async def search_interactions(self, query: str, limit: int = 10) -> List[Interaction]:
        """Search through interaction history."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT timestamp, role, content, metadata
                FROM interactions
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            
            interactions = []
            for row in cursor.fetchall():
                interaction = Interaction(
                    timestamp=datetime.fromisoformat(row[0]),
                    role=row[1],
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {}
                )
                interactions.append(interaction)
            
            return interactions
            
        except Exception as e:
            self.logger.error(f"Error searching interactions: {e}")
            return []
    
    async def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        try:
            if not self.current_session:
                return "No conversation history in current session."
            
            # Simple summary - in a real implementation, this could use AI to generate summaries
            user_messages = [i for i in self.current_session if i.role == "user"]
            assistant_messages = [i for i in self.current_session if i.role == "assistant"]
            
            summary = f"Current session started at {self.current_session[0].timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            summary += f"Total interactions: {len(self.current_session)}\n"
            summary += f"User messages: {len(user_messages)}\n"
            summary += f"Assistant responses: {len(assistant_messages)}\n"
            
            if user_messages:
                summary += f"Latest user message: {user_messages[-1].content[:100]}..."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return "Error generating summary."
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
            self.logger.info("Memory manager closed")