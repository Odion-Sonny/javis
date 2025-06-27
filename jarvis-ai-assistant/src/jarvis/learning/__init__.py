"""
Learning Module Package for Jarvis AI Assistant

This package provides intelligent learning capabilities including:
- User behavior pattern recognition
- Preference extraction from interactions  
- Command frequency analysis
- Proactive suggestion generation
- Feedback incorporation for improving responses

The module is designed to be modular and extensible for future enhancements.
"""

from .learning_module import (
    LearningModule,
    BaseLearningEngine,
    PatternRecognitionEngine,
    PreferenceExtractionEngine,
    CommandFrequencyAnalyzer,
    ProactiveSuggestionEngine,
    FeedbackIncorporationEngine,
    UserBehaviorPattern,
    CommandPattern,
    ProactiveSuggestion,
    FeedbackData,
    LearningType,
    PatternConfidence,
    create_learning_module
)

__all__ = [
    'LearningModule',
    'BaseLearningEngine',
    'PatternRecognitionEngine', 
    'PreferenceExtractionEngine',
    'CommandFrequencyAnalyzer',
    'ProactiveSuggestionEngine',
    'FeedbackIncorporationEngine',
    'UserBehaviorPattern',
    'CommandPattern', 
    'ProactiveSuggestion',
    'FeedbackData',
    'LearningType',
    'PatternConfidence',
    'create_learning_module'
]