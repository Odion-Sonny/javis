"""
Learning Module for Jarvis AI Assistant

This module implements intelligent learning capabilities including:
- User behavior pattern recognition
- Preference extraction from interactions
- Command frequency analysis
- Proactive suggestion generation
- Feedback incorporation for improving responses

The module is designed to be modular and extensible for future enhancements.
"""

import logging
import re
import json
import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics

try:
    from ..memory.memory_system import MemorySystem, InteractionType, PreferenceCategory
except ImportError:
    from memory_system import MemorySystem, InteractionType, PreferenceCategory


class LearningType(Enum):
    """Types of learning algorithms."""
    PATTERN_RECOGNITION = "pattern_recognition"
    PREFERENCE_EXTRACTION = "preference_extraction"
    FREQUENCY_ANALYSIS = "frequency_analysis"
    SUGGESTION_GENERATION = "suggestion_generation"
    FEEDBACK_INCORPORATION = "feedback_incorporation"


class PatternConfidence(Enum):
    """Confidence levels for learned patterns."""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class UserBehaviorPattern:
    """Represents a learned user behavior pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    confidence: float
    last_observed: datetime
    context_clues: List[str] = field(default_factory=list)
    temporal_patterns: Dict[str, float] = field(default_factory=dict)  # time-based patterns
    triggers: List[str] = field(default_factory=list)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandPattern:
    """Represents command usage patterns."""
    command: str
    frequency: int
    success_rate: float
    avg_response_time: float
    common_contexts: List[str] = field(default_factory=list)
    user_satisfaction: float = 0.0
    trending_score: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)


@dataclass
class ProactiveSuggestion:
    """Represents a proactive suggestion for the user."""
    suggestion_id: str
    suggestion_type: str
    content: str
    confidence: float
    relevance_score: float
    context: str
    reasoning: str
    expected_benefit: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackData:
    """Represents user feedback data."""
    feedback_id: str
    interaction_id: str
    feedback_type: str  # positive, negative, neutral
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    specific_aspect: Optional[str] = None  # what aspect was good/bad
    improvement_suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class BaseLearningEngine(ABC):
    """Abstract base class for learning engines."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def learn(self, data: Any) -> Dict[str, Any]:
        """Learn from provided data."""
        pass
    
    @abstractmethod
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from learned patterns."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this learning engine is enabled."""
        return self.enabled


