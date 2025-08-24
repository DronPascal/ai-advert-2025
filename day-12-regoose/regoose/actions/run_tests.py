"""Run tests action."""

import json
from pathlib import Path
from typing import Dict, List
from ..core.session import TestResult
from .base import BaseAction, ActionContext, ActionResult


class RunTestsAction(BaseAction):
    """Action to run tests in isolated container."""
    
    def get_dependencies(self) -> List[str]:
        """This action depends on having tests to run."""
        return []  # Dependencies handled by scenario
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["tests"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has tests to run."""
        tests = context.get("tests")
        return tests is not None and len(tests) > 0
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute tests in container."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("No tests to run")
            
            tests = context.get("tests")
            
            # Create temporary test directory
            filesystem = self.tools.get("filesystem")
            if not filesystem:
                return ActionResult.error_result("Filesystem tool not available")
            
            await filesystem.execute("create_directory", path="temp_tests")
            
            # Write test files
            for filename, content in tests.items():
                await filesystem.execute(
                    "write_file",
                    path=f"temp_tests/{filename}",
                    content=content
                )
            
            # Create requirements.txt for container
            requirements_content = "pytest>=8.0.0\npytest-json-report>=1.5.0\n"
            await filesystem.execute(
                "write_file",
                path="temp_tests/requirements.txt",
                content=requirements_content
            )
            
            # Run tests in container
            container = self.tools.get("container")
            if not container:
                return ActionResult.error_result("Container tool not available")
            
            container_command = "pip3 install -r requirements.txt && python3 -m pytest -v ."
            
            # Get working directory
            working_dir = self.tools.get("working_dir", Path("."))
            test_dir = Path(working_dir) / "temp_tests"
            
            result = await container.execute(
                "run",
                command=container_command,
                volumes={str(test_dir.absolute()): "/app"},
                working_dir="/app",
                timeout=120
            )
            
            # Parse test results
            test_results = await self._parse_test_results(test_dir, result, filesystem)
            
            # Cleanup temp files
            await self._cleanup_temp_files(test_dir)
            
            return ActionResult.success_result(
                data={
                    "test_results": test_results,
                    "container_output": result.output if hasattr(result, 'output') else str(result)
                }
            )
            
        except Exception as e:
            return ActionResult.error_result(f"Test execution failed: {str(e)}")
    
    async def _parse_test_results(self, test_dir: Path, container_result, filesystem) -> List[TestResult]:
        """Parse test execution results."""
        results = []
        
        try:
            # Try to read pytest json report
            json_report_result = await filesystem.execute(
                "read_file",
                path="temp_tests/results.json"
            )
            
            if json_report_result.success:
                report_data = json.loads(json_report_result.output)
                
                # Extract test summary
                summary = report_data.get("summary", {})
                
                result = TestResult(
                    test_file="all_tests",
                    passed=summary.get("passed", 0),
                    failed=summary.get("failed", 0),
                    errors=summary.get("error", 0),
                    duration=report_data.get("duration", 0.0),
                    details=[]
                )
                
                # Add individual test details
                for test in report_data.get("tests", []):
                    outcome = test.get("outcome", "unknown")
                    result.details.append({
                        "name": test.get("nodeid", "unknown"),
                        "outcome": outcome,
                        "duration": test.get("duration", 0.0)
                    })
                
                results.append(result)
            else:
                # Fallback: parse from container output
                results.append(self._parse_container_output(container_result))
                
        except Exception as e:
            # Create error result
            results.append(TestResult(
                test_file="test_execution",
                passed=0,
                failed=1,
                errors=1,
                duration=0.0,
                details=[{"error": f"Failed to parse results: {str(e)}"}]
            ))
        
        return results
    
    def _parse_container_output(self, container_result) -> TestResult:
        """Parse test results from container output text."""
        output = getattr(container_result, 'output', str(container_result))
        
        # Simple parsing for pytest output
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        errors = output.count(" ERROR")
        
        return TestResult(
            test_file="container_output",
            passed=passed,
            failed=failed,
            errors=errors,
            duration=0.0,
            details=[{"raw_output": output}]
        )
    
    async def _cleanup_temp_files(self, test_dir: Path) -> None:
        """Clean up temporary test files."""
        try:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
        except Exception:
            # Ignore cleanup errors
            pass
