#!/usr/bin/env python3
"""Simple test script for DeepSeek API."""

import asyncio
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_deepseek_api():
    """Test DeepSeek API directly."""
    print("🧪 Testing DeepSeek API")
    print("=" * 50)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment")
        return False
    
    print(f"✅ DeepSeek API key found: {api_key[:10]}...")
    
    try:
        # Create OpenAI client with DeepSeek endpoint
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        print("🤖 Client created successfully")
        
        # Test simple generation
        print("\n🚀 Testing simple generation...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a simple Python function that adds two numbers."}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        print("✅ Generation successful!")
        print(f"📊 Tokens used: {response.usage.total_tokens}")
        print(f"🤖 Model: {response.model}")
        print(f"📝 Response length: {len(response.choices[0].message.content)} characters")
        print("\n📄 Response preview:")
        print("-" * 30)
        content = response.choices[0].message.content
        print(content[:300] + "..." if len(content) > 300 else content)
        print("-" * 30)
        
        # Test test generation
        print("\n🧪 Testing test generation...")
        test_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
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
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        print("✅ Test generation successful!")
        print(f"📊 Tokens used: {test_response.usage.total_tokens}")
        test_content = test_response.choices[0].message.content
        print(f"📝 Response length: {len(test_content)} characters")
        print("\n🧪 Test code preview:")
        print("-" * 30)
        print(test_content[:400] + "..." if len(test_content) > 400 else test_content)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DeepSeek API: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

async def main():
    """Main test function."""
    print("🔬 DeepSeek API Test Suite")
    print("=" * 50)
    
    success = await test_deepseek_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! DeepSeek API is working correctly.")
    else:
        print("💥 Tests failed. Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
