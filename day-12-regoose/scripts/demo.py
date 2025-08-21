#!/usr/bin/env python3
"""Demo script for Regoose test generation agent."""

import asyncio
import tempfile
from pathlib import Path

from regoose.core.agent import RegooseAgent
from regoose.core.config import Settings
from regoose.providers.openai_provider import OpenAIProvider


# Example code samples for testing
EXAMPLE_CODES = {
    "fibonacci": '''
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number recursively."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
''',
    
    "calculator": '''
class Calculator:
    """Simple calculator class."""
    
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
''',
    
    "user_manager": '''
from typing import List, Optional

class User:
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.is_active = True

class UserManager:
    def __init__(self):
        self.users: List[User] = []
    
    def add_user(self, user: User) -> bool:
        if any(u.user_id == user.user_id for u in self.users):
            return False
        self.users.append(user)
        return True
    
    def get_user(self, user_id: int) -> Optional[User]:
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None
    
    def deactivate_user(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if user:
            user.is_active = False
            return True
        return False
'''
}


async def run_demo():
    """Run a demo of Regoose capabilities."""
    print("🚀 Regoose Demo - AI Test Generation Agent")
    print("=" * 50)
    
    try:
        # Initialize settings (this will fail if no API key is set)
        settings = Settings(
            openai_api_key="demo-key",  # This should be set in .env
            openai_model="gpt-4o-mini",
            container_runtime="podman",
            debug=True
        )
        
        # Initialize LLM provider
        llm_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        
        # Initialize agent
        agent = RegooseAgent(llm_provider, settings)
        
        print("\\n📝 Available example codes:")
        for i, (name, _) in enumerate(EXAMPLE_CODES.items(), 1):
            print(f"{i}. {name}")
        
        # For demo, use fibonacci example
        example_name = "fibonacci"
        example_code = EXAMPLE_CODES[example_name]
        
        print(f"\\n🔍 Testing with {example_name} example:")
        print("-" * 30)
        print(example_code)
        print("-" * 30)
        
        # Generate tests
        print("\\n🤖 Generating tests with AI...")
        tests, analysis = await agent.analyze_and_generate_tests(
            code=example_code,
            language="python"
        )
        
        print(f"\\n📊 Analysis: {analysis}")
        print(f"\\n📝 Generated {len(tests)} test file(s):")
        for filename in tests.keys():
            print(f"  - {filename}")
        
        # Display generated tests
        print("\\n📋 Generated test content:")
        for filename, content in tests.items():
            print(f"\\n--- {filename} ---")
            print(content)
            print("-" * 40)
        
        # Run tests
        print("\\n🐳 Running tests in container...")
        results = await agent.run_tests_in_container(tests)
        
        # Display results
        print("\\n📊 Test Results:")
        for result in results:
            print(f"  File: {result.test_file}")
            print(f"  Passed: {result.passed}")
            print(f"  Failed: {result.failed}")
            print(f"  Errors: {result.errors}")
            print(f"  Duration: {result.duration:.2f}s")
        
        # Generate report
        print("\\n📄 Generating report...")
        report = await agent.generate_report(tests, results)
        
        # Save report to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(report)
            report_path = f.name
        
        print(f"\\n✅ Demo complete! Report saved to: {report_path}")
        print("\\n🎯 Summary:")
        total_tests = sum(r.passed + r.failed + r.errors for r in results)
        total_passed = sum(r.passed for r in results)
        print(f"  - Generated {len(tests)} test files")
        print(f"  - Executed {total_tests} tests")
        print(f"  - Passed: {total_passed}/{total_tests}")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Demo failed: {str(e)}")
        print("\\n💡 Make sure you have:")
        print("  1. Set up your OpenAI API key (.env file)")
        print("  2. Installed dependencies (pip install -e .)")
        print("  3. Container runtime available (podman/docker)")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_demo())
    exit(0 if success else 1)
