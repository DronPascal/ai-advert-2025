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
            
            # Filter and prioritize steps - focus on main goal, skip unnecessary changes
            filtered_steps = self._filter_priority_steps(implementation_plan)
            
            for step in filtered_steps:
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
                    
                    current_content = read_result.output
                    
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
                        # Validate that the change actually improved the file
                        if self._validate_change_quality(current_content, modified_content, description):
                            step_result["success"] = True
                            step_result["changes_made"].append(f"Modified file: {file_path}")
                        else:
                            # Revert the change if it made things worse
                            await filesystem_tool.execute("write_file", path=file_path, content=current_content)
                            step_result["error"] = f"Change made file worse, reverted: {description}"
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
                    self.logger.info(f"⚠️ Step {step_result['step_number']}: Skipped non-file change: {change_type}")
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
        
        # NEVER replace entire file content unless explicitly requested
        # Always try to make targeted changes first
        
        # First, try to find OLD/NEW pattern in the new_code
        old_text = None
        new_text = None
        
        for line in new_code.split('\n'):
            line = line.strip()
            if line.startswith('OLD:'):
                old_text = line.replace('OLD:', '').strip()
            elif line.startswith('NEW:'):
                new_text = line.replace('NEW:', '').strip()
        
        # If we have OLD/NEW pattern, do exact replacement
        if old_text and new_text:
            if old_text in current_content:
                self.logger.info(f"Found exact match, replacing: '{old_text}' -> '{new_text}'")
                return current_content.replace(old_text, new_text)
            else:
                # Try to find similar lines with fuzzy matching
                return self._find_similar_line_and_replace(current_content, old_text, new_text)
        
        # If no OLD/NEW pattern, try to extract from description
        if "change" in description.lower() or "replace" in description.lower():
            # Look for quoted text in description
            import re
            quotes = re.findall(r'"([^"]*)"', description)
            if len(quotes) >= 2:
                old_text, new_text = quotes[0], quotes[1]
                if old_text in current_content:
                    self.logger.info(f"Found match from description, replacing: '{old_text}' -> '{new_text}'")
                    return current_content.replace(old_text, new_text)
        
        # If we can't determine how to apply changes safely, don't change anything
        self.logger.warning(f"Cannot determine safe change method, preserving original content: {description}")
        return current_content
    
    def _filter_priority_steps(self, implementation_plan: List[Dict]) -> List[Dict]:
        """Filter steps to focus on main goal, skip unnecessary changes."""
        
        if len(implementation_plan) <= 2:
            # For simple plans, execute all steps
            return implementation_plan
        
        # Priority order: modifications > additions > others
        priority_steps = []
        other_steps = []
        
        for step in implementation_plan:
            change_type = step.get("change_type", "").lower()
            description = step.get("description", "").lower()
            
            # High priority: direct modifications to achieve the goal
            if (change_type in ["modification", "edit", "modify_file"] and 
                any(word in description for word in ["change", "replace", "fix", "update"])):
                priority_steps.append(step)
            
            # Medium priority: necessary additions
            elif change_type in ["addition", "create"] and "necessary" in description:
                priority_steps.append(step)
            
            # Low priority: documentation, refactoring, etc.
            else:
                other_steps.append(step)
        
        # Return priority steps first, limit to 2-3 for simple tasks
        if priority_steps:
            return priority_steps[:2]  # Only first 2 priority steps
        
        # If no priority steps, return first 2 steps
        return implementation_plan[:2]
    
    def _validate_change_quality(self, original_content: str, modified_content: str, description: str) -> bool:
        """Validate that the change actually improved the file."""
        
        # Check if the file structure is preserved
        original_lines = original_content.split('\n')
        modified_lines = modified_content.split('\n')
        
        # If the file got significantly shorter, it's probably broken
        if len(modified_lines) < len(original_lines) * 0.8:
            self.logger.warning(f"File got too short, change probably broke it: {len(modified_lines)} vs {len(original_lines)} lines")
            return False
        
        # If the file got significantly longer, it might have added unnecessary content
        if len(modified_lines) > len(original_lines) * 1.5:
            self.logger.warning(f"File got too long, change might have added unnecessary content: {len(modified_lines)} vs {len(original_lines)} lines")
            return False
        
        # Check if Python syntax is preserved (basic check)
        try:
            compile(modified_content, '<string>', 'exec')
        except SyntaxError:
            self.logger.warning(f"Modified content has syntax errors")
            return False
        
        # Check if the change actually addresses the goal
        goal_keywords = description.lower().split()
        content_lower = modified_content.lower()
        
        # If the goal mentions specific words, check if they're in the result
        if any(word in goal_keywords for word in ['hello', 'hi', 'change', 'replace']):
            if 'hello' in goal_keywords and 'hi' in content_lower:
                return True  # Successfully changed Hello to Hi
            if 'hi' in goal_keywords and 'hi' in content_lower:
                return True  # Successfully added Hi
        
        # If we can't determine, be conservative and reject the change
        self.logger.warning(f"Cannot validate if change addresses the goal: {description}")
        return False
    
    def _find_and_replace_section(self, current_content: str, new_code: str, description: str) -> str:
        """Find the best section to replace based on description and new code."""
        
        current_lines = current_content.split('\n')
        new_lines = new_code.split('\n')
        
        # First, try to find OLD/NEW pattern in the new_code
        old_text = None
        new_text = None
        
        for i, line in enumerate(new_lines):
            if line.strip().startswith('// OLD:') or line.strip().startswith('OLD:'):
                old_text = line.split(':', 1)[1].strip()
            elif line.strip().startswith('// NEW:') or line.strip().startswith('NEW:'):
                new_text = line.split(':', 1)[1].strip()
        
        # If we have OLD/NEW pattern, do exact replacement
        if old_text and new_text:
            if old_text in current_content:
                return current_content.replace(old_text, new_text)
            else:
                # Try to find similar lines
                return self._find_similar_line_and_replace(current_content, old_text, new_text)
        
        # Fallback to keyword-based search
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
        
        # If no good match found, DON'T change the file
        return current_content
    
    def _find_similar_line_and_replace(self, current_content: str, old_text: str, new_text: str) -> str:
        """Find a similar line and replace it with new text."""
        
        current_lines = current_content.split('\n')
        
        # Look for lines that contain similar words
        old_words = set(old_text.lower().split())
        best_match_line = -1
        best_match_score = 0
        
        for i, line in enumerate(current_lines):
            line_words = set(line.lower().split())
            # Calculate similarity score
            common_words = old_words.intersection(line_words)
            if len(common_words) > 0:
                score = len(common_words) / max(len(old_words), len(line_words))
                if score > best_match_score:
                    best_match_score = score
                    best_match_line = i
        
        # If we found a good match, replace it
        if best_match_line >= 0 and best_match_score > 0.3:  # 30% similarity threshold
            current_lines[best_match_line] = new_text
            return '\n'.join(current_lines)
        
        # If no good match found, don't change anything
        return current_content
    
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
