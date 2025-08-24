"""Main Regoose agent implementation."""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .session import Session, TestResult, Message
from .config import Settings
from ..providers.base import LLMProvider
from ..tools.filesystem_tool import FilesystemTool
from ..tools.shell_tool import ShellTool
from ..tools.container_tool import ContainerTool


class RegooseAgent:
    """Main AI test generation agent inspired by Goose architecture."""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        settings: Settings,
        working_directory: Optional[str] = None
    ):
        self.llm = llm_provider
        self.settings = settings
        self.working_dir = Path(working_directory or ".")
        self.console = Console()
        
        # Initialize tools
        self.filesystem = FilesystemTool(str(self.working_dir))
        self.shell = ShellTool(str(self.working_dir))
        self.container = ContainerTool(
            runtime=settings.container_runtime,
            base_image=settings.container_image
        )
        
        # Session management
        self.current_session: Optional[Session] = None
    
    def create_session(self) -> Session:
        """Create a new session."""
        self.current_session = Session()
        return self.current_session
    
    async def analyze_and_generate_tests(
        self,
        code: str,
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> Tuple[Dict[str, str], str]:
        """Analyze code and generate comprehensive tests."""
        
        if not self.current_session:
            self.create_session()
        
        session = self.current_session
        session.original_code = code
        session.language = language
        session.framework = framework
        
        # Add user message
        session.add_message("user", f"Generate tests for this code:\n\n```python\n{code}\n```")
        
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(code, language, framework)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Analyzing code and generating tests...", total=None)
            
            # Get LLM analysis and test generation
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"Analyze and generate tests for:\n\n```\n{code}\n```"}
            ]
            
            response = await self.llm.generate(messages)
            
            progress.update(task, description="Parsing generated tests...")
            
                    # Parse response to extract tests and analysis
        tests, analysis = self._parse_test_response(response.content)
        
        # Add original code to test files (if not already included)
        for filename, test_content in tests.items():
            if code not in test_content:
                # Properly format multiline code and escape sequences
                formatted_code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                tests[filename] = f"# Original code to test\n{formatted_code}\n\n{test_content}"
            
            # Store generated tests in session
            session.generated_tests.update(tests)
            session.add_message("assistant", response.content)
        
        return tests, analysis
    
    async def improve_tests_from_failures(
        self,
        code: str,
        original_tests: Dict[str, str],
        failure_info: List[str],
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> Tuple[Dict[str, str], str]:
        """Improve tests based on failure information."""
        
        # Build improvement prompt
        improvement_prompt = self._build_improvement_prompt(
            code, original_tests, failure_info, language, framework
        )
        
        # Get response from LLM
        if hasattr(self.llm, 'generate_response'):
            response = await self.llm.generate_response(improvement_prompt)
        else:
            # Format as message for OpenAI API
            messages = [{"role": "user", "content": improvement_prompt}]
            response = await self.llm.generate(messages)
        
        # Parse improved tests and analysis
        improved_tests, new_analysis = self._parse_test_response(response.content)
        
        # Add original code to improved test files
        for filename, test_content in improved_tests.items():
            if code not in test_content:
                formatted_code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                improved_tests[filename] = f"# Original code to test\n{formatted_code}\n\n{test_content}"
        
        return improved_tests, new_analysis
    
    async def run_tests_in_container(self, tests: Dict[str, str]) -> List[TestResult]:
        """Run generated tests in isolated container."""
        
        if not tests:
            return []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Setting up test environment...", total=None)
            
            # Create temporary test directory
            test_dir = self.working_dir / "temp_tests"
            await self.filesystem.execute("create_directory", path="temp_tests")
            
            progress.update(task, description="Writing test files...")
            
            # Write test files
            for filename, content in tests.items():
                await self.filesystem.execute(
                    "write_file",
                    path=f"temp_tests/{filename}",
                    content=content
                )
            
            # Create requirements.txt for container
            requirements_content = "pytest>=8.0.0\npytest-json-report>=1.5.0\n"
            await self.filesystem.execute(
                "write_file",
                path="temp_tests/requirements.txt",
                content=requirements_content
            )
            
            progress.update(task, description="Running tests in container...")
            
            # Run tests in container - simplified command
            container_command = "pip3 install -r requirements.txt && python3 -m pytest -v ."
            
            result = await self.container.execute(
                "run",
                command=container_command,
                volumes={str(test_dir.absolute()): "/app"},
                working_dir="/app",
                timeout=120
            )
            
            progress.update(task, description="Collecting results...")
            
            # Parse test results
            test_results = await self._parse_test_results(test_dir, result)
            
            # Store results in session
            if self.current_session:
                for test_result in test_results:
                    self.current_session.add_test_result(test_result)
            
            # Always cleanup temp files to avoid old file conflicts
            await self._cleanup_temp_files(test_dir)
        
        return test_results
    
    async def generate_report(self, tests: Dict[str, str], results: List[TestResult]) -> str:
        """Generate comprehensive Markdown report."""
        
        report_parts = []
        
        # Header
        report_parts.append("# Regoose Test Generation Report")
        report_parts.append(f"Generated at: {self.current_session.created_at if self.current_session else 'Unknown'}")
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
        if self.current_session and self.current_session.messages:
            report_parts.append("## Generation Details")
            report_parts.append(f"- Model: {self.llm.get_model_name()}")
            report_parts.append(f"- Language: {self.current_session.language or 'Auto-detected'}")
            report_parts.append(f"- Framework: {self.current_session.framework or 'Auto-selected'}")
        
        return "\n".join(report_parts)
    
    def _build_improvement_prompt(
        self,
        code: str,
        original_tests: Dict[str, str],
        failure_info: List[str],
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> str:
        """Build prompt for improving tests based on failures."""
        
        failures_text = "\n\n".join([f"**Failure {i+1}:**\n{failure}" for i, failure in enumerate(failure_info)])
        
        original_tests_text = "\n\n".join([f"**{filename}:**\n```\n{content}\n```" for filename, content in original_tests.items()])
        
        return f"""You are Regoose, an expert AI test generation agent. Your task is to improve existing tests that have failed.

**Original Code:**
```{language or 'python'}
{code}
```

**Current Tests:**
{original_tests_text}

**Test Failures:**
{failures_text}

**Your task:**
1. Analyze why the tests failed
2. Understand the actual behavior of the code vs expected behavior in tests
3. Generate improved tests that match the real behavior of the code
4. Fix incorrect assumptions about how the code should behave

**Key principles:**
- Tests should validate actual code behavior, not impose requirements
- If code concatenates strings, tests should expect string concatenation
- If code adds lists, tests should expect list concatenation  
- Only expect TypeError if the code actually raises it
- Be realistic about Python's built-in behaviors

**Output Format:**
Respond with a JSON object:
```json
{{
    "analysis": "Analysis of failures and improvements made",
    "language": "{language or 'python'}",
    "framework": "{framework or 'unittest'}",
    "tests": {{
        "test_filename.py": "improved test file content"
    }}
}}
```

Generate realistic, working tests that match the actual behavior of the provided code."""
    
    def _build_analysis_prompt(
        self,
        code: str,
        language: Optional[str] = None,
        framework: Optional[str] = None
    ) -> str:
        """Build system prompt for code analysis and test generation."""
        
        return f"""You are Regoose, an expert AI test generation agent. Your task is to analyze code and generate comprehensive, high-quality tests.

**Your capabilities:**
- Analyze code in any programming language
- Generate appropriate test frameworks and patterns
- Create edge case tests and error handling tests
- Follow testing best practices and conventions

**Instructions:**
1. Analyze the provided code thoroughly
2. Determine the appropriate testing framework if not specified
3. Generate comprehensive tests covering:
   - Happy path scenarios
   - Edge cases and boundary conditions
   - Error handling and exceptions
   - Performance considerations (when relevant)

**Output Format:**
Respond with a JSON object containing:
```json
{{
    "analysis": "Brief analysis of the code and testing approach",
    "language": "detected or specified language",
    "framework": "chosen testing framework",
    "tests": {{
        "test_filename.py": "complete test file content",
        "test_filename2.py": "additional test file if needed"
    }}
}}
```

**Testing Guidelines:**
- Write clear, descriptive test names
- Include docstrings for complex tests
- Use appropriate assertions and test patterns
- Mock external dependencies when necessary
- Follow language-specific testing conventions

Language: {language or "Auto-detect"}
Framework: {framework or "Auto-select appropriate framework"}

Generate high-quality, production-ready tests that provide excellent coverage and follow best practices."""
    
    def _parse_test_response(self, response: str) -> Tuple[Dict[str, str], str]:
        """Parse LLM response to extract tests and analysis."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = response[json_start:json_end]
                data = json.loads(json_content)
                
                tests = data.get("tests", {})
                analysis = data.get("analysis", "No analysis provided")
                
                return tests, analysis
            else:
                # Fallback: treat entire response as a single test file
                return {"test_generated.py": response}, "Generated from non-JSON response"
                
        except (json.JSONDecodeError, KeyError):
            # Fallback: treat response as single test file
            return {"test_generated.py": response}, "Generated from malformed JSON response"
    
    async def _parse_test_results(self, test_dir: Path, container_result) -> List[TestResult]:
        """Parse test execution results."""
        results = []
        
        try:
            # Try to read pytest json report
            json_report_result = await self.filesystem.execute(
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
        output = container_result.output
        
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
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not cleanup temp files: {e}[/yellow]")
