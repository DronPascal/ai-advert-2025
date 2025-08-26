"""Implement changes action for code improvement scenarios."""

from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult
from ..core.logging import get_logger, timed_operation

logger = get_logger("implement_changes")


class ImplementChangesAction(BaseAction):
    """Action to implement planned code improvements."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["implementation_plan"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        implementation_plan = context.get("implementation_plan")
        return implementation_plan is not None and len(implementation_plan) > 0
    
    @timed_operation("implement_changes", "code_improvement")
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute code changes implementation."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing or empty 'implementation_plan'")
            
            implementation_plan = context.get("implementation_plan", [])
            goal = context.get("goal", "Code improvement")
            
            logger.info(f"Implementing {len(implementation_plan)} planned changes")
            
            # Get filesystem tool
            filesystem_tool = self.tools.get("secure_filesystem")
            if not filesystem_tool:
                return ActionResult.error_result("Secure filesystem tool not available")
            
            results = []
            successful_changes = 0
            failed_changes = 0
            
            for step in implementation_plan:
                step_result = await self._implement_step(step, filesystem_tool)
                results.append(step_result)
                
                if step_result["success"]:
                    successful_changes += 1
                    logger.info(f"✅ Step {step['step_number']}: {step['title']}")
                else:
                    failed_changes += 1
                    logger.error(f"❌ Step {step['step_number']}: {step_result['error']}")
            
            # Generate summary
            summary = self._generate_implementation_summary(results, successful_changes, failed_changes)
            
            logger.info(f"Implementation completed: {successful_changes} successful, {failed_changes} failed")
            
            return ActionResult.success_result(
                data={
                    "implementation_results": results,
                    "successful_changes": successful_changes,
                    "failed_changes": failed_changes,
                    "total_steps": len(implementation_plan),
                    "summary": summary
                },
                artifacts={
                    "implementation_results.md": self._generate_results_report(results, summary)
                }
            )
            
        except Exception as e:
            logger.error(f"Implementation failed: {e}", error=str(e))
            return ActionResult.error_result(f"Implementation failed: {str(e)}")
    
    async def _implement_step(self, step: Dict, filesystem_tool) -> Dict:
        """Implement a single step from the plan."""
        step_result = {
            "step_number": step.get("step_number", 0),
            "title": step.get("title", "Unknown step"),
            "file": step.get("file", ""),
            "change_type": step.get("change_type", "modification"),
            "success": False,
            "error": None,
            "changes_made": [],
            "backup_created": None
        }
        
        try:
            file_path = step.get("file", "").strip()
            change_type = step.get("change_type", "modification").lower()
            code = step.get("code", "").strip()
            description = step.get("description", "")
            
            if not file_path:
                step_result["error"] = "No file specified"
                return step_result
            
            # Handle different change types
            if change_type == "addition" or change_type == "create":
                # Create new file
                if code:
                    result = await filesystem_tool.execute("write_file", path=file_path, content=code)
                    if result.success:
                        step_result["success"] = True
                        step_result["changes_made"].append(f"Created file: {file_path}")
                    else:
                        step_result["error"] = f"Failed to create file: {result.error}"
                else:
                    step_result["error"] = "No code provided for file creation"
            
            elif change_type == "modification" or change_type == "edit":
                # Modify existing file
                if code:
                    # Create backup first
                    backup_result = await filesystem_tool.execute("backup_file", path=file_path)
                    if backup_result.success:
                        step_result["backup_created"] = backup_result.metadata.get("backup_path")
                    
                    # Write new content
                    result = await filesystem_tool.execute("write_file", path=file_path, content=code)
                    if result.success:
                        step_result["success"] = True
                        step_result["changes_made"].append(f"Modified file: {file_path}")
                    else:
                        step_result["error"] = f"Failed to modify file: {result.error}"
                else:
                    # If no code provided, try to make intelligent changes based on description
                    step_result = await self._intelligent_modification(
                        step, filesystem_tool, step_result
                    )
            
            elif change_type == "deletion" or change_type == "delete":
                # For safety, we'll just create a backup instead of deleting
                backup_result = await filesystem_tool.execute("backup_file", path=file_path)
                if backup_result.success:
                    step_result["success"] = True
                    step_result["backup_created"] = backup_result.metadata.get("backup_path")
                    step_result["changes_made"].append(f"Backed up for deletion: {file_path}")
                else:
                    step_result["error"] = f"Failed to backup file for deletion: {backup_result.error}"
            
            else:
                step_result["error"] = f"Unknown change type: {change_type}"
            
        except Exception as e:
            step_result["error"] = f"Step implementation error: {str(e)}"
        
        return step_result
    
    async def _intelligent_modification(self, step: Dict, filesystem_tool, step_result: Dict) -> Dict:
        """Make intelligent modifications when specific code is not provided."""
        
        file_path = step.get("file", "")
        description = step.get("description", "")
        
        try:
            # Read current file content
            read_result = await filesystem_tool.execute("read_file", path=file_path)
            if not read_result.success:
                step_result["error"] = f"Cannot read file for modification: {read_result.error}"
                return step_result
            
            current_content = read_result.output
            
            # Create backup
            backup_result = await filesystem_tool.execute("backup_file", path=file_path)
            if backup_result.success:
                step_result["backup_created"] = backup_result.metadata.get("backup_path")
            
            # Use LLM to generate the improved code
            improvement_prompt = f"""You are modifying code to implement this improvement:

