#!/usr/bin/env python3
"""Test script for DeepSeek provider."""

import asyncio
import os
from pathlib import Path

# Add the regoose package to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from regoose.providers.deepseek_provider import DeepSeekProvider
from regoose.core.config import get_settings


async def test_deepseek_provider():
    """Test DeepSeek provider functionality."""
    print("🧪 Testing DeepSeek Provider")
    print("=" * 50)
    
    try:
        # Get settings
        settings = get_settings()
        
        if not settings.deepseek_api_key:
            print("❌ DEEPSEEK_API_KEY not found in environment")
            print("Please set DEEPSEEK_API_KEY in your .env file")
            return False
        
        print(f"✅ DeepSeek API key found")
        print(f"📝 Model: {settings.deepseek_model}")
        
        # Create provider
        provider = DeepSeekProvider(
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
            max_tokens=settings.deepseek_max_tokens
        )
        
        print(f"🤖 Provider created: {provider.get_model_name()}")
        print(f"🔢 Max tokens: {provider.get_max_tokens()}")
        
        # Test simple generation
        print("\n🚀 Testing simple generation...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a simple Python function that adds two numbers."}
        ]
        
        response = await provider.generate(messages)
        
        print("✅ Generation successful!")
        print(f"📊 Tokens used: {response.tokens_used}")
        print(f"🤖 Model: {response.model}")
        print(f"📝 Response length: {len(response.content)} characters")
        print("\n📄 Response preview:")
        print("-" * 30)
        print(response.content[:200] + "..." if len(response.content) > 200 else response.content)
        print("-" * 30)
        
        # Test test generation
        print("\n🧪 Testing test generation...")
        test_messages = [
            {"role": "system", "content": "You are an expert test generator. Generate comprehensive unit tests for the given code."},
            {"role": "user", "content": """
Generate unit tests for this Python function:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

Please provide complete test code with imports and test cases.
"""}
        ]
        
        test_response = await provider.generate(test_messages)
        
        print("✅ Test generation successful!")
        print(f"📊 Tokens used: {test_response.tokens_used}")
        print(f"📝 Response length: {len(test_response.content)} characters")
        print("\n🧪 Test code preview:")
        print("-" * 30)
        print(test_response.content[:300] + "..." if len(test_response.content) > 300 else test_response.content)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DeepSeek provider: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    print("🔬 DeepSeek Provider Test Suite")
    print("=" * 50)
    
    success = await test_deepseek_provider()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! DeepSeek provider is working correctly.")
    else:
        print("💥 Tests failed. Please check the error messages above.")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
