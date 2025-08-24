"""Generate tests action."""

import json
from typing import Dict, List
from .base import BaseAction, ActionContext, ActionResult


class GenerateTestsAction(BaseAction):
    """Action to improve tests based on failure information."""
    
    def get_dependencies(self) -> List[str]:
        """This action depends on analyze_code for basic generation."""
        return []  # Can work independently for improvements
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["code", "original_tests", "failure_info"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context for test improvement."""
        return (
            context.get("code") is not None and
            context.get("original_tests") is not None and
            context.get("failure_info") is not None
        )
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute test improvement based on failures."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required fields for test improvement")
            
            code = context.get("code")
            original_tests = context.get("original_tests")
            failure_info = context.get("failure_info")
            language = context.get("language")
            framework = context.get("framework")
            
            # Build improvement prompt
            improvement_prompt = self._build_improvement_prompt(
                code, original_tests, failure_info, language, framework
            )
            
            # Get response from LLM
            messages = [{"role": "user", "content": improvement_prompt}]
            response = await self.llm.generate(messages)
            
            # Parse improved tests and analysis
            improved_tests, new_analysis = self._parse_test_response(response.content)
            
            # Add original code to improved test files
            for filename, test_content in improved_tests.items():
                if code not in test_content:
                    formatted_code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                    improved_tests[filename] = f"# Original code to test\n{formatted_code}\n\n{test_content}"
            
            return ActionResult.success_result(
                data={
                    "tests": improved_tests,
                    "analysis": new_analysis,
                    "improved": True
                },
                artifacts=improved_tests
            )
            
        except Exception as e:
            return ActionResult.error_result(f"Test improvement failed: {str(e)}")
    
    def _build_improvement_prompt(
        self,
        code: str,
        original_tests: Dict[str, str],
        failure_info: List[str],
        language: str = None,
        framework: str = None
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
    
    def _parse_test_response(self, response: str) -> tuple[Dict[str, str], str]:
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
