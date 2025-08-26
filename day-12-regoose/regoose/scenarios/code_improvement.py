"""Code improvement scenario."""

from typing import Dict, Any
from .base import BaseScenario, ScenarioResult
from ..core.orchestrator import ExecutionPlan
from ..core.logging import get_logger, operation_context

logger = get_logger("code_improvement_scenario")


class CodeImprovementScenario(BaseScenario):
    """Scenario for autonomous code improvement and development."""
    
    async def execute(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute the code improvement scenario."""
        
        goal = input_data.get("goal", "Improve code quality")
        target_directory = input_data.get("target_directory", ".")
        max_iterations = input_data.get("max_iterations", 1)
        
        with operation_context("code_improvement_scenario", "code_improvement") as correlation_id:
            logger.info(f"Starting code improvement scenario", metadata={
                "goal": goal,
                "target_directory": target_directory,
                "max_iterations": max_iterations,
                "correlation_id": correlation_id
            })
            
            try:
                # Create execution plan
                plan = ExecutionPlan.sequential([
                    "analyze_codebase",      # Analyze directory and understand current state
                    "plan_improvements",     # Create detailed improvement plan
                    "implement_changes",     # Execute the planned changes
                    "validate_changes",      # Validate syntax and basic checks
                    "generate_report"        # Generate final comprehensive report
                ])
                
                # Execute the plan
                context = await self.orchestrator.execute_plan(plan, input_data)
                
                logger.info("Code improvement scenario completed successfully", metadata={
                    "correlation_id": correlation_id,
                    "final_context_keys": list(context.data.keys())
                })
                
                return ScenarioResult.success_result(context)
                
            except Exception as e:
                logger.error(f"Code improvement scenario failed: {e}", error=str(e), metadata={
                    "correlation_id": correlation_id
                })
                return ScenarioResult.error_result(f"Code improvement scenario failed: {str(e)}")
    
    async def execute_with_iterations(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute code improvement with multiple iterations for complex goals."""
        
        goal = input_data.get("goal", "Improve code quality")
        target_directory = input_data.get("target_directory", ".")
        max_iterations = input_data.get("max_iterations", 3)
        
        with operation_context("iterative_code_improvement", "code_improvement") as correlation_id:
            logger.info(f"Starting iterative code improvement", metadata={
                "goal": goal,
                "max_iterations": max_iterations,
                "correlation_id": correlation_id
            })
            
            try:
                iteration_results = []
                current_context = None
                
                for iteration in range(1, max_iterations + 1):
                    logger.info(f"Starting iteration {iteration}/{max_iterations}")
                    
                    # Prepare input for this iteration
                    iteration_input = input_data.copy()
                    if current_context:
                        # Use results from previous iteration
                        iteration_input.update({
                            "previous_results": current_context.data,
                            "iteration_number": iteration
                        })
                    
                    # Run single iteration
                    result = await self.execute(iteration_input)
                    iteration_results.append({
                        "iteration": iteration,
                        "success": result.success,
                        "error": result.error,
                        "artifacts": result.artifacts
                    })
                    
                    if not result.success:
                        logger.warning(f"Iteration {iteration} failed: {result.error}")
                        # Continue with next iteration unless it's a critical error
                        if "critical" in str(result.error).lower():
                            break
                    else:
                        current_context = result.context
                        logger.info(f"Iteration {iteration} completed successfully")
                        
                        # Check if we should continue
                        validation_results = current_context.get("validation_results", [])
                        if validation_results:
                            # If all validations pass, we might be done
                            all_valid = all(vr.get("syntax_valid", False) for vr in validation_results)
                            if all_valid and iteration > 1:
                                logger.info(f"All validations passed, stopping at iteration {iteration}")
                                break
                
                # Generate final summary
                final_artifacts = self._generate_iteration_summary(iteration_results, goal)
                if current_context:
                    current_context.add_artifacts(final_artifacts)
                
                logger.info(f"Iterative improvement completed after {len(iteration_results)} iterations")
                
                return ScenarioResult.success_result(
                    current_context or self.orchestrator.context_class(),
                    artifacts=final_artifacts
                )
                
            except Exception as e:
                logger.error(f"Iterative improvement failed: {e}", error=str(e))
                return ScenarioResult.error_result(f"Iterative improvement failed: {str(e)}")
    
    def _generate_iteration_summary(self, iteration_results: list, goal: str) -> Dict[str, str]:
        """Generate summary of all iterations."""
        
        total_iterations = len(iteration_results)
        successful_iterations = sum(1 for r in iteration_results if r["success"])
        
        summary = f"""# Iterative Code Improvement Summary

**Goal:** {goal}
**Total Iterations:** {total_iterations}
**Successful Iterations:** {successful_iterations}
**Success Rate:** {successful_iterations/total_iterations*100:.1f}%

## Iteration Results

"""
        
        for result in iteration_results:
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            summary += f"### Iteration {result['iteration']} - {status}\n\n"
            
            if result["error"]:
                summary += f"**Error:** {result['error']}\n\n"
            
            if result["artifacts"]:
                summary += "**Artifacts Generated:**\n"
                for artifact_name in result["artifacts"].keys():
                    summary += f"- {artifact_name}\n"
                summary += "\n"
        
        # Overall assessment
        if successful_iterations == total_iterations:
            summary += "## ✅ Overall Assessment: ALL ITERATIONS SUCCESSFUL\n\n"
            summary += "All planned improvements were implemented successfully.\n"
        elif successful_iterations > 0:
            summary += f"## ⚠️ Overall Assessment: PARTIALLY SUCCESSFUL\n\n"
            summary += f"{successful_iterations} out of {total_iterations} iterations completed successfully.\n"
        else:
            summary += "## ❌ Overall Assessment: FAILED\n\n"
            summary += "No iterations completed successfully. Review errors and try again.\n"
        
        return {
            "iteration_summary.md": summary
        }