DESCRIPTION: {description}

CURRENT CODE:
```
{current_content}
```

Provide the complete improved code for the file. Only output the code, no explanations."""
            
            messages = [
                {"role": "system", "content": improvement_prompt}
            ]
            
            response = await self.llm.generate(messages)
            improved_code = response.content.strip()
            
            # Remove potential code block markers
            if improved_code.startswith('```'):
                lines = improved_code.split('\n')
                improved_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else improved_code
            
            # Write improved code
            write_result = await filesystem_tool.execute("write_file", path=file_path, content=improved_code)
            if write_result.success:
                step_result["success"] = True
                step_result["changes_made"].append(f"Intelligently modified file: {file_path}")
            else:
                step_result["error"] = f"Failed to write improved code: {write_result.error}"
        
        except Exception as e:
            step_result["error"] = f"Intelligent modification failed: {str(e)}"
        
        return step_result
    
    def _generate_implementation_summary(self, results: List[Dict], successful: int, failed: int) -> str:
        """Generate implementation summary."""
        
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        summary = f"""Implementation Summary:
- Total Steps: {total}
- Successful: {successful} ({success_rate:.1f}%)
- Failed: {failed}

Changes Made:
"""
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            summary += f"{status} Step {result['step_number']}: {result['title']}\n"
            
            for change in result.get("changes_made", []):
                summary += f"   • {change}\n"
            
            if result.get("backup_created"):
                summary += f"   • Backup: {result['backup_created']}\n"
            
            if result.get("error"):
                summary += f"   • Error: {result['error']}\n"
            
            summary += "\n"
        
        return summary
    
    def _generate_results_report(self, results: List[Dict], summary: str) -> str:
        """Generate detailed implementation results report."""
        
        report = f"""# Implementation Results Report

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
{summary}

## Detailed Results

"""
        
        for result in results:
            status_icon = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            
            report += f"""### Step {result['step_number']}: {result['title']} - {status_icon}

**File:** `{result['file']}`
**Change Type:** {result['change_type']}

"""
            
            if result.get("changes_made"):
                report += "**Changes Made:**\n"
                for change in result["changes_made"]:
                    report += f"- {change}\n"
                report += "\n"
            
            if result.get("backup_created"):
                report += f"**Backup Created:** `{result['backup_created']}`\n\n"
            
            if result.get("error"):
                report += f"**Error:** {result['error']}\n\n"
            
            report += "---\n\n"
        
        return report
