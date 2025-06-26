"""
AI Integration Module
Handles communication with various AI service providers and intelligent processing.
"""

from .ai_brain import AIBrain, AIProvider, IntentType, ResponseTone, AIResponse, create_ai_brain

__all__ = ["AIBrain", "AIProvider", "IntentType", "ResponseTone", "AIResponse", "create_ai_brain"]