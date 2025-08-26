"""Implement changes action for code improvement scenarios."""

from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult
from ..core.logging import get_logger, timed_operation

logger = get_logger("implement_changes")


class ImplementChangesAction(BaseAction):
    """Action to implement planned code improvements."""
    
    def __init__(self, llm_provider, tools):
        super().__init__(llm_provider, tools)
        self.logger = get_logger("implement_changes")
    
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
            
            self.logger.info(f"Implementing {len(implementation_plan)} planned changes")
            
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
                    self.logger.info(f"✅ Step {step['step_number']}: {step['title']}")
                else:
                    failed_changes += 1
                    self.logger.error(f"❌ Step {step['step_number']}: {step_result['error']}")
            
            # Generate summary
            summary = self._generate_implementation_summary(results, successful_changes, failed_changes)
            
            self.logger.info(f"Implementation completed: {successful_changes} successful, {failed_changes} failed")
            
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
            self.logger.error(f"Implementation failed: {e}", error=str(e))
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
            
            elif change_type == "modification" or change_type == "edit" or change_type == "modify_file":
                # Modify existing file with smart line-by-line changes
                if code:
                    # Read existing file first
                    read_result = await filesystem_tool.execute("read_file", path=file_path)
                    if not read_result.success:
                        step_result["error"] = f"Failed to read existing file: {read_result.error}"
                        return step_result
                    
                    current_content = read_result.content
                    
                    # Create backup first
                    backup_result = await filesystem_tool.execute("backup_file", path=file_path)
                    if backup_result.success:
                        step_result["backup_created"] = backup_result.metadata.get("backup_path")
                    
                    # Apply smart diff-based changes instead of full replacement
                    modified_content = await self._apply_smart_changes(
                        current_content, code, description
                    )
                    
                    # Write modified content
                    result = await filesystem_tool.execute("write_file", path=file_path, content=modified_content)
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
                # Handle unknown or non-file change types by skipping them with a warning
                if change_type in ["review", "analysis", "documentation", "note", "addition/modification"]:
                    step_result["status"] = "skipped"
                    step_result["message"] = f"Skipping non-file change type: {change_type}"
                    self.logger.info(f"⚠️ Step {step_idx + 1}: Skipped non-file change: {change_type}")
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
    
    async def _apply_smart_changes(self, current_content: str, new_code: str, description: str) -> str:
        """Apply smart changes to existing content instead of full replacement."""
        
        # If the new code is significantly shorter than current content,
        # it's likely a targeted change, not a full replacement
        current_lines = current_content.split('\n')
        new_lines = new_code.split('\n')
        
        # If new code is less than 50% of original, treat as targeted change
        if len(new_lines) < len(current_lines) * 0.5:
            # Look for best match in the current content to replace
            return self._find_and_replace_section(current_content, new_code, description)
        
        # If the new code is similar length, check for line-by-line changes
        if abs(len(new_lines) - len(current_lines)) <= 5:
            return self._merge_line_changes(current_content, new_code)
        
        # Default to full replacement if we can't determine targeted changes
        return new_code
    
    def _find_and_replace_section(self, current_content: str, new_code: str, description: str) -> str:
        """Find the best section to replace based on description and new code."""
        
        current_lines = current_content.split('\n')
        new_lines = new_code.split('\n')
        
        # Look for comments or function names mentioned in description
        keywords = description.lower().split()
        
        best_match_start = 0
        best_match_score = 0
        
        # Search for the best location to insert the new code
        for i in range(len(current_lines) - len(new_lines) + 1):
            score = 0
            section = '\n'.join(current_lines[i:i+len(new_lines)])
            
            # Score based on similar words
            for keyword in keywords:
                if keyword in section.lower():
                    score += 1
            
            # Score based on similar structure (functions, classes, etc.)
            if any(line.strip().startswith(('def ', 'class ', '#')) for line in new_lines):
                section_lines = current_lines[i:i+len(new_lines)]
                if any(line.strip().startswith(('def ', 'class ', '#')) for line in section_lines):
                    score += 2
            
            if score > best_match_score:
                best_match_score = score
                best_match_start = i
        
        # Replace the best matching section
        if best_match_score > 0:
            result_lines = current_lines[:best_match_start] + new_lines + current_lines[best_match_start + len(new_lines):]
            return '\n'.join(result_lines)
        
        # If no good match found, append at the end
        return current_content + '\n\n' + new_code
    
    def _merge_line_changes(self, current_content: str, new_code: str) -> str:
        """Merge line-by-line changes when content is similar length."""
        
        current_lines = current_content.split('\n')
        new_lines = new_code.split('\n')
        
        # Simple line-by-line merge - replace changed lines
        result_lines = []
        
        for i, new_line in enumerate(new_lines):
            if i < len(current_lines):
                # If lines are substantially different, use new line
                if len(new_line.strip()) > 0 and new_line.strip() != current_lines[i].strip():
                    result_lines.append(new_line)
                else:
                    result_lines.append(current_lines[i])
            else:
                result_lines.append(new_line)
        
        # Add any remaining original lines
        if len(current_lines) > len(new_lines):
            result_lines.extend(current_lines[len(new_lines):])
        
        return '\n'.join(result_lines)
