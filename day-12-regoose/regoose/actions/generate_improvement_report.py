"""
Action for generating code improvement reports.
"""

from typing import Dict, Any, List
from .base import BaseAction, ActionResult, ActionContext
from ..core.logging import get_logger


class GenerateImprovementReportAction(BaseAction):
    """Action for generating detailed reports on code improvements."""
    
    def __init__(self, llm_provider, tools):
        super().__init__(llm_provider, tools)
        self.logger = get_logger("generate_improvement_report")

    def get_required_fields(self) -> List[str]:
        return ["implementation_plan", "modified_files", "validation_results"]

    async def execute(self, context: ActionContext) -> ActionResult:
        """Generate a comprehensive improvement report."""
        try:
            self.logger.info("Generating code improvement report")
            
            implementation_plan = context.get("implementation_plan", [])
            modified_files = context.get("modified_files", [])
            validation_results = context.get("validation_results", {})
            goal = context.get("goal", "Code improvement")
            
            # Count successes and failures
            total_steps = len(implementation_plan)
            successful_changes = len([f for f in modified_files if f.get("success", False)])
            failed_changes = total_steps - successful_changes
            
            # Calculate validation stats
            validation_passed = sum(1 for result in validation_results.get("results", []) if result.get("valid", False))
            validation_failed = len(validation_results.get("results", [])) - validation_passed
            
            # Generate summary
            summary = self._generate_summary(
                total_steps, successful_changes, failed_changes, 
                validation_passed, validation_failed, goal
            )
            
            # Generate detailed report
            report = self._generate_detailed_report(
                goal, implementation_plan, modified_files, 
                validation_results, summary
            )
            
            self.logger.info(f"Report generated successfully: {successful_changes}/{total_steps} changes successful")
            
            return ActionResult.success_result(
                data={
                    "summary": summary,
                    "total_steps": total_steps,
                    "successful_changes": successful_changes,
                    "failed_changes": failed_changes,
                    "validation_passed": validation_passed,
                    "validation_failed": validation_failed
                },
                artifacts={
                    "improvement_report.md": report
                }
            )
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", error=str(e))
            return ActionResult.error_result(f"Report generation failed: {str(e)}")
    
    def _generate_summary(self, total_steps: int, successful: int, failed: int, 
                         validated: int, validation_failed: int, goal: str) -> str:
        """Generate a summary of the improvement process."""
        
        success_rate = (successful / total_steps * 100) if total_steps > 0 else 0
        validation_rate = (validated / (validated + validation_failed) * 100) if (validated + validation_failed) > 0 else 0
        
        return f"""
🎯 **Goal:** {goal}

📊 **Results Summary:**
- Total Steps: {total_steps}
- Successful Changes: {successful} ({success_rate:.1f}%)
- Failed Changes: {failed}
- Validation Passed: {validated} ({validation_rate:.1f}%)
- Validation Failed: {validation_failed}

✅ **Overall Status:** {'SUCCESS' if failed == 0 else 'PARTIAL SUCCESS' if successful > 0 else 'FAILED'}
"""
    
    def _generate_detailed_report(self, goal: str, plan: List[Dict], 
                                modified_files: List[Dict], validation_results: Dict, 
                                summary: str) -> str:
        """Generate detailed improvement report."""
        
        report = f"""# Code Improvement Report

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
{summary}

## Implementation Details

### Planned Steps
"""
        
        for i, step in enumerate(plan, 1):
            status = "✅ SUCCESS" if any(f.get("file") == step.get("file") and f.get("success") for f in modified_files) else "❌ FAILED"
            report += f"""
**Step {i}: {step.get('description', 'Unknown step')}** - {status}
- File: `{step.get('file', 'Unknown')}`
- Change Type: {step.get('change_type', 'Unknown')}
"""
        
        report += "\n### Modified Files\n"
        
        if modified_files:
            for file_info in modified_files:
                file_path = file_info.get("file", "Unknown")
                success = file_info.get("success", False)
                status_icon = "✅" if success else "❌"
                
                report += f"""
{status_icon} **{file_path}**
"""
                if file_info.get("changes_made"):
                    for change in file_info["changes_made"]:
                        report += f"  - {change}\n"
                
                if file_info.get("backup_created"):
                    report += f"  - Backup: `{file_info['backup_created']}`\n"
                
                if file_info.get("error"):
                    report += f"  - Error: {file_info['error']}\n"
        else:
            report += "No files were modified.\n"
        
        report += "\n### Validation Results\n"
        
        validation_data = validation_results.get("results", [])
        if validation_data:
            for result in validation_data:
                file_path = result.get("file", "Unknown")
                valid = result.get("valid", False)
                status_icon = "✅" if valid else "❌"
                
                report += f"{status_icon} **{file_path}** - {'Valid' if valid else 'Invalid'}\n"
                
                if result.get("errors"):
                    for error in result["errors"]:
                        report += f"  - Error: {error}\n"
                
                if result.get("warnings"):
                    for warning in result["warnings"]:
                        report += f"  - Warning: {warning}\n"
        else:
            report += "No validation performed.\n"
        
        report += "\n## Recommendations\n"
        report += "- Review any failed changes and address the underlying issues\n"
        report += "- Consider running validation tests to ensure code quality\n"
        report += "- Check that all modified files work as expected\n"
        
        return report