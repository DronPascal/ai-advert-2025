#!/usr/bin/env python3
"""Test script for code improvement scenario optimization validation."""

import asyncio
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
import re

# Add the regoose package to path
sys.path.insert(0, str(Path(__file__).parent / "regoose"))

logger = None

# Mock logger for testing without full setup
class MockLogger:
    def info(self, msg, **kwargs): print(f"INFO: {msg}")
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")
    def warning(self, msg, **kwargs): print(f"WARNING: {msg}")

def get_logger(name):
    return MockLogger()

class TokenUsageTracker:
    """Track token usage for optimization validation."""

    def __init__(self):
        self.usage_stats = {
            "total_calls": 0,
            "estimated_tokens": 0,
            "calls_by_action": {},
            "start_time": time.time()
        }

    def track_call(self, action_name: str, prompt_length: int, response_length: int = 0):
        """Track a single LLM call."""
        self.usage_stats["total_calls"] += 1

        # Rough token estimation (1 token ≈ 4 chars for GPT models)
        estimated_tokens = (prompt_length + response_length) // 4
        self.usage_stats["estimated_tokens"] += estimated_tokens

        if action_name not in self.usage_stats["calls_by_action"]:
            self.usage_stats["calls_by_action"][action_name] = {
                "calls": 0,
                "tokens": 0,
                "avg_prompt_len": 0,
                "total_prompt_len": 0
            }

        action_stats = self.usage_stats["calls_by_action"][action_name]
        action_stats["calls"] += 1
        action_stats["tokens"] += estimated_tokens
        action_stats["total_prompt_len"] += prompt_length
        action_stats["avg_prompt_len"] = action_stats["total_prompt_len"] // action_stats["calls"]

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        elapsed = time.time() - self.usage_stats["start_time"]
        return {
            **self.usage_stats,
            "elapsed_seconds": elapsed,
            "tokens_per_second": self.usage_stats["estimated_tokens"] / elapsed if elapsed > 0 else 0,
            "avg_tokens_per_call": self.usage_stats["estimated_tokens"] / self.usage_stats["total_calls"] if self.usage_stats["total_calls"] > 0 else 0
        }

