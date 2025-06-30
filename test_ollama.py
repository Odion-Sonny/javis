#!/usr/bin/env python3
import ollama
import time

def test_ollama():
    client = ollama.Client('http://localhost:11434')
    
    print("Testing Ollama connectivity...")
    models = client.list()
    print(f"Available models: {[m.model for m in models.models]}")
    
    print("\nTesting generation (this may take a while for first request)...")
    start_time = time.time()
    
    try:
        response = client.generate(
            model='llama2:latest',
            prompt='Hello, please respond with just "Hi there!"',
            stream=False,
            options={'num_predict': 10}  # Limit response length
        )
        
        end_time = time.time()
        print(f"Response: {response['response']}")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print("✅ Ollama is working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ollama()