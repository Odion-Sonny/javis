#!/usr/bin/env python3
"""
Test script to check the real Ollama behavior and understand why fallback occurs.
"""

import asyncio
import logging
import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_direct_ollama():
    """Test Ollama directly without the AI Brain wrapper."""
    print("=" * 80)
    print("TESTING DIRECT OLLAMA CONNECTION")
    print("=" * 80)
    
    try:
        # Test with aiohttp directly to Ollama
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test if Ollama is responding
            print("1. Testing Ollama API availability...")
            async with session.get('http://localhost:11434/api/tags') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Ollama API is responding")
                    print(f"Available models: {[m['name'] for m in data.get('models', [])]}")
                else:
                    print(f"❌ Ollama API returned status: {response.status}")
                    return
            
            # Test chat completion
            print("\n2. Testing Ollama chat completion...")
            payload = {
                'model': 'llama2',
                'messages': [{'role': 'user', 'content': 'Hello, respond with just "Ollama working"'}],
                'stream': False
            }
            
            async with session.post(
                'http://localhost:11434/api/chat',
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Chat completion successful")
                    print(f"Response: {data.get('message', {}).get('content', 'No content')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Chat completion failed: {response.status}")
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Direct Ollama test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_ollama_provider_directly():
    """Test the OllamaProvider class directly."""
    print("\n" + "=" * 80)
    print("TESTING OLLAMA PROVIDER CLASS")
    print("=" * 80)
    
    try:
        # We need to import ollama package or simulate it
        print("1. Testing without ollama package...")
        
        from jarvis.ai_integration.ai_brain import OllamaProvider
        
        config = {
            'model': 'llama2',
            'base_url': 'http://localhost:11434',
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        provider = OllamaProvider(config)
        print(f"Provider initialized: {provider is not None}")
        print(f"Client available: {provider.client is not None}")
        print(f"Is available: {provider.is_available()}")
        
        if provider.is_available():
            print("\n2. Testing generate_response...")
            messages = [{'role': 'user', 'content': 'Say hello'}]
            try:
                response = await provider.generate_response(messages)
                print(f"✅ Generation successful: {response.provider.value}")
                print(f"Content: {response.content[:100]}...")
            except Exception as e:
                print(f"❌ Generation failed: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        import traceback
        traceback.print_exc()

async def debug_ai_brain_with_ollama():
    """Debug the AI Brain with detailed logging."""
    print("\n" + "=" * 80)
    print("DEBUGGING AI BRAIN WITH OLLAMA")
    print("=" * 80)
    
    try:
        from jarvis.ai_integration.ai_brain import AIBrain
        
        config = {
            'primary_provider': 'ollama',
            'fallback_providers': ['mock'],
            'ollama': {
                'model': 'llama2',
                'base_url': 'http://localhost:11434',
                'temperature': 0.7,
                'max_tokens': 100
            },
            'mock': {}
        }
        
        brain = AIBrain(config)
        
        # Check detailed status
        print("Provider initialization status:")
        for provider_type, provider in brain.providers.items():
            print(f"  {provider_type.value}: {type(provider).__name__}")
            print(f"    Available: {provider.is_available()}")
            if hasattr(provider, 'client'):
                print(f"    Client: {provider.client}")
        
        print(f"\nPrimary provider: {brain.primary_provider.value}")
        print(f"Fallback providers: {[p.value for p in brain.fallback_providers]}")
        
        # Test message processing with detailed tracing
        print("\n3. Processing test message...")
        try:
            response = await brain.process_message("Hello, just say 'working'")
            print(f"✅ Response received from: {response.provider.value}")
            print(f"Content: {response.content}")
        except Exception as e:
            print(f"❌ Message processing failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ AI Brain debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_ollama())
    asyncio.run(test_ollama_provider_directly())
    asyncio.run(debug_ai_brain_with_ollama())