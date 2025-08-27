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
                    "generate_improvement_report"  # Generate final comprehensive report
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
        """Execute code improvement with smart iterations and convergence detection."""

        goal = input_data.get("goal", "Improve code quality")
        target_directory = input_data.get("target_directory", ".")
        max_iterations = input_data.get("max_iterations", 3)

        with operation_context("iterative_code_improvement", "code_improvement") as correlation_id:
            logger.info(f"Starting smart iterative code improvement", metadata={
                "goal": goal,
                "max_iterations": max_iterations,
                "correlation_id": correlation_id
            })

            try:
                iteration_results = []
                current_context = None
                convergence_score = 0.0
                previous_changes = set()

                for iteration in range(1, max_iterations + 1):
                    logger.info(f"Starting iteration {iteration}/{max_iterations}")

                    # Prepare input for this iteration with smart context
                    iteration_input = input_data.copy()
                    if current_context:
                        # Smart context preservation - only pass essential data
                        iteration_input.update({
                            "previous_results": self._extract_essential_context(current_context.data),
                            "iteration_number": iteration,
                            "convergence_score": convergence_score,
                            "previous_changes": list(previous_changes)
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
                        # Smart error handling - break on critical errors only
                        if self._is_critical_error(result.error):
                            break
                    else:
                        current_context = result.context
                        logger.info(f"Iteration {iteration} completed successfully")

                        # Smart convergence detection
                        if iteration > 1:
                            new_changes = self._extract_changes_from_context(current_context)
                            convergence_score = self._calculate_convergence_score(previous_changes, new_changes)

                            if convergence_score > 0.85:  # 85% convergence threshold
                                logger.info(f"High convergence detected ({convergence_score:.2f}), stopping at iteration {iteration}")
                                break
                            elif convergence_score < 0.1 and iteration >= 2:  # No progress after 2 iterations
                                logger.warning(f"No progress detected, stopping at iteration {iteration}")
                                break

                            previous_changes.update(new_changes)

                        # Check validation results for early termination
                        validation_results = current_context.get("validation_results", [])
                        if validation_results and self._all_validations_pass(validation_results):
                            logger.info(f"All validations passed, stopping at iteration {iteration}")
                            break

                # Generate final summary
                final_artifacts = self._generate_iteration_summary(iteration_results, goal)
                if current_context:
                    current_context.add_artifacts(final_artifacts)

                logger.info(f"Smart iterative improvement completed after {len(iteration_results)} iterations")

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

    def _extract_essential_context(self, context_data: Dict) -> Dict:
        """Extract only essential context data to minimize token usage."""
        essential = {}

        # Keep only critical data for next iteration
        if "validation_results" in context_data:
            essential["validation_results"] = context_data["validation_results"]
        if "implementation_results" in context_data:
            # Summarize implementation results to save tokens
            essential["implementation_summary"] = {
                "total_changes": len(context_data["implementation_results"]),
                "successful_changes": sum(1 for r in context_data["implementation_results"] if r.get("success")),
                "failed_changes": sum(1 for r in context_data["implementation_results"] if not r.get("success"))
            }
        if "goal" in context_data:
            essential["goal"] = context_data["goal"]

        return essential

    def _extract_changes_from_context(self, context) -> set:
        """Extract change signatures from context for convergence detection."""
        changes = set()

        implementation_results = context.get("implementation_results", [])
        for result in implementation_results:
            if result.get("success") and result.get("file"):
                # Create a signature of the change
                change_sig = f"{result['file']}:{result.get('change_type', 'unknown')}"
                changes.add(change_sig)

        return changes

    def _calculate_convergence_score(self, previous_changes: set, new_changes: set) -> float:
        """Calculate convergence score between iterations."""
        if not previous_changes:
            return 0.0

        # Calculate overlap between previous and new changes
        overlap = len(previous_changes.intersection(new_changes))
        total_unique = len(previous_changes.union(new_changes))

        return overlap / total_unique if total_unique > 0 else 1.0

    def _is_critical_error(self, error: str) -> bool:
        """Determine if an error is critical enough to stop iterations."""
        if not error:
            return False

        critical_keywords = ["authentication", "authorization", "permission", "security", "fatal"]
        error_lower = str(error).lower()

        return any(keyword in error_lower for keyword in critical_keywords)

    def _all_validations_pass(self, validation_results: List[Dict]) -> bool:
        """Check if all validation results pass."""
        if not validation_results:
            return False

        return all(
            result.get("syntax_valid", False) and result.get("file_readable", False)
            for result in validation_results
        )
