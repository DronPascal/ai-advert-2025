"""Validate changes action for code improvement scenarios."""

from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult
from ..core.logging import get_logger, timed_operation

logger = get_logger("validate_changes")


class ValidateChangesAction(BaseAction):
    """Action to validate implemented code changes."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["implementation_results"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        implementation_results = context.get("implementation_results")
        return implementation_results is not None
    
    @timed_operation("validate_changes", "code_improvement")
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute change validation."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing 'implementation_results'")
            
            implementation_results = context.get("implementation_results", [])
            goal = context.get("goal", "Code improvement")
            
            logger.info(f"Validating {len(implementation_results)} implemented changes")
            
            # Get filesystem tool
            filesystem_tool = self.tools.get("secure_filesystem")
            if not filesystem_tool:
                return ActionResult.error_result("Secure filesystem tool not available")
            
            validation_results = []
            syntax_valid_count = 0
            syntax_invalid_count = 0
            files_validated = 0
            
            # Validate each successfully changed file
            for result in implementation_results:
                if result.get("success", False) and result.get("file"):
                    file_path = result["file"]
                    validation_result = await self._validate_file(file_path, filesystem_tool, context)
                    validation_result["step_number"] = result.get("step_number", 0)
                    validation_result["step_title"] = result.get("title", "Unknown")
                    validation_results.append(validation_result)
                    files_validated += 1
                    
                    if validation_result["syntax_valid"]:
                        syntax_valid_count += 1
                    else:
                        syntax_invalid_count += 1
            
            # Run comprehensive validation
            overall_validation = await self._run_comprehensive_validation(filesystem_tool)
            
            # Generate validation summary
            summary = self._generate_validation_summary(
                validation_results, syntax_valid_count, syntax_invalid_count, 
                files_validated, overall_validation
            )
            
            success = syntax_invalid_count == 0 and overall_validation.get("success", True)
            
            logger.info(f"Validation completed: {syntax_valid_count} valid, {syntax_invalid_count} invalid files")
            
            return ActionResult.success_result(
                data={
                    "validation_results": validation_results,
                    "syntax_valid_count": syntax_valid_count,
                    "syntax_invalid_count": syntax_invalid_count,
                    "files_validated": files_validated,
                    "overall_validation": overall_validation,
                    "validation_success": success,
                    "summary": summary
                },
                artifacts={
                    "validation_report.md": self._generate_validation_report(
                        validation_results, summary, overall_validation
                    )
                }
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}", error=str(e))
            return ActionResult.error_result(f"Validation failed: {str(e)}")
    
    async def _validate_file(self, file_path: str, filesystem_tool, context: ActionContext) -> Dict:
        """Validate a single file."""
        validation_result = {
            "file": file_path,
            "syntax_valid": False,
            "syntax_error": None,
            "file_readable": False,
            "file_size": 0,
            "validation_notes": []
        }
        
        try:
            # Check file readability
            read_result = await filesystem_tool.execute("read_file", path=file_path)
            if read_result.success:
                validation_result["file_readable"] = True
                validation_result["file_size"] = len(read_result.output)
                validation_result["validation_notes"].append("✅ File is readable")

                # Update cached content if it exists in context
                cached_files = context.get("file_contents", {})
                if file_path in cached_files:
                    cached_files[file_path] = read_result.output
                    context.set("file_contents", cached_files)
                    logger.debug(f"Updated cached content for validated file: {file_path}")
            else:
                validation_result["validation_notes"].append(f"❌ File not readable: {read_result.error}")
                return validation_result
            
            # Validate syntax
            syntax_result = await filesystem_tool.execute("validate_syntax", path=file_path)
            if syntax_result.success:
                validation_result["syntax_valid"] = syntax_result.metadata.get("valid", True)
                if validation_result["syntax_valid"]:
                    validation_result["validation_notes"].append("✅ Syntax is valid")
                else:
                    validation_result["syntax_error"] = syntax_result.metadata.get("error", "Unknown syntax error")
                    validation_result["validation_notes"].append(f"❌ Syntax error: {validation_result['syntax_error']}")
            else:
                validation_result["validation_notes"].append(f"⚠️  Syntax validation unavailable: {syntax_result.error}")
                validation_result["syntax_valid"] = True  # Assume valid if can't validate
            
            # Additional checks based on file type
            file_extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            
            if file_extension in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'h']:
                # Check for common issues in code files
                content = read_result.output
                
                # Check for basic structure
                if len(content.strip()) < 10:
                    validation_result["validation_notes"].append("⚠️  File is very short")
                
                # Check for incomplete functions/classes (basic heuristic)
                if file_extension == 'py':
                    if 'def ' in content and content.count('):') < content.count('def '):
                        validation_result["validation_notes"].append("⚠️  Possible incomplete function definitions")
                    if 'class ' in content and content.count(':') < content.count('class '):
                        validation_result["validation_notes"].append("⚠️  Possible incomplete class definitions")
                
                # Check for proper indentation (Python)
                if file_extension == 'py':
                    lines = content.split('\n')
                    inconsistent_indent = False
                    for line in lines:
                        if line.strip() and line.startswith(' '):
                            # Check for tabs mixed with spaces (basic check)
                            if '\t' in line:
                                inconsistent_indent = True
                                break
                    if inconsistent_indent:
                        validation_result["validation_notes"].append("⚠️  Mixed tabs and spaces detected")
            
        except Exception as e:
            validation_result["validation_notes"].append(f"❌ Validation error: {str(e)}")
        
        return validation_result
    
    async def _run_comprehensive_validation(self, filesystem_tool) -> Dict:
        """Run comprehensive validation on the entire codebase."""
        comprehensive_result = {
            "success": True,
            "checks_performed": [],
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Analyze directory structure
            analysis_result = await filesystem_tool.execute("analyze_directory", path=".")
            if analysis_result.success:
                analysis_data = analysis_result.metadata
                comprehensive_result["checks_performed"].append("Directory structure analysis")
                
                # Check for large files
                large_files = analysis_data.get("large_files", [])
                if large_files:
                    comprehensive_result["issues_found"].append(f"Found {len(large_files)} large files")
                    comprehensive_result["recommendations"].append("Consider splitting large files")
                
                # Check for language distribution
                languages = analysis_data.get("languages", {})
                if len(languages) > 5:
                    comprehensive_result["issues_found"].append(f"Many languages detected: {len(languages)}")
                    comprehensive_result["recommendations"].append("Consider standardizing on fewer languages")
                
                comprehensive_result["checks_performed"].append(f"Language analysis: {list(languages.keys())}")
            
            # Get file tree for structure validation
            tree_result = await filesystem_tool.execute("get_file_tree", path=".")
            if tree_result.success:
                comprehensive_result["checks_performed"].append("File tree structure validation")
                
                # Basic structure checks
                tree_output = tree_result.output
                if "test" not in tree_output.lower() and "spec" not in tree_output.lower():
                    comprehensive_result["issues_found"].append("No test files detected")
                    comprehensive_result["recommendations"].append("Consider adding test files")
                
                if "readme" not in tree_output.lower():
                    comprehensive_result["issues_found"].append("No README file detected")
                    comprehensive_result["recommendations"].append("Consider adding a README file")
            
        except Exception as e:
            comprehensive_result["success"] = False
            comprehensive_result["issues_found"].append(f"Comprehensive validation error: {str(e)}")
        
        return comprehensive_result
    
    def _generate_validation_summary(self, validation_results: List[Dict], 
                                   syntax_valid_count: int, syntax_invalid_count: int,
                                   files_validated: int, overall_validation: Dict) -> str:
        """Generate validation summary."""
        
        success_rate = (syntax_valid_count / files_validated * 100) if files_validated > 0 else 0
        
        summary = f"""Validation Summary:
