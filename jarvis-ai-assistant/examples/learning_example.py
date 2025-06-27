#!/usr/bin/env python3
"""
Learning Module Example for Jarvis AI Assistant

This example demonstrates how to use the learning module's capabilities:
- User behavior pattern recognition
- Preference extraction from interactions
- Command frequency analysis  
- Proactive suggestion generation
- Feedback incorporation for improving responses
"""

import sys
import os
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.learning import create_learning_module, LearningModule
from jarvis.memory.memory_system import MemorySystem, InteractionType, PreferenceCategory


def setup_example_data():
    """Set up example memory system with sample data."""
    config = {
        'db_path': 'example_memory.db',
        'max_context_entries': 50,
        'max_context_tokens': 4000,
        'context_window_hours': 24,
        'pattern_learning_threshold': 2,
        'preference_confidence_threshold': 0.6
    }
    
    memory = MemorySystem(config)
    
    # Add sample conversations
    sample_interactions = [
        ("Hello Jarvis", "Hello! How can I help you today?", InteractionType.CONVERSATION),
        ("What's the weather like?", "I'd be happy to help with weather information.", InteractionType.QUESTION),
        ("Open my email", "I'll help you open your email application.", InteractionType.COMMAND),
        ("I prefer dark mode", "I'll remember that you prefer dark mode.", InteractionType.PREFERENCE_SETTING),
        ("Show me my calendar", "Here's your calendar information.", InteractionType.COMMAND),
        ("Can you help me schedule a meeting?", "I can help you schedule meetings.", InteractionType.TASK_REQUEST),
        ("Set a reminder for 3 PM", "I'll set a reminder for 3 PM.", InteractionType.COMMAND),
        ("I like shorter responses", "Noted. I'll keep responses concise.", InteractionType.PREFERENCE_SETTING),
        ("Search for Python tutorials", "Here are some Python tutorial results.", InteractionType.COMMAND),
        ("What time is it?", "The current time is 2:30 PM.", InteractionType.QUESTION),
        ("Open calculator", "Opening the calculator application.", InteractionType.COMMAND),
        ("I always check email in the morning", "I'll remember your morning email routine.", InteractionType.PREFERENCE_SETTING),
        ("Find my documents folder", "I'll help you locate your documents.", InteractionType.COMMAND),
        ("Create a new file", "Creating a new file for you.", InteractionType.COMMAND),
        ("What's my next appointment?", "Let me check your next appointment.", InteractionType.QUESTION)
    ]
    
    # Add interactions with timestamps spread over time
    base_time = datetime.now() - timedelta(days=7)
    for i, (user_input, assistant_response, interaction_type) in enumerate(sample_interactions):
        # Vary timestamps to simulate usage patterns
        timestamp = base_time + timedelta(hours=i * 2, minutes=i * 15)
        
        memory.store_conversation(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type=interaction_type,
            context_summary=f"Example interaction {i+1}",
            sentiment_score=0.7 + (i % 3) * 0.1,  # Vary sentiment
            confidence_score=0.8 + (i % 2) * 0.1,  # Vary confidence
            tokens_used=len(user_input.split()) + len(assistant_response.split()),
            response_time=0.5 + (i % 3) * 0.2
        )
    
    # Add some user preferences
    preferences = [
        ("interface_theme", "dark", PreferenceCategory.INTERFACE),
        ("response_length", "short", PreferenceCategory.BEHAVIOR),
        ("morning_routine", "check_email", PreferenceCategory.AUTOMATION),
        ("notification_sound", "soft_chime", PreferenceCategory.VOICE),
        ("auto_save", "enabled", PreferenceCategory.SYSTEM)
    ]
    
    for key, value, category in preferences:
        memory.learn_user_preference(
            key=key,
            value=value,
            category=category,
            confidence=0.8,
            context=f"Example preference: {key}"
        )
    
    return memory


