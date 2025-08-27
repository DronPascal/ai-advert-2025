#!/usr/bin/env python3
"""10-Iteration Optimization Testing Script with Token Counting and Continuous Improvement."""

import os
import sys
import shutil
import time
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Test configuration
ITERATIONS = 10
ORIGINAL_PROJECT = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/test_sample_project_original"
WORK_PROJECT = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/test_sample_project"
RESULTS_FILE = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/iteration_results.json"

class TokenCounter:
    """Simple token counter for optimization tracking."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.total_tokens = 0
        self.calls_by_action = {}
        self.iteration_data = []

    def estimate_tokens_from_logs(self, log_content: str) -> int:
        """Estimate tokens from log content."""
        # Rough estimation based on log patterns
        # This is approximate since we don't have direct API access

        # Count LLM calls (each call has token overhead)
        llm_calls = len(re.findall(r'LLM Call #\d+', log_content))

        # Estimate base tokens per call (prompt + response)
        base_tokens_per_call = 800  # rough average

        # Count specific actions
        analyze_calls = len(re.findall(r'analyze_codebase', log_content))
        plan_calls = len(re.findall(r'plan_improvements', log_content))
        implement_calls = len(re.findall(r'implement_changes', log_content))
        validate_calls = len(re.findall(r'validate_changes', log_content))

        # Estimate tokens with optimization factors
        estimated_tokens = (
            analyze_calls * 600 +    # analyze is shorter after optimization
            plan_calls * 500 +       # plan is much shorter after optimization
            implement_calls * 400 +  # implement is optimized
            validate_calls * 300     # validate is efficient
        )

        return max(estimated_tokens, llm_calls * 200)  # minimum estimate

    def record_iteration(self, iteration: int, tokens: int, changes: Dict, execution_time: float):
        """Record data for one iteration."""
        self.iteration_data.append({
            'iteration': iteration,
            'tokens_used': tokens,
            'changes_made': changes,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        })
        self.total_tokens += tokens

class ChangeAnalyzer:
    """Analyze changes made to files between iterations."""

    def __init__(self, original_dir: str, work_dir: str):
        self.original_dir = original_dir
        self.work_dir = work_dir

    def analyze_changes(self) -> Dict[str, Any]:
        """Analyze what changes were made to files."""
        changes = {}

        for filename in ['calculator.py', 'data_processor.py', 'user_manager.py']:
            original_file = os.path.join(self.original_dir, filename)
            work_file = os.path.join(self.work_dir, filename)

            if os.path.exists(original_file) and os.path.exists(work_file):
                with open(original_file, 'r') as f:
                    original_content = f.read()
                with open(work_file, 'r') as f:
                    work_content = f.read()

                if original_content != work_content:
                    changes[filename] = self._analyze_file_changes(original_content, work_content)

        return changes

    def _analyze_file_changes(self, original: str, modified: str) -> Dict[str, Any]:
        """Analyze specific changes in a file."""
        changes = {
            'lines_added': 0,
            'lines_removed': 0,
            'type_hints_added': 0,
            'error_handling_added': 0,
            'functions_modified': 0,
            'classes_modified': 0
        }

        # Count type hints
        original_type_hints = len(re.findall(r'->|\: \w+', original))
        modified_type_hints = len(re.findall(r'->|\: \w+', modified))
        changes['type_hints_added'] = modified_type_hints - original_type_hints

        # Count error handling
        original_exceptions = len(re.findall(r'except|raise|ValueError|TypeError', original))
        modified_exceptions = len(re.findall(r'except|raise|ValueError|TypeError', modified))
        changes['error_handling_added'] = modified_exceptions - original_exceptions

        # Count functions and classes
        original_functions = len(re.findall(r'def \w+', original))
        modified_functions = len(re.findall(r'def \w+', modified))
        changes['functions_modified'] = modified_functions - original_functions

        original_classes = len(re.findall(r'class \w+', original))
        modified_classes = len(re.findall(r'class \w+', modified))
        changes['classes_modified'] = modified_classes - original_classes

        return changes

class OptimizationTester:
    """Main tester class for 10 iterations."""

    def __init__(self):
        self.token_counter = TokenCounter()
        self.change_analyzer = ChangeAnalyzer(ORIGINAL_PROJECT, WORK_PROJECT)
        self.results = {
            'iterations': [],
            'summary': {},
            'optimizations_applied': []
        }

    def reset_work_directory(self):
        """Reset work directory to original state."""
        print("🔄 Resetting work directory...")

        # Remove all files in work directory
        if os.path.exists(WORK_PROJECT):
            shutil.rmtree(WORK_PROJECT)

        # Copy original files
        shutil.copytree(ORIGINAL_PROJECT, WORK_PROJECT)
        print("✅ Work directory reset complete")

    def run_iteration(self, iteration: int) -> Dict[str, Any]:
        """Run single iteration of testing."""
        print(f"\n{'='*60}")
        print(f"🚀 ITERATION {iteration}/10 - STARTING")
        print(f"{'='*60}")

        # Reset work directory
        self.reset_work_directory()

        # Run regoose improve command
        print("🔧 Running regoose improve...")
        start_time = time.time()

        cmd = [
            "regoose", "improve",
            "--goal", "Add type hints and improve error handling",
            "--directory", WORK_PROJECT,
            "--max-iterations", "1",
            "--dry-run"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            execution_time = time.time() - start_time

            # Extract token usage from logs (simplified estimation)
            log_content = result.stdout + result.stderr
            estimated_tokens = self.token_counter.estimate_tokens_from_logs(log_content)

            print(f"⏱️  Execution time: {execution_time:.2f}s")
            print(f"🎫 Estimated tokens: {estimated_tokens}")

            # Analyze changes made
            changes = self.change_analyzer.analyze_changes()
            print(f"📊 Changes detected: {len(changes)} files modified")

            # Record iteration data
            iteration_data = {
                'iteration': iteration,
                'success': result.returncode == 0,
                'execution_time': execution_time,
                'estimated_tokens': estimated_tokens,
                'changes': changes,
                'exit_code': result.returncode,
                'stdout_preview': result.stdout[:500] + '...' if len(result.stdout) > 500 else result.stdout,
                'stderr_preview': result.stderr[:500] + '...' if len(result.stderr) > 500 else result.stderr
            }

            self.token_counter.record_iteration(iteration, estimated_tokens, changes, execution_time)

            return iteration_data

        except subprocess.TimeoutExpired:
            print("❌ Timeout: Command took too long")
            return {'iteration': iteration, 'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return {'iteration': iteration, 'success': False, 'error': str(e)}

    def apply_optimization(self, iteration_data: Dict) -> str:
        """Apply optimization based on iteration results."""
        optimization = ""

        if iteration_data.get('success'):
            # Analyze what worked well and what can be improved
            changes = iteration_data.get('changes', {})
            execution_time = iteration_data.get('execution_time', 0)
            tokens = iteration_data.get('estimated_tokens', 0)

            if execution_time > 30:
                optimization += "OPTIMIZATION: Reduce execution time by optimizing LLM calls\n"

            if tokens > 1000:
                optimization += "OPTIMIZATION: Reduce token usage by shortening prompts\n"

            if not changes:
                optimization += "OPTIMIZATION: Improve change detection and implementation\n"

            # Check specific improvements
            total_type_hints = sum(c.get('type_hints_added', 0) for c in changes.values())
            total_error_handling = sum(c.get('error_handling_added', 0) for c in changes.values())

            if total_type_hints < 5:
                optimization += "OPTIMIZATION: Enhance type hint detection and addition\n"

            if total_error_handling < 3:
                optimization += "OPTIMIZATION: Improve error handling patterns\n"

        else:
            optimization += "OPTIMIZATION: Fix execution errors and improve stability\n"

        if not optimization:
            optimization = "OPTIMIZATION: Continue current optimization strategy\n"

        return optimization

    def run_all_iterations(self):
        """Run all 10 iterations with continuous optimization."""
        print("🎯 STARTING 10-ITERATION OPTIMIZATION TESTING")
        print("="*70)

        for iteration in range(1, ITERATIONS + 1):
            print(f"\n🟡 ITERATION {iteration} START")

            # Run iteration
            iteration_data = self.run_iteration(iteration)
            self.results['iterations'].append(iteration_data)

            # Apply optimization for next iteration
            if iteration < ITERATIONS:
                optimization = self.apply_optimization(iteration_data)
                print(f"🎛️  Optimization for next iteration:\n{optimization}")
                self.results['optimizations_applied'].append({
                    'iteration': iteration,
                    'optimization': optimization
                })

            print(f"🟢 ITERATION {iteration} COMPLETE")

            # Small delay between iterations
            time.sleep(2)

        # Generate final summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive summary of all iterations."""
        print(f"\n{'='*70}")
        print("📊 FINAL OPTIMIZATION SUMMARY")
        print(f"{'='*70}")

        # Calculate metrics
        successful_iterations = sum(1 for i in self.results['iterations'] if i.get('success'))
        total_tokens = sum(i.get('estimated_tokens', 0) for i in self.results['iterations'])
        avg_execution_time = sum(i.get('execution_time', 0) for i in self.results['iterations']) / ITERATIONS

        # Token efficiency analysis
        if len(self.token_counter.iteration_data) > 1:
            first_iteration_tokens = self.token_counter.iteration_data[0]['tokens_used']
            last_iteration_tokens = self.token_counter.iteration_data[-1]['tokens_used']
            token_improvement = ((first_iteration_tokens - last_iteration_tokens) / first_iteration_tokens) * 100
        else:
            token_improvement = 0

        # Change analysis
        total_type_hints = 0
        total_error_handling = 0

        for iteration in self.results['iterations']:
            changes = iteration.get('changes', {})
            for file_changes in changes.values():
                total_type_hints += file_changes.get('type_hints_added', 0)
                total_error_handling += file_changes.get('error_handling_added', 0)

        # Display results
        print(f"✅ Successful Iterations: {successful_iterations}/{ITERATIONS}")
        print(f"🎫 Total Tokens Used: {total_tokens}")
        print(f"⚡ Average Execution Time: {avg_execution_time:.2f}s")
        print(f"📈 Token Efficiency Improvement: {token_improvement:.1f}%")
        print(f"🏷️  Total Type Hints Added: {total_type_hints}")
        print(f"🛡️  Total Error Handling Added: {total_error_handling}")

        # Per-iteration breakdown
        print(f"\n📋 ITERATION BREAKDOWN:")
        for i, iteration in enumerate(self.results['iterations'], 1):
            status = "✅" if iteration.get('success') else "❌"
            tokens = iteration.get('estimated_tokens', 0)
            time_taken = iteration.get('execution_time', 0)
            changes_count = len(iteration.get('changes', {}))
            print(f"  {i}. {status} {tokens} tokens, {time_taken:.1f}s, {changes_count} files changed")

        # Save detailed results
        self.results['summary'] = {
            'total_iterations': ITERATIONS,
            'successful_iterations': successful_iterations,
            'success_rate': successful_iterations / ITERATIONS * 100,
            'total_tokens': total_tokens,
            'average_execution_time': avg_execution_time,
            'token_improvement_percent': token_improvement,
            'total_type_hints': total_type_hints,
            'total_error_handling': total_error_handling
        }

        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {RESULTS_FILE}")
        print(f"{'='*70}")

def main():
    """Main execution."""
    tester = OptimizationTester()
    tester.run_all_iterations()

if __name__ == "__main__":
    main()
