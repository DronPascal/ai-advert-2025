"""Analyze codebase action for code improvement scenarios."""

from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult
from ..core.logging import get_logger, timed_operation

logger = get_logger("analyze_codebase")


class AnalyzeCodebaseAction(BaseAction):
    """Action to analyze codebase structure and identify improvement opportunities."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["target_directory"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        target_dir = context.get("target_directory")
        return target_dir is not None
    
    @timed_operation("analyze_codebase", "code_improvement")
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute codebase analysis."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required field 'target_directory'")
            
            target_directory = context.get("target_directory")
            goal = context.get("goal", "General code improvement")
            
            # Use secure filesystem tool to analyze directory
            filesystem_tool = self.tools.get("secure_filesystem")
            if not filesystem_tool:
                return ActionResult.error_result("Secure filesystem tool not available")
            
            logger.info(f"Analyzing codebase in: {target_directory}")
            
            # Get directory analysis
            # Limit analysis to avoid token overflow
            analysis_result = await filesystem_tool.execute("analyze_directory", path=".", max_files=15)
            if not analysis_result.success:
                return ActionResult.error_result(f"Directory analysis failed: {analysis_result.error}")
            
            # Get file tree structure
            # Limit tree depth to save tokens
            tree_result = await filesystem_tool.execute("get_file_tree", path=".", max_depth=2)
            if not tree_result.success:
                logger.warning(f"File tree generation failed: {tree_result.error}")
                tree_output = "File tree not available"
            else:
                tree_output = tree_result.output
            
            analysis_data = analysis_result.metadata
            
            # Build comprehensive analysis prompt
            analysis_prompt = self._build_analysis_prompt(goal, analysis_data, tree_output)
            
            # Get LLM analysis
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"Goal: {goal}\n\nAnalyze this codebase and provide improvement recommendations."}
            ]
            
            response = await self.llm.generate(messages)
            
            # Parse the response to extract structured analysis
            analysis, recommendations = self._parse_analysis_response(response.content, analysis_data)
            
            logger.info(f"Codebase analysis completed. Found {len(recommendations)} recommendations")
            
            return ActionResult.success_result(
                data={
                    "directory_analysis": analysis_data,
                    "file_tree": tree_output,
                    "llm_analysis": analysis,
                    "recommendations": recommendations,
                    "goal": goal
                },
                artifacts={
                    "analysis_report.md": self._generate_analysis_report(analysis, recommendations, analysis_data)
                }
            )
            
        except Exception as e:
            logger.error(f"Codebase analysis failed: {e}", error=str(e))
            return ActionResult.error_result(f"Analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, goal: str, analysis_data: Dict, tree_output: str) -> str:
        """Build optimized analysis prompt for LLM with token efficiency focus."""
        # Extract key metrics for concise summary
        total_files = analysis_data.get('total_files', 0)
        code_files = analysis_data.get('code_files', 0)
        languages = ', '.join(analysis_data.get('languages', {}).keys()) or 'unknown'
        summary = analysis_data.get('summary', 'No summary available')

        # Truncate tree output to essential information only (max 200 chars)
        tree_preview = tree_output[:200] + '...' if len(tree_output) > 200 else tree_output

        return f"""Analyze for: {goal}

OVERVIEW:
- Files: {total_files} total, {code_files} code
- Languages: {languages}

STRUCTURE:
{tree_preview}

TASK:
- Focus on: {goal}
- Find files needing changes
- Prioritize actionable items

FORMAT:
## Summary
[2 sentences]

## Recommendations
[Priority: File - Change - Why]"""
    
    def _parse_analysis_response(self, response: str, analysis_data: Dict) -> tuple[str, List[Dict]]:
        """Parse LLM response to extract analysis and recommendations."""
        
        # Extract recommendations from the response
        recommendations = []
        lines = response.split('\n')
        
        current_section = None
        current_recommendation = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## Improvement Recommendations'):
                current_section = 'recommendations'
                continue
            elif line.startswith('##'):
                current_section = None
                if current_recommendation:
                    recommendations.append(current_recommendation)
                    current_recommendation = {}
                continue
            
            if current_section == 'recommendations' and line:
                if line.startswith('-') or line.startswith('*') or line.startswith('1.'):
                    # This is a recommendation item
                    if current_recommendation:
                        recommendations.append(current_recommendation)
                    
                    # Clean up the line
                    recommendation_text = line.lstrip('- *1234567890.')
                    current_recommendation = {
                        "title": recommendation_text.strip(),
                        "priority": "medium",  # Default priority
                        "type": "improvement",
                        "files": [],
                        "description": recommendation_text.strip()
                    }
                    
                    # Try to extract file mentions
                    for file_info in analysis_data.get('file_tree', []):
                        if 'path' in file_info and file_info['path'] in recommendation_text:
                            current_recommendation['files'].append(file_info['path'])
        
        # Add the last recommendation if exists
        if current_recommendation:
            recommendations.append(current_recommendation)
        
        # If no structured recommendations found, create basic ones
        if not recommendations:
            recommendations = [{
                "title": "General code improvement",
                "priority": "medium",
                "type": "improvement", 
                "files": [],
                "description": "Review and improve code based on analysis"
            }]
        
        return response, recommendations
    
    def _generate_analysis_report(self, analysis: str, recommendations: List[Dict], analysis_data: Dict) -> str:
        """Generate a comprehensive analysis report."""
        report = f"""# Codebase Analysis Report

## Directory Analysis
- **Total Files:** {analysis_data.get('total_files', 0)}
- **Code Files:** {analysis_data.get('code_files', 0)}
- **Languages:** {', '.join(analysis_data.get('languages', {}).keys())}

## Analysis Summary
{analysis}

## Recommendations Summary
{len(recommendations)} recommendations identified:

"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. **{rec['title']}** (Priority: {rec['priority']})\n"
            report += f"   - {rec['description']}\n"
            if rec['files']:
                report += f"   - Files: {', '.join(rec['files'])}\n"
            report += "\n"
        
        return report
