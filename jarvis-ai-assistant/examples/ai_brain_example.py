#!/usr/bin/env python3
"""
Example usage of the AI Brain module.
Demonstrates various features including provider fallback, context management, and intent recognition.
"""

import asyncio
import json
import logging
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.ai_integration import AIBrain, AIProvider, IntentType, ResponseTone


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_example_config() -> dict:
    """Get example configuration for AI Brain."""
    return {
        'primary_provider': 'ollama',
        'fallback_providers': ['openai', 'mock'],
        'context_window': 10,
        
        # Ollama configuration
        'ollama': {
            'model': 'llama2',  # or 'mistral', 'codellama', etc.
            'base_url': 'http://localhost:11434',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        
        # OpenAI configuration (optional fallback)
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY'),  # Set this environment variable
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        
        # Mock provider (always available for development)
        'mock': {
            'mock_responses': {
                'hello': 'Hello! How can I help you today?',
                'time': 'Let me check the current time for you.',
                'weather': 'I can help you set up weather integration!'
            }
        },
        
        # Custom system prompt
        'system_prompt': """You are Jarvis, an advanced AI assistant. You are:
- Helpful and knowledgeable
- Able to assist with system operations, coding, and general questions
- Conversational but professional
- Capable of understanding context and intent
- Focused on providing accurate and useful responses

Please be concise but thorough in your responses."""
    }


async def basic_example():
    """Basic usage example."""
    print("=" * 60)
    print("Basic AI Brain Example")
    print("=" * 60)
    
    # Initialize AI Brain
    config = get_example_config()
    brain = AIBrain(config)
    
    # Test messages
    test_messages = [
        "Hello Jarvis, how are you?",
        "What time is it?",
        "Can you help me open a file?",
        "Run the command 'ls -la'",
        "What's the weather like today?",
        "Goodbye!"
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        
        try:
            response = await brain.process_message(message)
            
            print(f"🤖 Jarvis: {response.content}")
            print(f"   Intent: {response.intent.value}")
            print(f"   Tone: {response.tone.value}")
            print(f"   Provider: {response.provider.value} ({response.model})")
            print(f"   Confidence: {response.confidence:.2f}")
            print(f"   Response time: {response.response_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Print conversation summary
    print("\n" + "=" * 60)
    print("Conversation Summary")
    print("=" * 60)
    summary = brain.get_conversation_summary()
    print(json.dumps(summary, indent=2))


async def provider_status_example():
    """Example showing provider status and fallback."""
    print("\n" + "=" * 60)
    print("Provider Status Example")
    print("=" * 60)
    
    config = get_example_config()
    brain = AIBrain(config)
    
    # Check provider status
    status = brain.get_provider_status()
    print("Provider Status:")
    for provider, info in status.items():
        available = "✅" if info['available'] else "❌"
        print(f"  {available} {provider}: {info['model_info']}")
    
    # Test with a message to see which provider is used
    print(f"\nTesting with primary provider: {brain.primary_provider.value}")
    response = await brain.process_message("Tell me about yourself")
    print(f"Response from: {response.provider.value} ({response.model})")


async def context_management_example():
    """Example showing context management."""
    print("\n" + "=" * 60)
    print("Context Management Example")
    print("=" * 60)
    
    config = get_example_config()
    brain = AIBrain(config)
    
    # Set user preferences
    brain.set_context_preference('preferred_tone', 'casual')
    brain.set_context_preference('programming_language', 'python')
    
    # Have a contextual conversation
    messages = [
        "My name is Alice",
        "What's my name?",
        "I prefer casual communication",
        "Remember that I work with Python",
        "What programming language do I use?"
    ]
    
    for message in messages:
        print(f"\n👤 User: {message}")
        response = await brain.process_message(message)
        print(f"🤖 Jarvis: {response.content}")
    
    # Show preferences
    print(f"\nStored preferences:")
    print(f"  Preferred tone: {brain.get_context_preference('preferred_tone')}")
    print(f"  Programming language: {brain.get_context_preference('programming_language')}")


async def command_parsing_example():
    """Example showing command parsing."""
    print("\n" + "=" * 60)
    print("Command Parsing Example")
    print("=" * 60)
    
    config = get_example_config()
    brain = AIBrain(config)
    
    # Test command parsing
    test_commands = [
        "open calculator",
        "run python script.py",
        "search for config files",
        "find all .txt files",
        "create a new folder",
        "delete old logs",
        "move file.txt to backup folder",
        "copy data.csv to reports directory"
    ]
    
    for command in test_commands:
        parsed_command, params = brain.parse_command(command)
        print(f"'{command}' -> Command: '{parsed_command}', Params: {params}")


async def error_handling_example():
    """Example showing error handling."""
    print("\n" + "=" * 60)
    print("Error Handling Example")
    print("=" * 60)
    
    # Create config with invalid settings to test error handling
    config = {
        'primary_provider': 'ollama',
        'fallback_providers': ['openai', 'mock'],
        'ollama': {
            'model': 'nonexistent-model',
            'base_url': 'http://invalid-url:11434'
        },
        'openai': {
            'api_key': 'invalid-key',
            'model': 'gpt-3.5-turbo'
        }
    }
    
    brain = AIBrain(config)
    
    # This should fall back to mock provider
    print("Testing with invalid providers (should fall back to mock)...")
    response = await brain.process_message("Hello, this is a test message")
    print(f"Response from: {response.provider.value}")
    print(f"Content: {response.content}")


async def main():
    """Run all examples."""
    print("🚀 AI Brain Module Examples")
    print("This demonstrates the capabilities of the AI Brain module")
    
    try:
        await basic_example()
        await provider_status_example()
        await context_management_example()
        await command_parsing_example()
        await error_handling_example()
        
    except KeyboardInterrupt:
        print("\n\n👋 Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())