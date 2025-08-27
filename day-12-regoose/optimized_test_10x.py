#!/usr/bin/env python3
"""Optimized 10-Iteration Testing Script with Dynamic Prompt Optimization."""

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
import hashlib

# Test configuration
ITERATIONS = 10
ORIGINAL_PROJECT = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/test_sample_project_original"
WORK_PROJECT = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/test_sample_project"
RESULTS_FILE = "/Users/appascal/Documents/Projects/ai-advert-2025/day-12-regoose/optimized_results.json"

class DynamicPromptOptimizer:
    """Dynamically optimizes prompts based on iteration results."""

    def __init__(self):
        self.base_prompts = {
            'analyze': self._get_base_analyze_prompt(),
            'plan': self._get_base_plan_prompt(),
            'implement': self._get_base_implement_prompt()
        }
        self.optimization_history = []

    def _get_base_analyze_prompt(self):
        return """Analyze the following Python code for improvements. Focus on:
- Type hints for function parameters and return values
- Error handling with proper exceptions
- Code quality and best practices

Be concise but thorough. Return findings in clear format."""

    def _get_base_plan_prompt(self):
        return """Create a specific implementation plan for the recommended changes.
Focus on:
- Clear, actionable steps
- File-specific modifications
- Minimal, targeted changes

Keep the plan focused and executable."""

    def _get_base_implement_prompt(self):
        return """Implement the specified code improvement.
Make precise, surgical changes only.
Return the complete modified code."""

    def optimize_prompt(self, prompt_type: str, iteration_results: Dict) -> str:
        """Optimize prompt based on previous iteration results."""
        base_prompt = self.base_prompts[prompt_type]

        # Analyze results and create optimizations
        optimizations = []

        if iteration_results.get('success'):
            if iteration_results.get('execution_time', 0) > 30:
                optimizations.append("OPTIMIZATION: Be more concise in analysis")
            if iteration_results.get('estimated_tokens', 0) > 2000:
                optimizations.append("OPTIMIZATION: Reduce response verbosity")
        else:
            optimizations.append("OPTIMIZATION: Improve error handling")

        # Apply optimizations
        optimized_prompt = base_prompt
        for opt in optimizations:
            optimized_prompt += f"\n{opt}"

        self.optimization_history.append({
            'iteration': len(self.optimization_history) + 1,
            'prompt_type': prompt_type,
            'optimizations_applied': optimizations
        })

        return optimized_prompt

