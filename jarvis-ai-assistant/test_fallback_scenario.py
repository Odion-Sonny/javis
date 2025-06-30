#!/usr/bin/env python3
"""
Test script to simulate the fallback behavior scenario.
This simulates what happens when Ollama is available but fails during generation.
"""

import asyncio
import logging
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jarvis.ai_integration.ai_brain import AIBrain, OllamaProvider, MockProvider, AIProvider
from unittest.mock import Mock, patch

# Configure logging to see the exact flow
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockOllamaProvider(OllamaProvider):
    """Mock Ollama provider that simulates availability but generation failure."""
    
    def __init__(self, config):
        super().__init__(config)
        # Override the client to simulate availability
        self.client = Mock()
        
    def is_available(self) -> bool:
        """Simulate that Ollama is available."""
        return True
        
    async def generate_response(self, messages, **kwargs):
        """Simulate a failure during generation."""
        print("🔴 SIMULATING: Ollama generation attempt...")
        # Simulate different types of failures
        raise Exception("Connection refused: Ollama server not responding")

async def test_fallback_scenario():
    """Test the exact fallback scenario."""
    print("=" * 80)
    print("TESTING FALLBACK SCENARIO")
    print("=" * 80)
    
    # Create config
    config = {
        'primary_provider': 'ollama',
        'fallback_providers': ['openai', 'mock'],
        'ollama': {
            'model': 'llama2',
            'base_url': 'http://localhost:11434',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        'openai': {
            'api_key': None,  # No API key to force fallback
            'model': 'gpt-3.5-turbo'
        },
        'mock': {}
    }
    
    # Create AI Brain
    brain = AIBrain(config)
    
    # Replace the Ollama provider with our mock that simulates availability but failure
    brain.providers[AIProvider.OLLAMA] = MockOllamaProvider(config['ollama'])
    
    print(f"Primary provider: {brain.primary_provider.value}")
    print(f"Fallback providers: {[p.value for p in brain.fallback_providers]}")
    
    # Check provider status
    status = brain.get_provider_status()
    print("Provider Status:")
    for provider, info in status.items():
        available = "✅" if info['available'] else "❌"
        print(f"  {available} {provider}")
    
    print("\n" + "=" * 80)
    print("TESTING MESSAGE PROCESSING")
    print("=" * 80)
    
    # Test message processing
    try:
        response = await brain.process_message("Hello, test the fallback mechanism")
        print(f"✅ Final response from: {response.provider.value}")
        print(f"Content: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def analyze_code_flow():
    """Analyze the exact code flow in _generate_with_fallback."""
    print("\n" + "=" * 80)
    print("CODE FLOW ANALYSIS")
    print("=" * 80)
    
    print("In _generate_with_fallback method:")
    print("1. Lines 685-692: Try primary provider (Ollama)")
    print("   - Checks if provider exists in self.providers")
    print("   - Calls provider.is_available() - this returns True")
    print("   - Calls provider.generate_response(messages)")
    print("   - If exception occurs, logs warning and continues")
    print("")
    print("2. Lines 694-703: Try fallback providers")
    print("   - Iterates through fallback_providers list")
    print("   - For each provider, checks availability")
    print("   - Logs 'Using fallback provider: {name}' at line 700")
    print("   - Calls generate_response()")
    print("")
    print("3. The key issue:")
    print("   - Ollama shows as 'available' during is_available() check")
    print("   - But fails during actual generate_response() call")
    print("   - This causes fallback to mock provider")
    print("   - Hence the log message: 'Using fallback provider: mock'")

if __name__ == "__main__":
    asyncio.run(test_fallback_scenario())
    asyncio.run(analyze_code_flow())