"""Analyze code action."""

import json
from typing import Dict, List, Any
from .base import BaseAction, ActionContext, ActionResult


class AnalyzeCodeAction(BaseAction):
    """Action to analyze code and prepare for test generation."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["code"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        code = context.get("code")
        return code is not None and len(code.strip()) > 0
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute code analysis."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required field 'code'")
            
            code = context.get("code")
            language = context.get("language")
            framework = context.get("framework")
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(code, language, framework)
            
            # Get LLM analysis
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"Analyze and generate tests for:\n\n```\n{code}\n```"}
            ]
            
            response = await self.llm.generate(messages)
            
            # Parse response
            tests, analysis = self._parse_test_response(response.content)
            
            # Add original code to test files (if not already included)
            for filename, test_content in tests.items():
                if code not in test_content:
                    # Properly format multiline code and escape sequences
                    formatted_code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                    tests[filename] = f"# Original code to test\n{formatted_code}\n\n{test_content}"
            
            return ActionResult.success_result(
                data={
                    "tests": tests,
                    "analysis": analysis,
                    "language": language,
                    "framework": framework
                },
                artifacts=tests
            )
            
        except Exception as e:
            return ActionResult.error_result(f"Analysis failed: {str(e)}")
    
    def _build_analysis_prompt(
        self,
        code: str,
        language: str = None,
        framework: str = None
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