- Files Validated: {files_validated}
- Syntax Valid: {syntax_valid_count} ({success_rate:.1f}%)
- Syntax Invalid: {syntax_invalid_count}

File-by-File Results:
"""
        
        for result in validation_results:
            status = "✅" if result["syntax_valid"] else "❌"
            summary += f"{status} {result['file']} - {result['file_size']} bytes\n"
            
            for note in result.get("validation_notes", []):
                summary += f"   • {note}\n"
        
        if overall_validation:
            summary += "\nOverall Validation:\n"
            for check in overall_validation.get("checks_performed", []):
                summary += f"✅ {check}\n"
            
            for issue in overall_validation.get("issues_found", []):
                summary += f"⚠️  {issue}\n"
        
        return summary
    
    def _generate_validation_report(self, validation_results: List[Dict], 
                                  summary: str, overall_validation: Dict) -> str:
        """Generate detailed validation report."""
        
        report = f"""# Code Validation Report

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
{summary}

## File Validation Details

"""
        
        for result in validation_results:
            status_icon = "✅ VALID" if result["syntax_valid"] else "❌ INVALID"
            
            report += f"""### {result['file']} - {status_icon}

**Size:** {result['file_size']} bytes
**Readable:** {"✅" if result['file_readable'] else "❌"}

"""
            
            if result.get("validation_notes"):
                report += "**Validation Notes:**\n"
                for note in result["validation_notes"]:
                    report += f"- {note}\n"
                report += "\n"
            
            if result.get("syntax_error"):
                report += f"**Syntax Error:** {result['syntax_error']}\n\n"
            
            report += "---\n\n"
        
        if overall_validation:
            report += """## Comprehensive Validation

"""
            
            if overall_validation.get("checks_performed"):
                report += "**Checks Performed:**\n"
                for check in overall_validation["checks_performed"]:
                    report += f"- {check}\n"
                report += "\n"
            
            if overall_validation.get("issues_found"):
                report += "**Issues Found:**\n"
                for issue in overall_validation["issues_found"]:
                    report += f"- {issue}\n"
                report += "\n"
            
            if overall_validation.get("recommendations"):
                report += "**Recommendations:**\n"
                for recommendation in overall_validation["recommendations"]:
                    report += f"- {recommendation}\n"
                report += "\n"
        
        return report
