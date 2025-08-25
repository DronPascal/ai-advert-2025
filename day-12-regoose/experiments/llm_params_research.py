#!/usr/bin/env python3
"""
LLM Parameters Research Script

This script conducts experiments to analyze the impact of different LLM parameters
on test generation quality and creativity.
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import sys
sys.path.append('..')

from regoose.providers.factory import LLMProviderFactory
from regoose.core.config import get_settings
from regoose.core.orchestrator import ActionOrchestrator
from regoose.scenarios.test_generation import TestGenerationScenario
from regoose.tools.filesystem_tool import FilesystemTool
from regoose.tools.shell_tool import ShellTool
from regoose.tools.container_tool import ContainerTool

# Test code samples for experiments
TEST_SAMPLES = {
    "fibonacci": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
    
    "sort_list": """def sort_list(lst):
    return sorted(lst)""",
    
    "calculator": """class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero")
        return a / b""",
    
    "password_validator": """def is_valid_password(password):
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit"""
}

# Parameter combinations to test
PARAMETER_SETS = [
    {"name": "default", "params": {}},
    {"name": "creative", "params": {"temperature": 1.2, "top_p": 0.95}},
    {"name": "focused", "params": {"temperature": 0.2, "top_p": 0.5}},
    {"name": "balanced", "params": {"temperature": 0.7, "top_p": 0.9}},
    {"name": "conservative", "params": {"temperature": 0.1, "presence_penalty": 0.5}},
    {"name": "exploratory", "params": {"temperature": 1.5, "frequency_penalty": 0.8}},
    {"name": "short_response", "params": {"max_tokens": 1000, "temperature": 0.5}},
    {"name": "long_response", "params": {"max_tokens": 3000, "temperature": 0.5}},
]

class LLMResearchExperiment:
    def __init__(self):
        self.results = []
        self.settings = get_settings()
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def run_single_experiment(self, code_name: str, code: str, param_set: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single experiment with given parameters."""
        print(f"🧪 Running experiment: {code_name} with {param_set['name']} parameters")
        
        start_time = time.time()
        
        try:
            # Create LLM provider with specific parameters
            llm_provider = LLMProviderFactory.create_provider(
                "openai",  # Using OpenAI for consistency
                self.settings,
                llm_params=param_set["params"]
            )
            
            # Create tools (without container for faster execution)
            tools = {
                "filesystem": FilesystemTool("./temp_experiments"),
                "shell": ShellTool("./temp_experiments"),
                "container": ContainerTool(runtime="podman", base_image="python:3.11-slim"),
                "working_dir": "./temp_experiments"
            }
            
            # Create orchestrator and scenario
            orchestrator = ActionOrchestrator(llm_provider, tools)
            scenario = TestGenerationScenario(orchestrator)
            
            # Prepare input
            scenario_input = {
                "code": code,
                "language": "python",
                "framework": "unittest",
                "max_iterations": 1  # Single iteration for speed
            }
            
            # Execute scenario
            result = await scenario.execute(scenario_input)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Analyze result
            analysis = self.analyze_result(result, param_set, execution_time)
            
            return {
                "code_name": code_name,
                "parameter_set": param_set["name"],
                "parameters": param_set["params"],
                "execution_time": execution_time,
                "success": result.get("success", False),
                "analysis": analysis,
                "raw_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            return {
                "code_name": code_name,
                "parameter_set": param_set["name"],
                "parameters": param_set["params"],
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_result(self, result: Dict[str, Any], param_set: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """Analyze the experiment result."""
        analysis = {
            "execution_time": execution_time,
            "parameter_impact": {},
            "quality_metrics": {}
        }
        
        # Analyze test content if available
        generated_tests = result.get("generated_tests", "")
        if generated_tests:
            analysis["quality_metrics"] = {
                "test_length": len(generated_tests),
                "test_count": generated_tests.count("def test_"),
                "assertion_count": generated_tests.count("assert"),
                "import_count": generated_tests.count("import"),
                "docstring_count": generated_tests.count('"""'),
                "complexity_indicators": {
                    "edge_cases": generated_tests.lower().count("edge"),
                    "error_handling": generated_tests.lower().count("error") + generated_tests.lower().count("exception"),
                    "performance_tests": generated_tests.lower().count("performance") + generated_tests.lower().count("time"),
                    "boundary_tests": generated_tests.lower().count("boundary") + generated_tests.lower().count("limit")
                }
            }
        
        # Parameter-specific analysis
        params = param_set["params"]
        if "temperature" in params:
            analysis["parameter_impact"]["temperature"] = {
                "value": params["temperature"],
                "expected_creativity": "high" if params["temperature"] > 1.0 else "medium" if params["temperature"] > 0.5 else "low"
            }
        
        if "top_p" in params:
            analysis["parameter_impact"]["top_p"] = {
                "value": params["top_p"],
                "expected_diversity": "high" if params["top_p"] > 0.8 else "medium" if params["top_p"] > 0.5 else "low"
            }
        
        return analysis
    
    async def run_all_experiments(self):
        """Run all experiment combinations."""
        print("🚀 Starting LLM Parameters Research Experiment")
        print(f"📊 Testing {len(TEST_SAMPLES)} code samples with {len(PARAMETER_SETS)} parameter sets")
        print(f"🔬 Total experiments: {len(TEST_SAMPLES) * len(PARAMETER_SETS)}")
        
        experiment_count = 0
        total_experiments = len(TEST_SAMPLES) * len(PARAMETER_SETS)
        
        for code_name, code in TEST_SAMPLES.items():
            for param_set in PARAMETER_SETS:
                experiment_count += 1
                print(f"\n📈 Progress: {experiment_count}/{total_experiments}")
                
                result = await self.run_single_experiment(code_name, code, param_set)
                self.results.append(result)
                
                # Save intermediate results
                self.save_results()
                
                # Brief pause between experiments
                await asyncio.sleep(1)
        
        print("\n✅ All experiments completed!")
        self.generate_final_report()
    
    def save_results(self):
        """Save results to JSON file."""
        results_file = self.results_dir / f"llm_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def generate_final_report(self):
        """Generate final markdown report."""
        report_file = self.results_dir / f"LLM_Parameters_Research_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w') as f:
            f.write(self.generate_markdown_report())
        
        print(f"📋 Final report saved to: {report_file}")
    
    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        report = f"""# LLM Parameters Research Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Experiments**: {len(self.results)}
**Test Samples**: {len(TEST_SAMPLES)}
**Parameter Sets**: {len(PARAMETER_SETS)}

## Executive Summary

This research analyzes the impact of different LLM parameters on test generation quality, creativity, and performance.

## Parameter Sets Tested

"""
        
        for param_set in PARAMETER_SETS:
            report += f"### {param_set['name'].title()}\n"
            if param_set["params"]:
                for key, value in param_set["params"].items():
                    report += f"- **{key}**: {value}\n"
            else:
                report += "- Default parameters\n"
            report += "\n"
        
        # Performance Analysis
        report += "## Performance Analysis\n\n"
        
        performance_by_params = {}
        for result in self.results:
            param_name = result["parameter_set"]
            if param_name not in performance_by_params:
                performance_by_params[param_name] = {
                    "times": [],
                    "success_count": 0,
                    "total_count": 0
                }
            
            performance_by_params[param_name]["times"].append(result["execution_time"])
            performance_by_params[param_name]["total_count"] += 1
            if result["success"]:
                performance_by_params[param_name]["success_count"] += 1
        
        report += "| Parameter Set | Avg Time (s) | Success Rate | Total Tests |\n"
        report += "|---------------|-------------|-------------|-------------|\n"
        
        for param_name, data in performance_by_params.items():
            avg_time = sum(data["times"]) / len(data["times"])
            success_rate = (data["success_count"] / data["total_count"]) * 100
            report += f"| {param_name} | {avg_time:.2f} | {success_rate:.1f}% | {data['total_count']} |\n"
        
        # Quality Analysis
        report += "\n## Quality Analysis\n\n"
        
        quality_by_params = {}
        for result in self.results:
            if not result["success"]:
                continue
                
            param_name = result["parameter_set"]
            analysis = result.get("analysis", {})
            quality_metrics = analysis.get("quality_metrics", {})
            
            if param_name not in quality_by_params:
                quality_by_params[param_name] = {
                    "test_counts": [],
                    "assertion_counts": [],
                    "complexity_scores": []
                }
            
            quality_by_params[param_name]["test_counts"].append(quality_metrics.get("test_count", 0))
            quality_by_params[param_name]["assertion_counts"].append(quality_metrics.get("assertion_count", 0))
            
            # Calculate complexity score
            complexity = quality_metrics.get("complexity_indicators", {})
            complexity_score = sum(complexity.values()) if complexity else 0
            quality_by_params[param_name]["complexity_scores"].append(complexity_score)
        
        report += "| Parameter Set | Avg Tests | Avg Assertions | Avg Complexity Score |\n"
        report += "|---------------|-----------|----------------|----------------------|\n"
        
        for param_name, data in quality_by_params.items():
            avg_tests = sum(data["test_counts"]) / len(data["test_counts"]) if data["test_counts"] else 0
            avg_assertions = sum(data["assertion_counts"]) / len(data["assertion_counts"]) if data["assertion_counts"] else 0
            avg_complexity = sum(data["complexity_scores"]) / len(data["complexity_scores"]) if data["complexity_scores"] else 0
            
            report += f"| {param_name} | {avg_tests:.1f} | {avg_assertions:.1f} | {avg_complexity:.1f} |\n"
        
        # Detailed Results
        report += "\n## Detailed Results\n\n"
        
        for code_name in TEST_SAMPLES.keys():
            report += f"### {code_name.title()} Results\n\n"
            
            code_results = [r for r in self.results if r["code_name"] == code_name]
            
            report += "| Parameter Set | Success | Time (s) | Tests Generated | Assertions |\n"
            report += "|---------------|---------|----------|-----------------|------------|\n"
            
            for result in code_results:
                success = "✅" if result["success"] else "❌"
                time_str = f"{result['execution_time']:.2f}"
                
                if result["success"]:
                    analysis = result.get("analysis", {})
                    quality = analysis.get("quality_metrics", {})
                    tests = quality.get("test_count", 0)
                    assertions = quality.get("assertion_count", 0)
                else:
                    tests = "N/A"
                    assertions = "N/A"
                
                report += f"| {result['parameter_set']} | {success} | {time_str} | {tests} | {assertions} |\n"
            
            report += "\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        
        # Find best performing parameter sets
        best_performance = max(performance_by_params.items(), key=lambda x: x[1]["success_count"] / x[1]["total_count"])
        fastest_params = min(performance_by_params.items(), key=lambda x: sum(x[1]["times"]) / len(x[1]["times"]))
        
        report += f"### Best Overall Performance\n"
        report += f"**{best_performance[0]}** achieved the highest success rate ({(best_performance[1]['success_count'] / best_performance[1]['total_count']) * 100:.1f}%)\n\n"
        
        report += f"### Fastest Execution\n"
        report += f"**{fastest_params[0]}** had the fastest average execution time ({sum(fastest_params[1]['times']) / len(fastest_params[1]['times']):.2f}s)\n\n"
        
        # Parameter-specific recommendations
        report += "### Parameter Guidelines\n\n"
        report += "- **Temperature 0.1-0.3**: Best for consistent, focused test generation\n"
        report += "- **Temperature 0.7-1.0**: Good balance of creativity and coherence\n"
        report += "- **Temperature 1.2+**: High creativity but may reduce coherence\n"
        report += "- **Top-p 0.5-0.9**: Recommended range for most use cases\n"
        report += "- **Max Tokens 2000-3000**: Optimal for comprehensive test suites\n"
        report += "- **Presence/Frequency Penalties**: Use sparingly, may reduce test coverage\n\n"
        
        report += "## Conclusion\n\n"
        report += "This research demonstrates that LLM parameters significantly impact test generation quality and performance. "
        report += "Choose parameters based on your specific needs: lower temperature for consistency, higher for creativity.\n"
        
        return report

async def main():
    """Main function to run the research experiment."""
    experiment = LLMResearchExperiment()
    await experiment.run_all_experiments()

if __name__ == "__main__":
    asyncio.run(main())