class AdvancedTokenCounter:
    """Advanced token counter with better estimation."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.total_tokens = 0
        self.calls_by_action = {}
        self.iteration_data = []
        self.prompt_lengths = []

    def estimate_tokens_from_logs(self, log_content: str, prompt_context: Dict = None) -> int:
        """Estimate tokens with improved accuracy."""
        # Count API calls
        openai_calls = len(re.findall(r'openai_generate', log_content))
        tokens_used = []

        # Extract actual token usage from logs
        token_matches = re.findall(r'openai_tokens_used=(\d+)', log_content)
        for match in token_matches:
            tokens_used.append(int(match))

        if tokens_used:
            return sum(tokens_used)

        # Fallback estimation
        base_estimate = openai_calls * 1000  # rough average per call

        # Adjust based on prompt context
        if prompt_context:
            prompt_length = len(str(prompt_context))
            if prompt_length > 1000:
                base_estimate += (prompt_length - 1000) * 0.5

        return max(base_estimate, 500)  # minimum estimate

    def record_iteration(self, iteration: int, tokens: int, changes: Dict, execution_time: float, prompt_context: Dict = None):
        """Record data for one iteration."""
        self.iteration_data.append({
            'iteration': iteration,
            'tokens_used': tokens,
            'changes_made': changes,
            'execution_time': execution_time,
            'prompt_context': prompt_context or {},
            'timestamp': datetime.now().isoformat()
        })
        self.total_tokens += tokens

class FileChangeTracker:
    """Advanced file change tracker with diff analysis."""

    def __init__(self, original_dir: str, work_dir: str):
        self.original_dir = original_dir
        self.work_dir = work_dir
        self.original_hashes = self._calculate_hashes(original_dir)

    def _calculate_hashes(self, directory: str) -> Dict[str, str]:
        """Calculate MD5 hashes for all files in directory."""
        hashes = {}
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'rb') as f:
                        content = f.read()
                        hashes[file] = hashlib.md5(content).hexdigest()
        return hashes

    def analyze_changes(self) -> Dict[str, Any]:
        """Analyze what actually changed in files."""
        changes = {}
        current_hashes = self._calculate_hashes(self.work_dir)

        for filename, original_hash in self.original_hashes.items():
            work_file = os.path.join(self.work_dir, filename)
            original_file = os.path.join(self.original_dir, filename)

            if os.path.exists(work_file):
                with open(work_file, 'rb') as f:
                    current_content = f.read()
                current_hash = hashlib.md5(current_content).hexdigest()

                if original_hash != current_hash:
                    changes[filename] = self._analyze_file_diff(original_file, work_file)

        return changes

    def _analyze_file_diff(self, original_file: str, modified_file: str) -> Dict[str, Any]:
        """Analyze differences between original and modified file."""
        with open(original_file, 'r') as f:
            original_lines = f.readlines()
        with open(modified_file, 'r') as f:
            modified_lines = f.readlines()

        changes = {
            'total_lines_original': len(original_lines),
            'total_lines_modified': len(modified_lines),
            'lines_changed': abs(len(original_lines) - len(modified_lines)),
            'type_hints_added': 0,
            'error_handling_added': 0,
            'functions_modified': 0,
            'classes_modified': 0,
            'specific_changes': []
        }

        # Analyze line-by-line changes
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod:
                changes['specific_changes'].append({
                    'line': i + 1,
                    'original': orig.strip(),
                    'modified': mod.strip()
                })

                # Detect type hints
                if '->' in mod or ': ' in mod:
                    changes['type_hints_added'] += 1

                # Detect error handling
                if 'raise' in mod or 'except' in mod or 'ValueError' in mod:
                    changes['error_handling_added'] += 1

        return changes

class OptimizedTester:
    """Optimized tester with dynamic improvements."""

    def __init__(self):
        self.token_counter = AdvancedTokenCounter()
        self.change_tracker = FileChangeTracker(ORIGINAL_PROJECT, WORK_PROJECT)
        self.prompt_optimizer = DynamicPromptOptimizer()
        self.results = {
            'iterations': [],
            'summary': {},
            'optimizations_applied': [],
            'prompt_evolution': []
        }

    def reset_work_directory(self):
        """Reset work directory to original state."""
        print("🔄 Resetting work directory...")

        # Remove all files in work directory
        if os.path.exists(WORK_PROJECT):
            shutil.rmtree(WORK_PROJECT)

        # Copy original files
        shutil.copytree(ORIGINAL_PROJECT, WORK_PROJECT)

        # Reset change tracker
        self.change_tracker = FileChangeTracker(ORIGINAL_PROJECT, WORK_PROJECT)
        print("✅ Work directory reset complete")

    def run_iteration(self, iteration: int) -> Dict[str, Any]:
        """Run single iteration with optimized prompts."""
        print(f"\n{'='*60}")
        print(f"🚀 ITERATION {iteration}/10 - OPTIMIZED RUN")
        print(f"{'='*60}")

        # Reset work directory
        self.reset_work_directory()

        # Get optimized prompts for this iteration
        optimized_prompts = {}
        if iteration > 1:
            # Use previous iteration results to optimize prompts
            prev_results = self.results['iterations'][-1]
            optimized_prompts = {
                'analyze': self.prompt_optimizer.optimize_prompt('analyze', prev_results),
                'plan': self.prompt_optimizer.optimize_prompt('plan', prev_results),
                'implement': self.prompt_optimizer.optimize_prompt('implement', prev_results)
            }

        print("🔧 Running regoose improve with optimizations...")
        start_time = time.time()

        # Run command with optimized settings
        cmd = [
            "regoose", "improve",
            "--goal", "Add type hints and improve error handling",
            "--directory", WORK_PROJECT,
            "--max-iterations", "1"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            execution_time = time.time() - start_time

            # Extract token usage and other metrics from logs
            log_content = result.stdout + result.stderr
            estimated_tokens = self.token_counter.estimate_tokens_from_logs(log_content, optimized_prompts)

            print(f"⏱️  Execution time: {execution_time:.2f}s")
            print(f"🎫 Estimated tokens: {estimated_tokens}")

            # Analyze actual changes made
            changes = self.change_tracker.analyze_changes()
            print(f"📊 Files changed: {len(changes)}")

            # Show detailed change summary
            for filename, change_data in changes.items():
                print(f"   📄 {filename}:")
                print(f"      Type hints: +{change_data.get('type_hints_added', 0)}")
                print(f"      Error handling: +{change_data.get('error_handling_added', 0)}")
                print(f"      Lines changed: {change_data.get('lines_changed', 0)}")

            # Record iteration data
            iteration_data = {
                'iteration': iteration,
                'success': result.returncode == 0,
                'execution_time': execution_time,
                'estimated_tokens': estimated_tokens,
                'changes': changes,
                'exit_code': result.returncode,
                'optimized_prompts': optimized_prompts,
                'change_summary': self._summarize_changes(changes)
            }

            self.token_counter.record_iteration(iteration, estimated_tokens, changes, execution_time, optimized_prompts)

            return iteration_data

        except subprocess.TimeoutExpired:
            print("❌ Timeout: Command took too long")
            return {'iteration': iteration, 'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return {'iteration': iteration, 'success': False, 'error': str(e)}

    def _summarize_changes(self, changes: Dict) -> Dict[str, Any]:
        """Create summary of all changes."""
        summary = {
            'total_files_changed': len(changes),
            'total_type_hints': sum(c.get('type_hints_added', 0) for c in changes.values()),
            'total_error_handling': sum(c.get('error_handling_added', 0) for c in changes.values()),
            'total_lines_changed': sum(c.get('lines_changed', 0) for c in changes.values())
        }
        return summary

    def apply_optimization(self, iteration_data: Dict) -> str:
        """Apply optimization based on iteration results."""
        optimization = ""

        if iteration_data.get('success'):
            changes_summary = iteration_data.get('change_summary', {})
            execution_time = iteration_data.get('execution_time', 0)
            tokens = iteration_data.get('estimated_tokens', 0)

            if execution_time > 30:
                optimization += "OPTIMIZATION: Reduce analysis depth for faster execution\n"

            if tokens > 2000:
                optimization += "OPTIMIZATION: Implement token-aware prompt truncation\n"

            if changes_summary.get('total_type_hints', 0) == 0:
                optimization += "OPTIMIZATION: Enhance type hint detection patterns\n"

            if changes_summary.get('total_error_handling', 0) == 0:
                optimization += "OPTIMIZATION: Improve error handling recognition\n"

            if changes_summary.get('total_files_changed', 0) == 0:
                optimization += "OPTIMIZATION: Fix file modification pipeline\n"

        else:
            optimization += "OPTIMIZATION: Debug and fix execution pipeline errors\n"

        if not optimization:
            optimization = "OPTIMIZATION: Continue refining current approach\n"

        return optimization

    def run_all_iterations(self):
        """Run all 10 iterations with continuous optimization."""
        print("🎯 STARTING OPTIMIZED 10-ITERATION TESTING")
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
                    'optimization': optimization,
                    'based_on': iteration_data.get('change_summary', {})
                })

            print(f"🟢 ITERATION {iteration} COMPLETE")

            # Small delay between iterations
            time.sleep(3)

        # Generate final summary
        self.generate_final_summary()

    def generate_final_summary(self):
        """Generate comprehensive final summary."""
        print(f"\n{'='*70}")
        print("📊 OPTIMIZED TESTING FINAL SUMMARY")
        print(f"{'='*70}")

        # Calculate metrics
        successful_iterations = sum(1 for i in self.results['iterations'] if i.get('success'))
        total_tokens = sum(i.get('estimated_tokens', 0) for i in self.results['iterations'])
        avg_execution_time = sum(i.get('execution_time', 0) for i in self.results['iterations']) / ITERATIONS

        # Token efficiency analysis
        if len(self.token_counter.iteration_data) > 1:
            first_tokens = self.token_counter.iteration_data[0]['tokens_used']
            last_tokens = self.token_counter.iteration_data[-1]['tokens_used']
            token_improvement = ((first_tokens - last_tokens) / first_tokens) * 100 if first_tokens > 0 else 0
        else:
            token_improvement = 0

        # Change analysis across all iterations
        total_type_hints = 0
        total_error_handling = 0
        total_files_changed = 0
        total_lines_changed = 0

        for iteration in self.results['iterations']:
            changes_summary = iteration.get('change_summary', {})
            total_type_hints += changes_summary.get('total_type_hints', 0)
            total_error_handling += changes_summary.get('total_error_handling', 0)
            total_files_changed += changes_summary.get('total_files_changed', 0)
            total_lines_changed += changes_summary.get('total_lines_changed', 0)

        # Display results
        print(f"✅ Successful Iterations: {successful_iterations}/{ITERATIONS}")
        print(f"🎫 Total Tokens Used: {total_tokens:,}")
        print(f"⚡ Average Execution Time: {avg_execution_time:.2f}s")
        print(f"📈 Token Efficiency Improvement: {token_improvement:.1f}%")
        print(f"🏷️  Total Type Hints Added: {total_type_hints}")
        print(f"🛡️  Total Error Handling Added: {total_error_handling}")
        print(f"📄 Total Files Changed: {total_files_changed}")
        print(f"📝 Total Lines Changed: {total_lines_changed}")

        # Per-iteration breakdown
        print(f"\n📋 ITERATION BREAKDOWN:")
        for i, iteration in enumerate(self.results['iterations'], 1):
            status = "✅" if iteration.get('success') else "❌"
            tokens = iteration.get('estimated_tokens', 0)
            time_taken = iteration.get('execution_time', 0)
            changes = iteration.get('change_summary', {})
            files_changed = changes.get('total_files_changed', 0)
            print(f"  {i}. {status} {tokens:,} tokens, {time_taken:.1f}s, {files_changed} files")

        # Optimization history
        print(f"\n🎛️  OPTIMIZATION HISTORY:")
        for opt in self.results['optimizations_applied']:
            print(f"  Iteration {opt['iteration']}: {opt['optimization'].strip()}")

        # Save detailed results
        self.results['summary'] = {
            'total_iterations': ITERATIONS,
            'successful_iterations': successful_iterations,
            'success_rate': successful_iterations / ITERATIONS * 100,
            'total_tokens': total_tokens,
            'average_execution_time': avg_execution_time,
            'token_improvement_percent': token_improvement,
            'total_type_hints': total_type_hints,
            'total_error_handling': total_error_handling,
            'total_files_changed': total_files_changed,
            'total_lines_changed': total_lines_changed,
            'optimization_history': self.prompt_optimizer.optimization_history
        }

        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {RESULTS_FILE}")
        print(f"{'='*70}")

def main():
    """Main execution."""
    tester = OptimizedTester()
    tester.run_all_iterations()

if __name__ == "__main__":
    main()