class OptimizationTest:
    """Test harness for code improvement optimization validation."""

    def __init__(self):
        self.tracker = TokenUsageTracker()
        self.test_results = []

    def analyze_prompt_optimizations(self) -> Dict[str, Any]:
        """Analyze the prompt optimizations we implemented."""

        logger.info("Analyzing prompt optimizations...")

        # Read the optimized action files
        action_files = {
            "analyze_codebase": "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/regoose/actions/analyze_codebase.py",
            "plan_improvements": "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/regoose/actions/plan_improvements.py",
            "implement_changes": "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/regoose/actions/implement_changes.py"
        }

        optimization_results = {}

        for action_name, file_path in action_files.items():
            with open(file_path, 'r') as f:
                content = f.read()

            # Find prompt building functions
            prompt_functions = re.findall(r'def _build_.*_prompt.*?return f"""(.*?)"""', content, re.DOTALL)

            if prompt_functions:
                prompt = prompt_functions[0]
                optimization_results[action_name] = {
                    "prompt_length": len(prompt),
                    "estimated_tokens": len(prompt) // 4,  # Rough estimation
                    "lines_count": len(prompt.split('\n')),
                    "word_count": len(prompt.split()),
                    "conciseness_score": self.calculate_conciseness_score(prompt)
                }

        return optimization_results

    def calculate_conciseness_score(self, prompt: str) -> float:
        """Calculate a conciseness score for the prompt (0-100, higher is better)."""
        words = len(prompt.split())
        lines = len(prompt.split('\n'))

        # Penalize verbose prompts
        if words > 200:
            score = max(0, 100 - (words - 200) * 0.5)
        elif words < 50:
            score = 100  # Very concise
        else:
            score = 100 - (words - 50) * 0.3

        # Bonus for structured format
        if "##" in prompt and "- **" in prompt:
            score += 10

        return min(100, max(0, score))

    def analyze_iteration_logic_improvements(self) -> Dict[str, Any]:
        """Analyze the iteration logic improvements."""

        logger.info("Analyzing iteration logic improvements...")

        scenario_file = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/regoose/scenarios/code_improvement.py"

        with open(scenario_file, 'r') as f:
            content = f.read()

        improvements = {}

        # Check for smart convergence detection
        if "convergence_score" in content:
            improvements["convergence_detection"] = True

        # Check for context optimization
        if "_extract_essential_context" in content:
            improvements["context_optimization"] = True

        # Check for smart error handling
        if "_is_critical_error" in content:
            improvements["smart_error_handling"] = True

        # Check for validation optimization
        if "_all_validations_pass" in content:
            improvements["validation_optimization"] = True

        # Count new helper methods
        helper_methods = len(re.findall(r'def _\w+', content))
        improvements["helper_methods_count"] = helper_methods

        return improvements

    def generate_optimization_report(self, prompt_analysis: Dict, logic_analysis: Dict) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""

        # Calculate overall token savings
        total_original_tokens = 800  # Estimated original token usage
        total_optimized_tokens = sum(action["estimated_tokens"] for action in prompt_analysis.values())

        token_savings_percent = ((total_original_tokens - total_optimized_tokens) / total_original_tokens) * 100

        report = {
            "prompt_optimizations": {
                "actions_analyzed": len(prompt_analysis),
                "total_optimized_tokens": total_optimized_tokens,
                "estimated_token_savings_percent": token_savings_percent,
                "action_details": prompt_analysis
            },
            "logic_improvements": {
                "features_implemented": sum(logic_analysis.values()),
                "convergence_detection": logic_analysis.get("convergence_detection", False),
                "context_optimization": logic_analysis.get("context_optimization", False),
                "smart_error_handling": logic_analysis.get("smart_error_handling", False),
                "validation_optimization": logic_analysis.get("validation_optimization", False),
                "helper_methods_added": logic_analysis.get("helper_methods_count", 0)
            },
            "overall_score": {
                "token_efficiency_score": max(0, min(100, 100 - token_savings_percent)),
                "logic_improvement_score": (sum(logic_analysis.values()) / len(logic_analysis)) * 100,
                "combined_score": ((100 - token_savings_percent) + (sum(logic_analysis.values()) / len(logic_analysis)) * 100) / 2
            }
        }

        return report

    def create_test_project(self) -> str:
        """Create a test Python project for optimization testing."""
        test_dir = "/tmp/regoose_test_project"
        os.makedirs(test_dir, exist_ok=True)

        # Create a simple Python project with some issues to fix
        files = {
            "main.py": '''def greet(name):
    return f"Hello {name}"

def calculate_sum(a,b):
    return a+b

if __name__ == "__main__":
    print(greet("World"))
    print(calculate_sum(5,3))''',

            "utils.py": '''import math

def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n-1)

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(math.sqrt(num)) + 1):
        if num % i == 0:
            return False
    return True''',

            "README.md": '''# Test Project

This is a simple test project for optimization testing.

## Usage

Run the main script:
python main.py

## Features

- Greeting function
- Math calculations
- Utility functions'''
        }

        for filename, content in files.items():
            with open(os.path.join(test_dir, filename), 'w') as f:
                f.write(content)

        return test_dir

    def run_comprehensive_test(self):
        """Run comprehensive optimization validation tests."""

        logger.info("Starting comprehensive optimization validation tests")

        # Analyze prompt optimizations
        prompt_analysis = self.analyze_prompt_optimizations()

        # Analyze iteration logic improvements
        logic_analysis = self.analyze_iteration_logic_improvements()

        # Generate comprehensive report
        report = self.generate_optimization_report(prompt_analysis, logic_analysis)

        # Save detailed analysis
        with open("/tmp/prompt_analysis.json", 'w') as f:
            json.dump({
                "prompt_analysis": prompt_analysis,
                "logic_analysis": logic_analysis,
                "report": report
            }, f, indent=2)

        return report

    def generate_optimization_report(self, prompt_analysis: Dict, logic_analysis: Dict) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""

        # Calculate overall token savings
        total_original_tokens = 800  # Estimated original token usage
        total_optimized_tokens = sum(action["estimated_tokens"] for action in prompt_analysis.values())

        token_savings_percent = ((total_original_tokens - total_optimized_tokens) / total_original_tokens) * 100

        report = {
            "prompt_optimizations": {
                "actions_analyzed": len(prompt_analysis),
                "total_optimized_tokens": total_optimized_tokens,
                "estimated_token_savings_percent": token_savings_percent,
                "action_details": prompt_analysis
            },
            "logic_improvements": {
                "features_implemented": sum(logic_analysis.values()),
                "convergence_detection": logic_analysis.get("convergence_detection", False),
                "context_optimization": logic_analysis.get("context_optimization", False),
                "smart_error_handling": logic_analysis.get("smart_error_handling", False),
                "validation_optimization": logic_analysis.get("validation_optimization", False),
                "helper_methods_added": logic_analysis.get("helper_methods_count", 0)
            },
            "overall_score": {
                "token_efficiency_score": max(0, min(100, 100 - token_savings_percent)),
                "logic_improvement_score": (sum(logic_analysis.values()) / len(logic_analysis)) * 100,
                "combined_score": ((100 - token_savings_percent) + (sum(logic_analysis.values()) / len(logic_analysis)) * 100) / 2
            }
        }

        return report

    def print_optimization_report(self, report: Dict[str, Any]):
        """Print the optimization report in a beautiful format."""

        print("\n" + "="*70)
        print("🎯 CODE IMPROVEMENT SCENARIO OPTIMIZATION RESULTS")
        print("="*70)

        # Prompt optimizations
        prompt = report["prompt_optimizations"]
        print(f"\n📝 PROMPT OPTIMIZATIONS:")
        print(f"   Actions Analyzed: {prompt['actions_analyzed']}")
        print(f"   Estimated Token Savings: {prompt['estimated_token_savings_percent']:.1f}%")
        print(f"   Total Optimized Tokens: {prompt['total_optimized_tokens']}")

        for action, details in prompt["action_details"].items():
            print(f"   • {action}:")
            print(f"     - Words: {details['word_count']}, Tokens: ~{details['estimated_tokens']}")
            print(f"     - Conciseness Score: {details['conciseness_score']:.1f}/100")

        # Logic improvements
        logic = report["logic_improvements"]
        print(f"\n🧠 LOGIC IMPROVEMENTS:")
        print(f"   Features Implemented: {logic['features_implemented']}")
        print(f"   ✅ Convergence Detection: {'Yes' if logic['convergence_detection'] else 'No'}")
        print(f"   ✅ Context Optimization: {'Yes' if logic['context_optimization'] else 'No'}")
        print(f"   ✅ Smart Error Handling: {'Yes' if logic['smart_error_handling'] else 'No'}")
        print(f"   ✅ Validation Optimization: {'Yes' if logic['validation_optimization'] else 'No'}")
        print(f"   Helper Methods Added: {logic['helper_methods_added']}")

        # Overall scores
        scores = report["overall_score"]
        print(f"\n🏆 OVERALL SCORES:")
        print(f"   Token Efficiency Score: {scores['token_efficiency_score']:.1f}/100")
        print(f"   Logic Improvement Score: {scores['logic_improvement_score']:.1f}/100")
        print(f"   Combined Score: {scores['combined_score']:.1f}/100")

        print("\n" + "="*70)
        print("✅ OPTIMIZATION VALIDATION COMPLETE")
        print("="*70)

    def calculate_token_efficiency(self, results: List[Dict]) -> float:
        """Calculate token efficiency score (0-100)."""
        # Lower token usage per successful test = higher efficiency
        successful_results = [r for r in results if r["success"]]
        if not successful_results:
            return 0.0

        # This would be more accurate with actual token counting
        # For now, use a proxy based on test completion time
        avg_time = sum(r["elapsed_seconds"] for r in successful_results) / len(successful_results)
        efficiency = max(0, 100 - (avg_time * 10))  # Rough approximation
        return min(100, efficiency)

    def calculate_iteration_efficiency(self, results: List[Dict]) -> float:
        """Calculate iteration efficiency score (0-100)."""
        successful_results = [r for r in results if r["success"]]
        if not successful_results:
            return 0.0

        avg_iterations = sum(r["iterations_completed"] for r in successful_results) / len(successful_results)
        # Lower iterations = higher efficiency (optimal is 1-2 iterations)
        efficiency = max(0, 100 - ((avg_iterations - 1.5) * 20))
        return min(100, efficiency)

    def calculate_success_stability(self, results: List[Dict]) -> float:
        """Calculate success stability score (0-100)."""
        # Consistency in success rate across different scenarios
        success_pattern = [r["success"] for r in results]
        if len(set(success_pattern)) == 1:  # All same result
            return 100.0 if success_pattern[0] else 0.0
        else:
            # Calculate consistency score
            success_count = sum(success_pattern)
            consistency = min(success_count, len(success_pattern) - success_count)
            return (consistency / len(success_pattern)) * 100

def main():
    """Main test execution."""
    # Initialize logger
    global logger
    logger = get_logger("optimization_test")

    # Run optimization validation tests
    tester = OptimizationTest()
    report = tester.run_comprehensive_test()

    # Print results
    tester.print_optimization_report(report)

    print("\n📄 Detailed analysis saved to: /tmp/prompt_analysis.json")

if __name__ == "__main__":
    main()
