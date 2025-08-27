"""Plan improvements action for code improvement scenarios."""

from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult
from ..core.logging import get_logger, timed_operation

logger = get_logger("plan_improvements")


class PlanImprovementsAction(BaseAction):
    """Action to plan specific code improvements based on analysis."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["recommendations", "goal"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        recommendations = context.get("recommendations")
        goal = context.get("goal")
        return recommendations is not None and goal is not None
    
    @timed_operation("plan_improvements", "code_improvement")
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute improvement planning."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required fields 'recommendations' or 'goal'")
            
            recommendations = context.get("recommendations", [])
            goal = context.get("goal")
            analysis = context.get("llm_analysis", "")
            directory_analysis = context.get("directory_analysis", {})
            
            logger.info(f"Planning improvements for goal: {goal}")
            logger.info(f"Working with {len(recommendations)} recommendations")
            
            # Get filesystem tool for file inspection
            filesystem_tool = self.tools.get("secure_filesystem")
            if not filesystem_tool:
                return ActionResult.error_result("Secure filesystem tool not available")
            
            # Read relevant files to understand current implementation
            file_contents = {}
            relevant_files = set()
            
            # Collect files mentioned in recommendations
            for rec in recommendations:
                if 'files' in rec:
                    relevant_files.update(rec.get('files', []))
            
            # If no specific files mentioned, try to find relevant ones
            if not relevant_files:
                # Get code files from directory analysis
                file_tree = directory_analysis.get('file_tree', [])
                code_files = [item['path'] for item in file_tree 
                             if item.get('type') == 'file' and item.get('extension', '').lower() in 
                             ['.py', '.js', '.ts', '.java', '.cpp', '.h']][:5]  # Limit to 5 files
                relevant_files.update(code_files)
            
            # Read file contents
            for file_path in list(relevant_files)[:10]:  # Limit to 10 files
                result = await filesystem_tool.execute("read_file", path=file_path)
                if result.success:
                    file_contents[file_path] = result.output
                    logger.debug(f"Read file for planning: {file_path}")
                else:
                    logger.warning(f"Could not read file {file_path}: {result.error}")
            
            # Build planning prompt
            planning_prompt = self._build_planning_prompt(goal, recommendations, analysis, file_contents)
            
            # Get LLM planning
            messages = [
                {"role": "system", "content": planning_prompt},
                {"role": "user", "content": f"Create a detailed implementation plan for: {goal}"}
            ]
            
            response = await self.llm.generate(messages)
            
            # Parse response to extract implementation plan
            implementation_plan = self._parse_planning_response(response.content, recommendations)
            
            logger.info(f"Implementation plan created with {len(implementation_plan)} steps")
            
            return ActionResult.success_result(
                data={
                    "implementation_plan": implementation_plan,
                    "analyzed_files": list(file_contents.keys()),
                    "planning_response": response.content,
                    "goal": goal,
                    "selected_recommendations": recommendations
                },
                artifacts={
                    "implementation_plan.md": self._generate_plan_document(implementation_plan, goal)
                }
            )
            
        except Exception as e:
            logger.error(f"Improvement planning failed: {e}", error=str(e))
            return ActionResult.error_result(f"Planning failed: {str(e)}")
    
    def _build_planning_prompt(self, goal: str, recommendations: List[Dict], 
                             analysis: str, file_contents: Dict[str, str]) -> str:
        """Build planning prompt for LLM."""
        
        files_summary = ""
        if file_contents:
            files_summary = "CURRENT CODE FILES:\n"
            for file_path, content in file_contents.items():
                # Truncate very long files
                truncated_content = content[:2000] + "..." if len(content) > 2000 else content
                files_summary += f"\n--- {file_path} ---\n{truncated_content}\n"
        
        recommendations_text = ""
        for i, rec in enumerate(recommendations, 1):
            recommendations_text += f"{i}. {rec.get('title', 'Unknown')}: {rec.get('description', '')}\n"
        
        return f"""You are an expert software engineer. Your task is to make MINIMAL changes to achieve the goal.

GOAL: {goal}

PREVIOUS ANALYSIS:
{analysis}

RECOMMENDATIONS TO IMPLEMENT:
{recommendations_text}

{files_summary}

IMPORTANT INSTRUCTIONS:
1. **Do ONLY what is asked** - no extra features, no refactoring, no documentation
2. **Maximum 2-3 steps** for simple tasks
3. **Be precise** - find exact text and replace it exactly
4. **No file creation** unless explicitly requested
5. **No structural changes** unless necessary

RESPONSE FORMAT:
## Implementation Plan

### Step 1: [Main Change]
- **File:** filename.ext
- **Change Type:** modification
- **Description:** Exact change needed
- **Code:** 
```language
OLD: exact text to find
NEW: exact text to replace with
```

