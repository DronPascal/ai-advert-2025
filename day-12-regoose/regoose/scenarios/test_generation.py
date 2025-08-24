"""Test generation scenario."""

from typing import Dict, Any
from .base import BaseScenario, ScenarioResult
from ..core.orchestrator import ExecutionPlan


class TestGenerationScenario(BaseScenario):
    """Scenario for comprehensive test generation and execution."""
    
    async def execute(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute the test generation scenario."""
        try:
            # Create execution plan
            plan = ExecutionPlan.sequential([
                "analyze_code",      # Analyze code and generate tests
                "run_tests",         # Run tests in container
                "generate_report"    # Generate final report
            ])
            
            # Execute the plan
            context = await self.orchestrator.execute_plan(plan, input_data)
            
            return ScenarioResult.success_result(context)
            
        except Exception as e:
            return ScenarioResult.error_result(f"Test generation scenario failed: {str(e)}")
    
    async def execute_with_improvements(self, input_data: Dict[str, Any], max_iterations: int = 3) -> ScenarioResult:
        """Execute test generation with iterative improvements."""
        try:
            # First iteration - initial generation
            initial_plan = ExecutionPlan.sequential([
                "analyze_code",
                "run_tests"
            ])
            
            context = await self.orchestrator.execute_plan(initial_plan, input_data)
            
            # Check if improvement is needed
            test_results = context.get("test_results", [])
            iteration = 1
            
            while iteration < max_iterations:
                # Calculate success rate
                total_tests = sum(r.passed + r.failed + r.errors for r in test_results)
                total_passed = sum(r.passed for r in test_results)
                
                if total_passed == total_tests and total_tests > 0:
                    # All tests passed, no improvement needed
                    break
                
                if total_tests > 0:
                    # Extract failure information for improvement
                    failure_info = []
                    for result in test_results:
                        if result.failed > 0 and result.details:
                            for detail in result.details:
                                if isinstance(detail, dict) and 'raw_output' in detail:
                                    failure_info.append(detail['raw_output'])
                    
                    if failure_info:
                        # Prepare context for improvement
                        improvement_data = {
                            "code": context.get("code"),
                            "original_tests": context.get("tests"),
                            "failure_info": failure_info,
                            "language": context.get("language"),
                            "framework": context.get("framework")
                        }
                        
                        # Run improvement iteration
                        improvement_plan = ExecutionPlan.sequential([
                            "generate_tests",  # Improve tests based on failures
                            "run_tests"        # Run improved tests
                        ])
                        
                        improved_context = await self.orchestrator.execute_plan(improvement_plan, improvement_data)
                        
                        # Update context with improved results
                        context.update(improved_context.data)
                        context.add_artifacts(improved_context.artifacts)
                        context.history.extend(improved_context.history)
                        
                        test_results = context.get("test_results", [])
                        iteration += 1
                    else:
                        break
                else:
                    break
            
            # Generate final report
            report_plan = ExecutionPlan.sequential(["generate_report"])
            final_context = await self.orchestrator.execute_plan(report_plan, context.data)
            
            # Merge contexts
            context.update(final_context.data)
            context.add_artifacts(final_context.artifacts)
            
            return ScenarioResult.success_result(context)
            
        except Exception as e:
            return ScenarioResult.error_result(f"Test generation with improvements failed: {str(e)}")