class PatternRecognitionEngine(BaseLearningEngine):
    """Engine for recognizing user behavior patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.min_pattern_frequency = config.get('min_pattern_frequency', 3)
        self.pattern_window_days = config.get('pattern_window_days', 7)
        self.patterns: Dict[str, UserBehaviorPattern] = {}
    
    def learn(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn patterns from interaction data."""
        if not self.enabled:
            return {}
        
        try:
            # Analyze temporal patterns
            temporal_patterns = self._analyze_temporal_patterns(interactions)
            
            # Analyze sequence patterns
            sequence_patterns = self._analyze_sequence_patterns(interactions)
            
            # Analyze context patterns
            context_patterns = self._analyze_context_patterns(interactions)
            
            # Update pattern database
            self._update_patterns(temporal_patterns, sequence_patterns, context_patterns)
            
            return {
                'patterns_identified': len(self.patterns),
                'temporal_patterns': len(temporal_patterns),
                'sequence_patterns': len(sequence_patterns),
                'context_patterns': len(context_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Pattern recognition failed: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Analyze time-based usage patterns."""
        temporal_data = defaultdict(list)
        
        for interaction in interactions:
            timestamp = datetime.fromisoformat(interaction.get('timestamp', ''))
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            interaction_type = interaction.get('interaction_type', 'unknown')
            
            temporal_data[f"{interaction_type}_hourly"].append(hour)
            temporal_data[f"{interaction_type}_daily"].append(day_of_week)
        
        patterns = {}
        for pattern_type, times in temporal_data.items():
            if len(times) >= self.min_pattern_frequency:
                # Calculate frequency distribution
                time_counter = Counter(times)
                total = len(times)
                frequency_dist = {str(k): v/total for k, v in time_counter.items()}
                patterns[pattern_type] = frequency_dist
        
        return patterns
    
    def _analyze_sequence_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze command/interaction sequences."""
        sequences = []
        current_sequence = []
        
        for interaction in interactions:
            user_input = interaction.get('user_input', '').lower().strip()
            if user_input:
                current_sequence.append(user_input)
                if len(current_sequence) >= 3:  # Look for 3+ command sequences
                    sequences.append(tuple(current_sequence[-3:]))
        
        sequence_patterns = {}
        sequence_counter = Counter(sequences)
        
        for sequence, count in sequence_counter.items():
            if count >= self.min_pattern_frequency:
                pattern_id = f"sequence_{'_'.join(sequence[:2])}"
                sequence_patterns[pattern_id] = {
                    'sequence': sequence,
                    'frequency': count,
                    'confidence': min(count / len(sequences), 1.0)
                }
        
        return sequence_patterns
    
    def _analyze_context_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze contextual usage patterns."""
        context_data = defaultdict(list)
        
        for interaction in interactions:
            user_input = interaction.get('user_input', '').lower()
            context = interaction.get('context_summary', '')
            interaction_type = interaction.get('interaction_type', 'conversation')
            
            # Extract keywords from user input
            keywords = self._extract_keywords(user_input)
            
            for keyword in keywords:
                context_data[keyword].append({
                    'interaction_type': interaction_type,
                    'context': context,
                    'timestamp': interaction.get('timestamp')
                })
        
        patterns = {}
        for keyword, occurrences in context_data.items():
            if len(occurrences) >= self.min_pattern_frequency:
                # Analyze context associations
                contexts = [occ['context'] for occ in occurrences if occ['context']]
                interaction_types = [occ['interaction_type'] for occ in occurrences]
                
                patterns[f"context_{keyword}"] = {
                    'keyword': keyword,
                    'frequency': len(occurrences),
                    'common_contexts': list(set(contexts))[:5],
                    'interaction_types': dict(Counter(interaction_types)),
                    'confidence': min(len(occurrences) / 10, 1.0)  # Max confidence at 10+ occurrences
                }
        
        return patterns
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Simple keyword extraction - could be enhanced with NLP
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'please', 'help', 'me', 'i', 'you', 'it', 'this', 'that'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return list(set(keywords))[:10]  # Return up to 10 unique keywords
    
    def _update_patterns(self, temporal: Dict, sequence: Dict, context: Dict):
        """Update the pattern database with new findings."""
        all_patterns = {**temporal, **sequence, **context}
        
        for pattern_id, pattern_data in all_patterns.items():
            if pattern_id in self.patterns:
                # Update existing pattern
                existing = self.patterns[pattern_id]
                existing.frequency += pattern_data.get('frequency', 1)
                existing.confidence = min(existing.confidence + 0.1, 1.0)
                existing.last_observed = datetime.now()
            else:
                # Create new pattern
                self.patterns[pattern_id] = UserBehaviorPattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_id.split('_')[0],
                    description=f"Pattern: {pattern_id}",
                    frequency=pattern_data.get('frequency', 1),
                    confidence=pattern_data.get('confidence', 0.5),
                    last_observed=datetime.now(),
                    metadata=pattern_data
                )
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from recognized patterns."""
        if not self.patterns:
            return {'message': 'No patterns identified yet'}
        
        # Group patterns by type
        pattern_types = defaultdict(list)
        for pattern in self.patterns.values():
            pattern_types[pattern.pattern_type].append(pattern)
        
        insights = {}
        for pattern_type, patterns in pattern_types.items():
            insights[pattern_type] = {
                'count': len(patterns),
                'avg_confidence': statistics.mean([p.confidence for p in patterns]),
                'most_frequent': max(patterns, key=lambda x: x.frequency).pattern_id if patterns else None
            }
        
        return insights


class PreferenceExtractionEngine(BaseLearningEngine):
    """Engine for extracting user preferences from interactions."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        self.preference_patterns = self._load_preference_patterns()
    
    def _load_preference_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for identifying preferences in text."""
        return {
            'explicit_preference': {
                'patterns': [
                    r'i prefer (.+?)(?:\.|$|,)',
                    r'i like (.+?) better',
                    r'i want (.+?)(?:\.|$|,)',
                    r'i need (.+?)(?:\.|$|,)',
                    r'i\'d rather (.+?)(?:\.|$|,)',
                    r'please (.+?)(?:\.|$|,)',
                    r'always (.+?)(?:\.|$|,)',
                    r'never (.+?)(?:\.|$|,)'
                ],
                'category': PreferenceCategory.BEHAVIOR,
                'confidence': 0.8
            },
            'interface_preference': {
                'patterns': [
                    r'make it (.+?)(?:\.|$|,)',
                    r'change the (.+?)(?:\.|$|,)',
                    r'set (.+?) to (.+?)(?:\.|$|,)',
                    r'use (.+?) instead',
                    r'show me (.+?)(?:\.|$|,)',
                    r'display (.+?)(?:\.|$|,)'
                ],
                'category': PreferenceCategory.INTERFACE,
                'confidence': 0.7
            },
            'voice_preference': {
                'patterns': [
                    r'speak (.+?)(?:\.|$|,)',
                    r'say (.+?)(?:\.|$|,)',
                    r'voice (.+?)(?:\.|$|,)',
                    r'sound (.+?)(?:\.|$|,)',
                    r'volume (.+?)(?:\.|$|,)',
                    r'speed (.+?)(?:\.|$|,)'
                ],
                'category': PreferenceCategory.VOICE,
                'confidence': 0.7
            },
            'automation_preference': {
                'patterns': [
                    r'automatically (.+?)(?:\.|$|,)',
                    r'auto (.+?)(?:\.|$|,)',
                    r'schedule (.+?)(?:\.|$|,)',
                    r'remind me (.+?)(?:\.|$|,)',
                    r'every (.+?)(?:\.|$|,)',
                    r'when (.+?) then (.+?)(?:\.|$|,)'
                ],
                'category': PreferenceCategory.AUTOMATION,
                'confidence': 0.6
            }
        }
    
    def learn(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract preferences from interaction data."""
        if not self.enabled:
            return {}
        
        extracted_preferences = []
        
        try:
            for interaction in interactions:
                user_input = interaction.get('user_input', '')
                preferences = self._extract_preferences_from_text(user_input)
                
                for pref in preferences:
                    pref['interaction_context'] = interaction.get('context_summary', '')
                    pref['timestamp'] = interaction.get('timestamp')
                    extracted_preferences.append(pref)
            
            return {
                'preferences_extracted': len(extracted_preferences),
                'preferences': extracted_preferences
            }
            
        except Exception as e:
            self.logger.error(f"Preference extraction failed: {e}")
            return {}
    
    def _extract_preferences_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract preferences from a single text input."""
        preferences = []
        text_lower = text.lower().strip()
        
        for pref_type, config in self.preference_patterns.items():
            for pattern in config['patterns']:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        key, value = match
                    else:
                        key = pref_type
                        value = match
                    
                    # Clean up extracted text
                    key = key.strip()
                    value = value.strip()
                    
                    if len(key) > 1 and len(value) > 1:
                        preferences.append({
                            'key': key,
                            'value': value,
                            'category': config['category'],
                            'confidence': config['confidence'],
                            'extraction_method': pref_type,
                            'source_text': text[:100] + '...' if len(text) > 100 else text
                        })
        
        return preferences
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights about extracted preferences."""
        return {
            'extraction_patterns': len(self.preference_patterns),
            'categories_supported': list(set(config['category'] for config in self.preference_patterns.values())),
            'confidence_threshold': self.confidence_threshold
        }


class CommandFrequencyAnalyzer(BaseLearningEngine):
    """Engine for analyzing command usage frequency and trends."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analysis_window_days = config.get('analysis_window_days', 30)
        self.min_frequency = config.get('min_frequency', 2)
        self.command_patterns: Dict[str, CommandPattern] = {}
    
    def learn(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command frequency from interactions."""
        if not self.enabled:
            return {}
        
        try:
            # Extract commands from interactions
            commands = self._extract_commands(interactions)
            
            # Analyze frequency and trends
            frequency_data = self._analyze_frequency(commands)
            trend_data = self._analyze_trends(commands)
            success_data = self._analyze_success_rates(interactions)
            
            # Update command patterns
            self._update_command_patterns(frequency_data, trend_data, success_data)
            
            return {
                'commands_analyzed': len(commands),
                'unique_commands': len(set(commands)),
                'patterns_updated': len(self.command_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Command frequency analysis failed: {e}")
            return {}
    
    def _extract_commands(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract command information from interactions."""
        commands = []
        
        for interaction in interactions:
            user_input = interaction.get('user_input', '').lower().strip()
            timestamp = datetime.fromisoformat(interaction.get('timestamp', ''))
            
            # Simple command extraction - identify action words
            command_words = self._identify_command_words(user_input)
            
            for cmd in command_words:
                commands.append({
                    'command': cmd,
                    'full_input': user_input,
                    'timestamp': timestamp,
                    'interaction_type': interaction.get('interaction_type'),
                    'context': interaction.get('context_summary', ''),
                    'confidence_score': interaction.get('confidence_score', 0.0)
                })
        
        return commands
    
    def _identify_command_words(self, text: str) -> List[str]:
        """Identify command words in text."""
        action_words = {
            'open', 'close', 'start', 'stop', 'run', 'execute', 'create', 'delete', 
            'save', 'load', 'show', 'hide', 'search', 'find', 'get', 'set',
            'change', 'modify', 'update', 'install', 'remove', 'move', 'copy',
            'send', 'receive', 'connect', 'disconnect', 'play', 'pause',
            'calculate', 'compute', 'analyze', 'check', 'verify', 'test'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        commands = [word for word in words if word in action_words]
        
        # Also look for compound commands
        compound_patterns = [
            r'(turn on|turn off|shut down|log in|log out|sign in|sign out)',
            r'(look up|back up|set up|clean up|speed up|slow down)',
            r'(check out|find out|figure out|work out)'
        ]
        
        for pattern in compound_patterns:
            matches = re.findall(pattern, text)
            commands.extend([match.replace(' ', '_') for match in matches])
        
        return list(set(commands))
    
    def _analyze_frequency(self, commands: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze command frequency."""
        command_counts = Counter([cmd['command'] for cmd in commands])
        return dict(command_counts)
    
    def _analyze_trends(self, commands: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze command usage trends."""
        if len(commands) < 2:
            return {}
        
        # Group by command and time periods
        now = datetime.now()
        recent_threshold = now - timedelta(days=7)
        older_threshold = now - timedelta(days=14)
        
        recent_commands = [cmd for cmd in commands if cmd['timestamp'] >= recent_threshold]
        older_commands = [cmd for cmd in commands if older_threshold <= cmd['timestamp'] < recent_threshold]
        
        recent_counts = Counter([cmd['command'] for cmd in recent_commands])
        older_counts = Counter([cmd['command'] for cmd in older_commands])
        
        trends = {}
        for command in set(list(recent_counts.keys()) + list(older_counts.keys())):
            recent_freq = recent_counts.get(command, 0)
            older_freq = older_counts.get(command, 0)
            
            if older_freq > 0:
                trend_score = (recent_freq - older_freq) / older_freq
            else:
                trend_score = 1.0 if recent_freq > 0 else 0.0
            
            trends[command] = trend_score
        
        return trends
    
    def _analyze_success_rates(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze success rates for commands."""
        success_data = defaultdict(list)
        
        for interaction in interactions:
            user_input = interaction.get('user_input', '').lower()
            confidence = interaction.get('confidence_score', 0.0)
            commands = self._identify_command_words(user_input)
            
            for cmd in commands:
                success_data[cmd].append(confidence)
        
        success_rates = {}
        for cmd, confidences in success_data.items():
            if confidences:
                success_rates[cmd] = statistics.mean(confidences)
        
        return success_rates
    
    def _update_command_patterns(self, frequency_data: Dict[str, int], 
                                trend_data: Dict[str, float], 
                                success_data: Dict[str, float]):
        """Update command pattern database."""
        all_commands = set(list(frequency_data.keys()) + list(trend_data.keys()) + list(success_data.keys()))
        
        for command in all_commands:
            frequency = frequency_data.get(command, 0)
            trend = trend_data.get(command, 0.0)
            success_rate = success_data.get(command, 0.0)
            
            if frequency >= self.min_frequency:
                if command in self.command_patterns:
                    # Update existing pattern
                    pattern = self.command_patterns[command]
                    pattern.frequency = frequency
                    pattern.trending_score = trend
                    pattern.success_rate = success_rate
                    pattern.last_used = datetime.now()
                else:
                    # Create new pattern
                    self.command_patterns[command] = CommandPattern(
                        command=command,
                        frequency=frequency,
                        success_rate=success_rate,
                        avg_response_time=1.0,  # Default
                        trending_score=trend,
                        last_used=datetime.now()
                    )
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights about command usage."""
        if not self.command_patterns:
            return {'message': 'No command patterns identified yet'}
        
        # Get top commands by different metrics
        top_frequent = sorted(self.command_patterns.values(), key=lambda x: x.frequency, reverse=True)[:5]
        top_trending = sorted(self.command_patterns.values(), key=lambda x: x.trending_score, reverse=True)[:5]
        top_successful = sorted(self.command_patterns.values(), key=lambda x: x.success_rate, reverse=True)[:5]
        
        return {
            'total_commands': len(self.command_patterns),
            'top_frequent': [cmd.command for cmd in top_frequent],
            'top_trending': [cmd.command for cmd in top_trending],
            'top_successful': [cmd.command for cmd in top_successful],
            'avg_success_rate': statistics.mean([cmd.success_rate for cmd in self.command_patterns.values()])
        }


class ProactiveSuggestionEngine(BaseLearningEngine):
    """Engine for generating proactive suggestions based on learned patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.suggestion_threshold = config.get('suggestion_threshold', 0.7)
        self.max_suggestions = config.get('max_suggestions', 5)
        self.suggestion_types = config.get('suggestion_types', [
            'command_optimization', 'workflow_improvement', 'preference_suggestion',
            'automation_opportunity', 'learning_tip'
        ])
    
    def learn(self, patterns: Dict[str, Any], commands: Dict[str, Any], 
             preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestions based on learned data."""
        if not self.enabled:
            return {}
        
        try:
            suggestions = []
            
            # Generate different types of suggestions
            suggestions.extend(self._generate_command_suggestions(commands))
            suggestions.extend(self._generate_workflow_suggestions(patterns))
            suggestions.extend(self._generate_automation_suggestions(patterns))
            suggestions.extend(self._generate_preference_suggestions(preferences))
            
            # Rank and filter suggestions
            ranked_suggestions = self._rank_suggestions(suggestions)
            top_suggestions = ranked_suggestions[:self.max_suggestions]
            
            return {
                'suggestions_generated': len(suggestions),
                'top_suggestions': len(top_suggestions),
                'suggestions': [s.__dict__ for s in top_suggestions]
            }
            
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {e}")
            return {}
    
    def _generate_command_suggestions(self, command_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate command optimization suggestions."""
        suggestions = []
        command_patterns = command_data.get('command_patterns', {})
        
        for command, pattern in command_patterns.items():
            if hasattr(pattern, 'success_rate') and pattern.success_rate < 0.5:
                suggestion = ProactiveSuggestion(
                    suggestion_id=f"cmd_opt_{command}_{int(datetime.now().timestamp())}",
                    suggestion_type="command_optimization",
                    content=f"The command '{command}' has low success rate ({pattern.success_rate:.2f}). Consider rephrasing or using alternatives.",
                    confidence=0.8,
                    relevance_score=pattern.frequency / 10,  # Higher for more frequent commands
                    context=f"Command: {command}",
                    reasoning=f"Success rate of {pattern.success_rate:.2f} is below optimal threshold",
                    expected_benefit="Improved command success and user satisfaction"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_workflow_suggestions(self, pattern_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate workflow improvement suggestions."""
        suggestions = []
        
        # Look for sequence patterns that could be automated
        sequence_patterns = pattern_data.get('sequence_patterns', {})
        
        for pattern_id, pattern in sequence_patterns.items():
            if pattern.get('frequency', 0) >= 3:  # Frequently repeated sequences
                suggestion = ProactiveSuggestion(
                    suggestion_id=f"workflow_{pattern_id}_{int(datetime.now().timestamp())}",
                    suggestion_type="workflow_improvement",
                    content=f"You frequently use the sequence: {' → '.join(pattern.get('sequence', []))}. Consider creating a shortcut or macro.",
                    confidence=pattern.get('confidence', 0.5),
                    relevance_score=pattern.get('frequency', 0) / 5,
                    context=f"Sequence pattern: {pattern_id}",
                    reasoning=f"Sequence repeated {pattern.get('frequency', 0)} times",
                    expected_benefit="Reduced time and effort for common tasks"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_automation_suggestions(self, pattern_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate automation opportunity suggestions."""
        suggestions = []
        
        # Look for temporal patterns that suggest automation opportunities
        temporal_patterns = pattern_data.get('temporal_patterns', {})
        
        for pattern_type, distribution in temporal_patterns.items():
            if isinstance(distribution, dict):
                # Find time periods with high activity
                max_activity = max(distribution.values()) if distribution else 0
                
                if max_activity > 0.3:  # More than 30% of activity at specific times
                    peak_time = max(distribution.keys(), key=lambda k: distribution[k])
                    
                    suggestion = ProactiveSuggestion(
                        suggestion_id=f"auto_{pattern_type}_{int(datetime.now().timestamp())}",
                        suggestion_type="automation_opportunity",
                        content=f"You often use {pattern_type.replace('_', ' ')} around {peak_time}. Consider setting up automated reminders or actions.",
                        confidence=0.6,
                        relevance_score=max_activity,
                        context=f"Temporal pattern: {pattern_type}",
                        reasoning=f"Peak activity at {peak_time} ({max_activity:.2f} of total)",
                        expected_benefit="Proactive assistance and reduced manual effort"
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_preference_suggestions(self, preference_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate preference-based suggestions."""
        suggestions = []
        
        # Look for conflicting or incomplete preferences
        extracted_prefs = preference_data.get('preferences', [])
        
        # Group preferences by category
        pref_categories = defaultdict(list)
        for pref in extracted_prefs:
            category = pref.get('category', 'unknown')
            pref_categories[str(category)].append(pref)
        
        for category, prefs in pref_categories.items():
            if len(prefs) >= 2:  # Multiple preferences in same category
                suggestion = ProactiveSuggestion(
                    suggestion_id=f"pref_{category}_{int(datetime.now().timestamp())}",
                    suggestion_type="preference_suggestion",
                    content=f"I've learned several {category} preferences. Would you like me to apply these settings consistently?",
                    confidence=0.7,
                    relevance_score=len(prefs) / 5,
                    context=f"Category: {category}",
                    reasoning=f"Multiple preferences identified in {category} category",
                    expected_benefit="More consistent and personalized experience"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _rank_suggestions(self, suggestions: List[ProactiveSuggestion]) -> List[ProactiveSuggestion]:
        """Rank suggestions by relevance and confidence."""
        def suggestion_score(suggestion: ProactiveSuggestion) -> float:
            return suggestion.confidence * suggestion.relevance_score
        
        return sorted(suggestions, key=suggestion_score, reverse=True)
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights about suggestion generation."""
        return {
            'suggestion_types': self.suggestion_types,
            'suggestion_threshold': self.suggestion_threshold,
            'max_suggestions': self.max_suggestions
        }


class FeedbackIncorporationEngine(BaseLearningEngine):
    """Engine for incorporating user feedback to improve responses."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feedback_weight = config.get('feedback_weight', 0.3)
        self.improvement_threshold = config.get('improvement_threshold', 0.1)
        self.feedback_history: List[FeedbackData] = []
    
    def learn(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn from user feedback."""
        if not self.enabled:
            return {}
        
        try:
            processed_feedback = []
            
            for feedback in feedback_data:
                feedback_obj = self._process_feedback(feedback)
                if feedback_obj:
                    self.feedback_history.append(feedback_obj)
                    processed_feedback.append(feedback_obj)
            
            # Analyze feedback patterns
            insights = self._analyze_feedback_patterns()
            
            return {
                'feedback_processed': len(processed_feedback),
                'total_feedback': len(self.feedback_history),
                'insights': insights
            }
            
        except Exception as e:
            self.logger.error(f"Feedback incorporation failed: {e}")
            return {}
    
    def _process_feedback(self, feedback_data: Dict[str, Any]) -> Optional[FeedbackData]:
        """Process raw feedback data into structured format."""
        try:
            return FeedbackData(
                feedback_id=feedback_data.get('feedback_id', f"fb_{int(datetime.now().timestamp())}"),
                interaction_id=feedback_data.get('interaction_id', ''),
                feedback_type=feedback_data.get('feedback_type', 'neutral'),
                rating=feedback_data.get('rating'),
                comment=feedback_data.get('comment'),
                specific_aspect=feedback_data.get('specific_aspect'),
                improvement_suggestion=feedback_data.get('improvement_suggestion'),
                timestamp=datetime.fromisoformat(feedback_data.get('timestamp', datetime.now().isoformat()))
            )
        except Exception as e:
            self.logger.warning(f"Failed to process feedback: {e}")
            return None
    
    def _analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in user feedback."""
        if not self.feedback_history:
            return {}
        
        # Analyze feedback types
        feedback_types = Counter([fb.feedback_type for fb in self.feedback_history])
        
        # Analyze ratings
        ratings = [fb.rating for fb in self.feedback_history if fb.rating is not None]
        avg_rating = statistics.mean(ratings) if ratings else 0
        
        # Analyze aspects mentioned
        aspects = [fb.specific_aspect for fb in self.feedback_history if fb.specific_aspect]
        aspect_counts = Counter(aspects)
        
        # Identify improvement areas
        negative_feedback = [fb for fb in self.feedback_history if fb.feedback_type == 'negative']
        improvement_areas = Counter([fb.specific_aspect for fb in negative_feedback if fb.specific_aspect])
        
        return {
            'feedback_distribution': dict(feedback_types),
            'average_rating': avg_rating,
            'most_mentioned_aspects': dict(aspect_counts.most_common(5)),
            'improvement_areas': dict(improvement_areas.most_common(3)),
            'total_feedback_count': len(self.feedback_history)
        }
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for improvement based on feedback."""
        suggestions = []
        
        # Analyze negative feedback for improvement opportunities
        negative_feedback = [fb for fb in self.feedback_history if fb.feedback_type == 'negative']
        
        for feedback in negative_feedback:
            if feedback.improvement_suggestion:
                suggestions.append({
                    'area': feedback.specific_aspect or 'general',
                    'suggestion': feedback.improvement_suggestion,
                    'priority': 'high' if feedback.rating and feedback.rating <= 2 else 'medium',
                    'feedback_id': feedback.feedback_id
                })
        
        return suggestions
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights about feedback incorporation."""
        return {
            'feedback_count': len(self.feedback_history),
            'patterns': self._analyze_feedback_patterns(),
            'improvement_suggestions': len(self.get_improvement_suggestions())
        }


class LearningModule:
    """Main learning module that orchestrates all learning engines."""
    
    def __init__(self, config: Dict[str, Any], memory_system: MemorySystem):
        """
        Initialize the learning module.
        
        Args:
            config: Learning module configuration
            memory_system: Memory system for data access
        """
        self.config = config
        self.memory_system = memory_system
        self.logger = logging.getLogger(__name__)
        
        # Initialize learning engines
        self.engines = self._initialize_engines()
        
        # Learning configuration
        self.learning_interval_hours = config.get('learning_interval_hours', 24)
        self.last_learning_run = datetime.now() - timedelta(hours=self.learning_interval_hours)
        
        self.logger.info("Learning module initialized with engines: " + 
                        ", ".join(self.engines.keys()))
    
    def _initialize_engines(self) -> Dict[str, BaseLearningEngine]:
        """Initialize all learning engines based on configuration."""
        engines = {}
        
        # Pattern Recognition Engine
        pattern_config = self.config.get('pattern_recognition', {})
        if pattern_config.get('enabled', True):
            engines['pattern_recognition'] = PatternRecognitionEngine(pattern_config)
        
        # Preference Extraction Engine
        preference_config = self.config.get('preference_extraction', {})
        if preference_config.get('enabled', True):
            engines['preference_extraction'] = PreferenceExtractionEngine(preference_config)
        
        # Command Frequency Analyzer
        frequency_config = self.config.get('command_frequency', {})
        if frequency_config.get('enabled', True):
            engines['command_frequency'] = CommandFrequencyAnalyzer(frequency_config)
        
        # Proactive Suggestion Engine
        suggestion_config = self.config.get('suggestion_generation', {})
        if suggestion_config.get('enabled', True):
            engines['suggestion_generation'] = ProactiveSuggestionEngine(suggestion_config)
        
        # Feedback Incorporation Engine
        feedback_config = self.config.get('feedback_incorporation', {})
        if feedback_config.get('enabled', True):
            engines['feedback_incorporation'] = FeedbackIncorporationEngine(feedback_config)
        
        return engines
    
    def run_learning_cycle(self, force: bool = False) -> Dict[str, Any]:
        """
        Run a complete learning cycle.
        
        Args:
            force: Force learning even if interval hasn't passed
            
        Returns:
            Dictionary with learning results
        """
        try:
            # Check if learning should run
            if not force and not self._should_run_learning():
                return {'status': 'skipped', 'reason': 'interval not reached'}
            
            self.logger.info("Starting learning cycle...")
            
            # Get data from memory system
            learning_data = self._gather_learning_data()
            
            # Run each learning engine
            results = {}
            for engine_name, engine in self.engines.items():
                if engine.is_enabled():
                    try:
                        engine_result = self._run_engine(engine, learning_data)
                        results[engine_name] = engine_result
                    except Exception as e:
                        self.logger.error(f"Engine {engine_name} failed: {e}")
                        results[engine_name] = {'error': str(e)}
            
            # Generate comprehensive insights
            insights = self._generate_insights(results)
            
            # Update last learning run time
            self.last_learning_run = datetime.now()
            
            self.logger.info(f"Learning cycle completed. Engines run: {len(results)}")
            
            return {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'engines_run': list(results.keys()),
                'results': results,
                'insights': insights
            }
            
        except Exception as e:
            self.logger.error(f"Learning cycle failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _should_run_learning(self) -> bool:
        """Check if learning cycle should run based on interval."""
        time_since_last = datetime.now() - self.last_learning_run
        return time_since_last.total_seconds() >= (self.learning_interval_hours * 3600)
    
    def _gather_learning_data(self) -> Dict[str, Any]:
        """Gather data from memory system for learning."""
        try:
            # Get recent interactions
            interactions = self.memory_system.get_conversation_context(
                max_entries=100, include_metadata=True
            )
            
            # Get user preferences
            preference_categories = ['voice', 'interface', 'behavior', 'system', 'automation']
            preferences = {}
            for category in preference_categories:
                try:
                    cat_enum = getattr(PreferenceCategory, category.upper())
                    prefs = self.memory_system.get_preferences_by_category(cat_enum)
                    preferences[category] = [pref.__dict__ for pref in prefs]
                except:
                    preferences[category] = []
            
            # Get interaction patterns
            patterns = self.memory_system.analyze_interaction_patterns(days_back=30)
            
            # Get task history
            tasks = self.memory_system.get_task_history(limit=50)
            
            return {
                'interactions': interactions,
                'preferences': preferences,
                'patterns': patterns,
                'tasks': [task.__dict__ for task in tasks]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to gather learning data: {e}")
            return {}
    
    def _run_engine(self, engine: BaseLearningEngine, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific learning engine with the provided data."""
        if isinstance(engine, PatternRecognitionEngine):
            return engine.learn(data.get('interactions', []))
        elif isinstance(engine, PreferenceExtractionEngine):
            return engine.learn(data.get('interactions', []))
        elif isinstance(engine, CommandFrequencyAnalyzer):
            return engine.learn(data.get('interactions', []))
        elif isinstance(engine, ProactiveSuggestionEngine):
            return engine.learn(
                data.get('patterns', {}),
                {'command_patterns': getattr(self.engines.get('command_frequency'), 'command_patterns', {})},
                data.get('preferences', {})
            )
        elif isinstance(engine, FeedbackIncorporationEngine):
            # Feedback would come from a separate source
            return engine.learn([])
        else:
            return {'error': 'Unknown engine type'}
    
    def _generate_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights from all learning results."""
        insights = {}
        
        for engine_name, engine in self.engines.items():
            if engine.is_enabled() and engine_name in results:
                try:
                    insights[engine_name] = engine.get_insights()
                except Exception as e:
                    self.logger.warning(f"Failed to get insights from {engine_name}: {e}")
                    insights[engine_name] = {'error': str(e)}
        
        return insights
    
    def get_proactive_suggestions(self, context: str = "", max_suggestions: int = 3) -> List[Dict[str, Any]]:
        """Get proactive suggestions for the current context."""
        suggestion_engine = self.engines.get('suggestion_generation')
        if not suggestion_engine or not suggestion_engine.is_enabled():
            return []
        
        try:
            # Get contextual suggestions from memory system
            memory_suggestions = self.memory_system.get_contextual_suggestions(context, max_suggestions)
            
            # Combine with learning-based suggestions
            # This would typically use the latest learning results
            learning_suggestions = []
            
            return memory_suggestions + learning_suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to get proactive suggestions: {e}")
            return []
    
    def add_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Add user feedback for learning improvement."""
        feedback_engine = self.engines.get('feedback_incorporation')
        if not feedback_engine or not feedback_engine.is_enabled():
            return False
        
        try:
            result = feedback_engine.learn([feedback_data])
            return result.get('feedback_processed', 0) > 0
        except Exception as e:
            self.logger.error(f"Failed to add feedback: {e}")
            return False
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning module status."""
        return {
            'engines_enabled': [name for name, engine in self.engines.items() if engine.is_enabled()],
            'last_learning_run': self.last_learning_run.isoformat(),
            'next_scheduled_run': (self.last_learning_run + timedelta(hours=self.learning_interval_hours)).isoformat(),
            'learning_interval_hours': self.learning_interval_hours,
            'should_run_learning': self._should_run_learning()
        }


# Convenience function for creating learning module
def create_learning_module(config: Dict[str, Any], memory_system: MemorySystem) -> LearningModule:
    """
    Create and initialize a Learning Module instance.
    
    Args:
        config: Learning module configuration
        memory_system: Memory system instance
        
    Returns:
        Initialized LearningModule instance
    """
    return LearningModule(config, memory_system)