def demonstrate_learning_module():
    """Demonstrate learning module capabilities."""
    print("🧠 Jarvis Learning Module Example")
    print("=" * 50)
    
    # Set up example data
    print("\n1. Setting up example data...")
    memory = setup_example_data()
    
    # Configure learning module
    learning_config = {
        'enabled': True,
        'learning_interval_hours': 1,  # Short interval for demo
        'pattern_recognition': {
            'enabled': True,
            'min_pattern_frequency': 2,
            'pattern_window_days': 7
        },
        'preference_extraction': {
            'enabled': True,
            'confidence_threshold': 0.6
        },
        'command_frequency': {
            'enabled': True,
            'analysis_window_days': 30,
            'min_frequency': 1
        },
        'suggestion_generation': {
            'enabled': True,
            'suggestion_threshold': 0.6,
            'max_suggestions': 5
        },
        'feedback_incorporation': {
            'enabled': True,
            'feedback_weight': 0.3,
            'improvement_threshold': 0.1
        }
    }
    
    # Create learning module
    print("2. Initializing learning module...")
    learning_module = create_learning_module(learning_config, memory)
    
    # Run learning cycle
    print("\n3. Running learning cycle...")
    result = learning_module.run_learning_cycle(force=True)
    
    print(f"✅ Learning Status: {result.get('status')}")
    print(f"📊 Engines Run: {', '.join(result.get('engines_run', []))}")
    
    # Display results from each engine
    results = result.get('results', {})
    insights = result.get('insights', {})
    
    print("\n4. Learning Results:")
    print("-" * 30)
    
    # Pattern Recognition Results
    if 'pattern_recognition' in results:
        pr_result = results['pattern_recognition']
        print(f"\n🔍 Pattern Recognition:")
        print(f"   • Patterns identified: {pr_result.get('patterns_identified', 0)}")
        print(f"   • Temporal patterns: {pr_result.get('temporal_patterns', 0)}")
        print(f"   • Sequence patterns: {pr_result.get('sequence_patterns', 0)}")
        print(f"   • Context patterns: {pr_result.get('context_patterns', 0)}")
    
    # Preference Extraction Results
    if 'preference_extraction' in results:
        pe_result = results['preference_extraction']
        print(f"\n🎯 Preference Extraction:")
        print(f"   • Preferences extracted: {pe_result.get('preferences_extracted', 0)}")
        if pe_result.get('preferences'):
            print("   • Sample preferences found:")
            for pref in pe_result['preferences'][:3]:
                print(f"     - {pref.get('key', 'Unknown')}: {pref.get('value', 'Unknown')} "
                      f"(confidence: {pref.get('confidence', 0):.2f})")
    
    # Command Frequency Results
    if 'command_frequency' in results:
        cf_result = results['command_frequency']
        print(f"\n📈 Command Frequency Analysis:")
        print(f"   • Commands analyzed: {cf_result.get('commands_analyzed', 0)}")
        print(f"   • Unique commands: {cf_result.get('unique_commands', 0)}")
        print(f"   • Patterns updated: {cf_result.get('patterns_updated', 0)}")
    
    # Suggestion Generation Results
    if 'suggestion_generation' in results:
        sg_result = results['suggestion_generation']
        print(f"\n💡 Suggestion Generation:")
        print(f"   • Suggestions generated: {sg_result.get('suggestions_generated', 0)}")
        print(f"   • Top suggestions: {sg_result.get('top_suggestions', 0)}")
        
        suggestions = sg_result.get('suggestions', [])
        if suggestions:
            print("   • Sample suggestions:")
            for suggestion in suggestions[:2]:
                print(f"     - {suggestion.get('suggestion_type', 'Unknown')}: "
                      f"{suggestion.get('content', 'No content')[:60]}...")
    
    # Display insights
    print("\n5. Learning Insights:")
    print("-" * 30)
    
    for engine_name, engine_insights in insights.items():
        if engine_insights and not engine_insights.get('error'):
            print(f"\n🔬 {engine_name.replace('_', ' ').title()}:")
            for key, value in engine_insights.items():
                if isinstance(value, (int, float)):
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, str) and len(value) < 50:
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, list) and len(value) <= 5:
                    print(f"   • {key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
    
    # Demonstrate proactive suggestions
    print("\n6. Getting Proactive Suggestions:")
    print("-" * 30)
    
    suggestions = learning_module.get_proactive_suggestions("morning routine", 3)
    if suggestions:
        print("💡 Proactive suggestions based on patterns:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion.get('content', 'No content')}")
    else:
        print("📝 No specific suggestions available yet - more data needed")
    
    # Demonstrate feedback incorporation
    print("\n7. Adding User Feedback:")
    print("-" * 30)
    
    sample_feedback = {
        'feedback_id': 'demo_feedback_1',
        'interaction_id': 'conv_1',
        'feedback_type': 'positive',
        'rating': 4,
        'comment': 'Great response time and accuracy',
        'specific_aspect': 'response_quality',
        'timestamp': datetime.now().isoformat()
    }
    
    feedback_added = learning_module.add_feedback(sample_feedback)
    print(f"✅ Feedback added successfully: {feedback_added}")
    
    # Get learning status
    print("\n8. Learning Module Status:")
    print("-" * 30)
    
    status = learning_module.get_learning_status()
    print(f"🔧 Enabled engines: {', '.join(status.get('engines_enabled', []))}")
    print(f"⏰ Last learning run: {status.get('last_learning_run')}")
    print(f"🔄 Should run learning: {status.get('should_run_learning', False)}")
    
    # Cleanup
    print("\n9. Cleaning up...")
    memory.close()
    
    # Remove example database
    try:
        os.remove('example_memory.db')
        print("✅ Example database cleaned up")
    except:
        pass
    
    print("\n🎉 Learning Module Demo Complete!")
    print("\nThe learning module can:")
    print("• 🧠 Recognize user behavior patterns")
    print("• 🎯 Extract preferences from natural language")
    print("• 📊 Analyze command frequency and trends")
    print("• 💡 Generate proactive suggestions")
    print("• 📈 Incorporate feedback for continuous improvement")
    print("• 🔧 Run autonomously on configurable schedules")


if __name__ == "__main__":
    demonstrate_learning_module()