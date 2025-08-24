"""Generate report action."""

from typing import Dict, List
from ..core.session import TestResult
from .base import BaseAction, ActionContext, ActionResult


class GenerateReportAction(BaseAction):
    """Action to generate comprehensive test report."""
    
    def get_dependencies(self) -> List[str]:
        """This action depends on having test results."""
        return []  # Dependencies handled by scenario, not individual actions
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["tests", "test_results"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required data."""
        return (
            context.get("tests") is not None and
            context.get("test_results") is not None
        )
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute report generation."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required data for report generation")
            
            tests = context.get("tests")
            test_results = context.get("test_results")
            analysis = context.get("analysis", "No analysis available")
            
            # Generate comprehensive report
            report = self._generate_report(tests, test_results, analysis, context)
            
            return ActionResult.success_result(
                data={"report": report},
                artifacts={"regoose_report.md": report}
            )
            
        except Exception as e:
            return ActionResult.error_result(f"Report generation failed: {str(e)}")
    
    def _generate_report(
        self, 
        tests: Dict[str, str], 
        results: List[TestResult], 
        analysis: str,
        context: ActionContext
    ) -> str:
        """Generate comprehensive Markdown report."""
        
        report_parts = []
        
        # Header
        report_parts.append("# Regoose Test Generation Report")
        report_parts.append(f"Generated at: {context.get('timestamp', 'Unknown')}")
        report_parts.append("")
        
        # Summary
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_errors = sum(r.errors for r in results)
        total_duration = sum(r.duration for r in results)
        
        report_parts.append("## Summary")
        report_parts.append(f"- **Total Tests**: {total_passed + total_failed + total_errors}")
        report_parts.append(f"- **Passed**: {total_passed} ✅")
        report_parts.append(f"- **Failed**: {total_failed} ❌")
        report_parts.append(f"- **Errors**: {total_errors} ⚠️")
        report_parts.append(f"- **Duration**: {total_duration:.2f}s")
        report_parts.append("")
        
        # Analysis
        if analysis and analysis != "No analysis available":
            report_parts.append("## Analysis")
            report_parts.append(analysis)
            report_parts.append("")
        
        # Test Files
        report_parts.append("## Generated Test Files")
        for filename, content in tests.items():
            report_parts.append(f"### {filename}")
            report_parts.append("```python")
            # Properly format the content with unescaped newlines
            formatted_content = content.replace('\\n', '\n').replace('\\t', '\t')
            report_parts.append(formatted_content)
            report_parts.append("```")
            report_parts.append("")
        
        # Detailed Results
        report_parts.append("## Test Results")
        for result in results:
            status_emoji = "✅" if result.failed == 0 and result.errors == 0 else "❌"
            report_parts.append(f"### {result.test_file} {status_emoji}")
            report_parts.append(f"- Passed: {result.passed}")
            report_parts.append(f"- Failed: {result.failed}")
            report_parts.append(f"- Errors: {result.errors}")
            report_parts.append(f"- Duration: {result.duration:.2f}s")
            
            if result.details:
                report_parts.append("#### Details:")
                for detail in result.details:
                    # Format details properly too
                    formatted_detail = str(detail).replace('\\n', '\n').replace('\\t', '\t')
                    report_parts.append(f"- {formatted_detail}")
            
            report_parts.append("")
        
        # Model info
        report_parts.append("## Generation Details")
        report_parts.append(f"- Model: {self.llm.get_model_name()}")
        report_parts.append(f"- Language: {context.get('language', 'Auto-detected')}")
        report_parts.append(f"- Framework: {context.get('framework', 'Auto-selected')}")
        
        return "\n".join(report_parts)
