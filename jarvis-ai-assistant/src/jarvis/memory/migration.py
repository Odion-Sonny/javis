"""
Memory System Migration Utility

Handles migration from the simple MemoryManager to the advanced MemorySystem.
Preserves existing data and provides backward compatibility.
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from .memory_system import MemorySystem, InteractionType, TaskStatus, PreferenceCategory
except ImportError:
    from memory_system import MemorySystem, InteractionType, TaskStatus, PreferenceCategory


class MemoryMigration:
    """Handles migration between memory system versions."""
    
    def __init__(self, old_db_path: str = "jarvis_memory.db", 
                 new_config: Optional[Dict[str, Any]] = None):
        """
        Initialize migration utility.
        
        Args:
            old_db_path: Path to the old simple memory database
            new_config: Configuration for the new advanced memory system
        """
        self.old_db_path = Path(old_db_path)
        self.logger = logging.getLogger(__name__)
        self.new_config = new_config or {}
        
    def migrate_to_advanced_system(self) -> MemorySystem:
        """
        Migrate data from simple MemoryManager to advanced MemorySystem.
        
        Returns:
            Configured MemorySystem with migrated data
        """
        # Initialize new advanced memory system
        memory_system = MemorySystem(self.new_config)
        
        if not self.old_db_path.exists():
            self.logger.info("No existing memory database found - starting fresh")
            return memory_system
        
        try:
            # Connect to old database
            old_conn = sqlite3.connect(str(self.old_db_path))
            old_conn.row_factory = sqlite3.Row
            
            # Migrate interactions
            self._migrate_interactions(old_conn, memory_system)
            
            # Migrate user preferences
            self._migrate_preferences(old_conn, memory_system)
            
            # Close old connection
            old_conn.close()
            
            # Backup old database
            self._backup_old_database()
            
            self.logger.info("Migration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            raise
        
        return memory_system
    
    def _migrate_interactions(self, old_conn: sqlite3.Connection, 
                            memory_system: MemorySystem):
        """Migrate interaction history."""
        try:
            cursor = old_conn.cursor()
            cursor.execute("""
                SELECT session_id, timestamp, role, content, metadata
                FROM interactions
                ORDER BY timestamp
            """)
            
            interactions = cursor.fetchall()
            migrated_count = 0
            current_session = None
            user_message = None
            
            for interaction in interactions:
                try:
                    session_id = interaction['session_id']
                    timestamp = datetime.fromisoformat(interaction['timestamp'])
                    role = interaction['role']
                    content = interaction['content']
                    metadata = json.loads(interaction['metadata']) if interaction['metadata'] else {}
                    
                    if role == 'user':
                        user_message = content
                        current_session = session_id
                    elif role == 'assistant' and user_message:
                        # Store complete conversation entry
                        memory_system.store_conversation(
                            user_input=user_message,
                            assistant_response=content,
                            interaction_type=InteractionType.CONVERSATION,
                            context_summary="Migrated from old system",
                            sentiment_score=0.0,
                            confidence_score=0.8,  # Default confidence
                            tokens_used=len(content.split()) * 4,  # Rough estimation
                            response_time=1.0,  # Default response time
                            metadata=metadata
                        )
                        migrated_count += 1
                        user_message = None
                        
                except Exception as e:
                    self.logger.warning(f"Failed to migrate interaction: {e}")
                    continue
            
            self.logger.info(f"Migrated {migrated_count} conversation pairs")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate interactions: {e}")
    
    def _migrate_preferences(self, old_conn: sqlite3.Connection, 
                           memory_system: MemorySystem):
        """Migrate user preferences."""
        try:
            cursor = old_conn.cursor()
            cursor.execute("""
                SELECT key, value, updated_at
                FROM user_preferences
            """)
            
            preferences = cursor.fetchall()
            migrated_count = 0
            
            for pref in preferences:
                try:
                    key = pref['key']
                    value = pref['value']
                    
                    # Determine category based on key
                    category = self._categorize_preference(key)
                    
                    memory_system.learn_user_preference(
                        key=key,
                        value=value,
                        category=category,
                        confidence=0.7,  # Moderate confidence for migrated data
                        context="Migrated from old system"
                    )
                    migrated_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to migrate preference {pref['key']}: {e}")
                    continue
            
            self.logger.info(f"Migrated {migrated_count} user preferences")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate preferences: {e}")
    
    def _categorize_preference(self, key: str) -> PreferenceCategory:
        """Categorize a preference based on its key."""
        key_lower = key.lower()
        
        if any(word in key_lower for word in ['voice', 'speech', 'audio', 'sound']):
            return PreferenceCategory.VOICE
        elif any(word in key_lower for word in ['interface', 'ui', 'display', 'theme']):
            return PreferenceCategory.INTERFACE
        elif any(word in key_lower for word in ['system', 'config', 'setting']):
            return PreferenceCategory.SYSTEM
        elif any(word in key_lower for word in ['privacy', 'secure', 'private']):
            return PreferenceCategory.PRIVACY
        elif any(word in key_lower for word in ['auto', 'automation', 'schedule']):
            return PreferenceCategory.AUTOMATION
        else:
            return PreferenceCategory.BEHAVIOR
    
    def _backup_old_database(self):
        """Backup the old database."""
        try:
            if self.old_db_path.exists():
                backup_path = self.old_db_path.with_suffix('.db.backup')
                self.old_db_path.rename(backup_path)
                self.logger.info(f"Old database backed up to: {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to backup old database: {e}")
    
    def check_migration_needed(self) -> bool:
        """Check if migration is needed."""
        return self.old_db_path.exists()
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """Get summary of what would be migrated."""
        if not self.old_db_path.exists():
            return {
                'migration_needed': False,
                'reason': 'No old database found'
            }
        
        try:
            conn = sqlite3.connect(str(self.old_db_path))
            cursor = conn.cursor()
            
            # Count interactions
            cursor.execute("SELECT COUNT(*) FROM interactions")
            interaction_count = cursor.fetchone()[0]
            
            # Count preferences
            cursor.execute("SELECT COUNT(*) FROM user_preferences")
            preference_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'migration_needed': True,
                'interactions_to_migrate': interaction_count,
                'preferences_to_migrate': preference_count,
                'old_database_path': str(self.old_db_path)
            }
            
        except Exception as e:
            return {
                'migration_needed': False,
                'error': str(e)
            }


def create_memory_system_with_migration(config: Dict[str, Any]) -> MemorySystem:
    """
    Create a memory system with automatic migration from old system.
    
    Args:
        config: Memory system configuration
        
    Returns:
        Configured MemorySystem with migrated data
    """
    migration = MemoryMigration(new_config=config)
    
    if migration.check_migration_needed():
        logging.getLogger(__name__).info("Migrating from old memory system...")
        summary = migration.get_migration_summary()
        logging.getLogger(__name__).info(f"Migration summary: {summary}")
        return migration.migrate_to_advanced_system()
    else:
        logging.getLogger(__name__).info("No migration needed - creating new memory system")
        return MemorySystem(config)