### Step 2: [Additional Change - ONLY if absolutely necessary]
[Same format]

## Validation Steps
[How to verify the main goal is achieved]

Remember: SIMPLE and PRECISE changes only. Do not over-engineer."""
    
    def _parse_planning_response(self, response: str, recommendations: List[Dict]) -> List[Dict]:
        """Parse planning response into structured implementation steps."""
        
        implementation_steps = []
        lines = response.split('\n')
        
        current_step = None
        current_section = None
        current_code_block = []
        in_code_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Detect step headers
            if stripped_line.startswith('### Step'):
                if current_step:
                    implementation_steps.append(current_step)
                
                # Extract step title
                step_title = stripped_line.replace('### Step', '').strip()
                step_title = step_title.split(':', 1)[-1].strip() if ':' in step_title else step_title
                
                current_step = {
                    "step_number": len(implementation_steps) + 1,
                    "title": step_title,
                    "file": "",
                    "change_type": "modification",
                    "description": "",
                    "code": "",
                    "validation": ""
                }
                current_section = None
                continue
            
            # Detect code blocks
            if stripped_line.startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_step:
                        current_step["code"] = '\n'.join(current_code_block)
                    current_code_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                    current_code_block = []
                continue
            
            if in_code_block:
                current_code_block.append(line)
                continue
            
            # Parse step content
            if current_step and stripped_line:
                if stripped_line.startswith('- **File:**'):
                    file_path = stripped_line.replace('- **File:**', '').strip()
                    # Clean up any markdown artifacts (backticks, brackets, parentheses, etc.)
                    file_path = file_path.strip('`').strip('()').strip('[]').strip()
                    # Remove common markdown suffixes
                    file_path = file_path.replace('` (assuming a test file exists)', '').strip()
                    # Normalize path - remove directory prefixes to make relative
                    if '/' in file_path:
                        file_path = file_path.split('/')[-1]  # Take only filename
                    current_step["file"] = file_path
                elif stripped_line.startswith('- **Change Type:**'):
                    change_type = stripped_line.replace('- **Change Type:**', '').strip().lower()
                    # Clean up markdown artifacts and brackets
                    change_type = change_type.strip('`').strip('[]').strip()
                    current_step["change_type"] = change_type
                elif stripped_line.startswith('- **Description:**'):
                    description = stripped_line.replace('- **Description:**', '').strip()
                    # Clean up markdown artifacts
                    description = description.strip('`').strip()
                    current_step["description"] = description
                elif stripped_line.startswith('- **Validation:**'):
                    validation = stripped_line.replace('- **Validation:**', '').strip()
                    # Clean up markdown artifacts
                    validation = validation.strip('`').strip()
                    current_step["validation"] = validation
                elif not stripped_line.startswith('-') and not stripped_line.startswith('#'):
                    # Continue description
                    cleaned_line = stripped_line.strip('`').strip()
                    if current_step["description"]:
                        current_step["description"] += " " + cleaned_line
                    else:
                        current_step["description"] = cleaned_line
        
        # Add the last step
        if current_step:
            implementation_steps.append(current_step)
        
        # If no structured steps found, create basic ones from recommendations
        if not implementation_steps:
            for i, rec in enumerate(recommendations, 1):
                implementation_steps.append({
                    "step_number": i,
                    "title": rec.get('title', f'Improvement {i}'),
                    "file": rec.get('files', [''])[0] if rec.get('files') else '',
                    "change_type": "modification",
                    "description": rec.get('description', ''),
                    "code": "",
                    "validation": "Review and test changes"
                })
        
        return implementation_steps
    
    def _generate_plan_document(self, implementation_plan: List[Dict], goal: str) -> str:
        """Generate implementation plan document."""
        
        plan_doc = f"""# Implementation Plan

**Goal:** {goal}
**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
This plan outlines {len(implementation_plan)} implementation steps to achieve the specified goal.

"""
        
        for step in implementation_plan:
            plan_doc += f"""## Step {step['step_number']}: {step['title']}

**File:** `{step['file']}`
**Change Type:** {step['change_type']}

**Description:**
{step['description']}

"""
            if step['code']:
                # Try to detect language from file extension
                file_ext = step['file'].split('.')[-1] if step['file'] else 'text'
                lang_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'java': 'java', 'cpp': 'cpp', 'h': 'cpp'}
                lang = lang_map.get(file_ext, 'text')
                
                plan_doc += f"""**Code Changes:**
```{lang}
{step['code']}
```

"""
            
            if step['validation']:
                plan_doc += f"""**Validation:**
{step['validation']}

"""
            
            plan_doc += "---\n\n"
        
        plan_doc += """## Next Steps

1. Review each step carefully
2. Implement changes in order
3. Test after each step
4. Validate final implementation

"""
        
        return plan_doc
