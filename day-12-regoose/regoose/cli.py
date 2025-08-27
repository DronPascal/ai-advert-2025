"""New CLI interface using Action/Scenario architecture."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from .core.config import get_settings
from .core.logging import setup_logging, LogLevel, get_logger, CorrelationContext, operation_context, token_tracker
from .core.health import run_health_checks, run_single_health_check
from .providers.factory import LLMProviderFactory
from .tools.filesystem_tool import FilesystemTool
from .tools.shell_tool import ShellTool
from .tools.container_tool import ContainerTool
from .tools.github_tool import GitHubTool
from .core.orchestrator import ActionOrchestrator
from .scenarios.test_generation import TestGenerationScenario
from .scenarios.github_pr_review import GitHubPRReviewScenario
from .scenarios.mcp_pr_review import MCPGitHubPRReviewScenario
from .scenarios.code_improvement import CodeImprovementScenario
from .providers.mcp_github_provider import MCPGitHubProvider
from .tools.secure_filesystem_tool import SecureFilesystemTool

app = typer.Typer(
    name="regoose",
    help="AI-powered test generation agent with Action/Scenario architecture",
    add_completion=False
)
console = Console()

# Initialize logging on import
settings = get_settings()
log_level = LogLevel.DEBUG if settings.debug else LogLevel.INFO
setup_logging(log_level)
cli_logger = get_logger("cli")


def extract_llm_params(params: dict) -> dict:
    """Extract LLM parameters from CLI params."""
    llm_params = {
        "temperature": params.get("temperature"),
        "max_tokens": params.get("max_tokens"),
        "top_p": params.get("top_p"),
        "presence_penalty": params.get("presence_penalty"),
        "frequency_penalty": params.get("frequency_penalty")
    }
    # Filter out None values
    return {k: v for k, v in llm_params.items() if v is not None}


def create_tools(settings, working_dir: str = ".", include_github: bool = False, secure_filesystem: bool = False):
    """Create tools for orchestrator."""
    tools = {
        "filesystem": FilesystemTool(working_dir),
        "shell": ShellTool(working_dir),
        "container": ContainerTool(
            runtime=settings.container_runtime,
            base_image=settings.container_image
        ),
        "working_dir": working_dir
    }
    
    # Add secure filesystem tool if requested
    if secure_filesystem:
        tools["secure_filesystem"] = SecureFilesystemTool(working_dir)
    
    # Add GitHub tool if requested and configured
    if include_github and settings.github_token:
        tools["github"] = GitHubTool(
            token=settings.github_token,
            repo_owner=settings.github_repo_owner or "DronPascal",
            repo_name=settings.github_repo_name or "ai-advert-2025"
        )
    
    return tools


@app.command()
def generate(
    code: Optional[str] = typer.Option(None, "--code", "-c", help="Code to generate tests for"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="File containing code"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Testing framework"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for report"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (openai, deepseek, local, auto)"),
    max_iterations: int = typer.Option(3, "--max-iterations", help="Maximum improvement iterations"),
    # LLM Parameters
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens in response"),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Nucleus sampling parameter (0.0-1.0)"),
    presence_penalty: Optional[float] = typer.Option(None, "--presence-penalty", help="Presence penalty (-2.0 to 2.0)"),
    frequency_penalty: Optional[float] = typer.Option(None, "--frequency-penalty", help="Frequency penalty (-2.0 to 2.0)"),
):
    """Generate tests using test generation scenario."""
    with operation_context("generate_tests", "cli") as correlation_id:
        cli_logger.info("Starting test generation command",
                       metadata={"provider": provider, "language": language})
        asyncio.run(_run_test_generation_scenario({
        "code": code,
        "file": file,
        "language": language,
        "framework": framework,
        "output": output,
        "provider": provider,
        "max_iterations": max_iterations,
        # LLM Parameters
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty
    }))


@app.command()
def review_pr(
    pr_number: int = typer.Argument(..., help="Pull Request number to review"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (openai, deepseek, local, auto)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Analyze only, don't publish review"),
    repo_owner: Optional[str] = typer.Option(None, "--repo-owner", help="Repository owner (overrides config)"),
    repo_name: Optional[str] = typer.Option(None, "--repo-name", help="Repository name (overrides config)"),
    # LLM Parameters
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens in response"),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Nucleus sampling parameter (0.0-1.0)"),
    presence_penalty: Optional[float] = typer.Option(None, "--presence-penalty", help="Presence penalty (-2.0 to 2.0)"),
    frequency_penalty: Optional[float] = typer.Option(None, "--frequency-penalty", help="Frequency penalty (-2.0 to 2.0)"),
):
    """Review a GitHub Pull Request using AI analysis."""
    asyncio.run(_run_pr_review_scenario({
        "pr_number": pr_number,
        "provider": provider,
        "dry_run": dry_run,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        # LLM Parameters
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty
    }))


@app.command()
def review_pr_mcp(
    pr_number: int = typer.Argument(..., help="Pull Request number to review"),
    provider: Optional[str] = typer.Option("openai", "--provider", "-p", help="Base LLM provider (openai, deepseek)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Analysis only, do not publish review"),
    debug: bool = typer.Option(False, "--debug", help="Enable verbose debug output"),
    repo_owner: Optional[str] = typer.Option(None, "--repo-owner", help="Repository owner (overrides config)"),
    repo_name: Optional[str] = typer.Option(None, "--repo-name", help="Repository name (overrides config)"),
    # LLM Parameters
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens in response"),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Nucleus sampling parameter (0.0-1.0)"),
    presence_penalty: Optional[float] = typer.Option(None, "--presence-penalty", help="Presence penalty (-2.0 to 2.0)"),
    frequency_penalty: Optional[float] = typer.Option(None, "--frequency-penalty", help="Frequency penalty (-2.0 to 2.0)"),
):
    """Review a GitHub Pull Request using MCP GitHub tools integration."""
    asyncio.run(_run_mcp_pr_review_scenario({
        "pr_number": pr_number,
        "provider": provider,
        "dry_run": dry_run,
        "debug": debug,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        # LLM Parameters
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty
    }))


@app.command()
def improve(
    goal: str = typer.Option(..., "--goal", "-g", help="Goal or specification for code improvement"),
    directory: Optional[str] = typer.Option(".", "--directory", "-d", help="Target directory to improve"),
    max_iterations: int = typer.Option(1, "--max-iterations", "-i", help="Maximum improvement iterations"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Analyze only, don't make changes"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Max tokens"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode with verbose output")
):
    """Improve code autonomously based on specified goal."""
    asyncio.run(_run_code_improvement_scenario({
        "goal": goal,
        "directory": directory,
        "max_iterations": max_iterations,
        "dry_run": dry_run,
        "provider": provider,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "debug": debug
    }))


@app.command()
def health(
    check: Optional[str] = typer.Option(None, "--check", "-c", help="Run specific health check")
):
    """Check system health and component status."""
    asyncio.run(_run_health_check(check))


@app.command()
def interactive():
    """Start interactive mode."""
    asyncio.run(_interactive_mode())


@app.command()
def setup():
    """Setup Regoose configuration."""
    _setup_configuration()


async def _run_test_generation_scenario(params: dict):
    """Run the test generation scenario."""
    try:
        # Get settings
        settings = get_settings()
        
        # Determine provider
        provider = params.get("provider")
        if not provider:
            # Auto-select provider based on available API keys
            available_providers = LLMProviderFactory.get_available_providers(settings)
            if not available_providers:
                console.print("[red]Error: No LLM providers configured. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY[/red]")
                return
            provider = available_providers[0]  # Use first available provider
        
        # Initialize LLM provider
        try:
            llm_provider = LLMProviderFactory.create_provider(provider, settings)
            console.print(f"[green]Using {provider} provider with model {llm_provider.get_model_name()}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating {provider} provider: {str(e)}[/red]")
            return
        
        # Get code input
        code = params.get("code")
        file = params.get("file")
        
        if file:
            if not file.exists():
                console.print(f"[red]Error: File {file} not found[/red]")
                return
            code = file.read_text()
            console.print(f"[green]Loaded code from {file}[/green]")
        elif not code:
            console.print("[red]Error: Please provide code via --code or --file[/red]")
            return
        
        # Display code preview
        console.print(Panel(
            f"[dim]{code[:200]}{'...' if len(code) > 200 else ''}[/dim]",
            title="Code to Test",
            border_style="blue"
        ))
        
        # Create tools and orchestrator
        tools = create_tools(settings, str(Path.cwd()))
        orchestrator = ActionOrchestrator(llm_provider, tools)
        
        # Create and execute scenario
        scenario = TestGenerationScenario(orchestrator)
        
        # Prepare input data
        input_data = {
            "code": code,
            "language": params.get("language"),
            "framework": params.get("framework"),
            "timestamp": datetime.now().isoformat()
        }
        
        console.print("[bold blue]Starting test generation scenario...[/bold blue]")
        
        # Execute scenario with improvements
        max_iterations = params.get("max_iterations", 3)
        result = await scenario.execute_with_improvements(input_data, max_iterations)
        
        if not result.success:
            console.print(f"[red]Scenario failed: {result.error}[/red]")
            return
        
        # Display results
        context = result.context
        test_results = context.get("test_results", [])
        
        # Calculate and display summary
        total_tests = sum(r.passed + r.failed + r.errors for r in test_results)
        total_passed = sum(r.passed for r in test_results)
        total_failed = sum(r.failed for r in test_results)
        
        if total_passed == total_tests and total_tests > 0:
            console.print(f"[green]✅ All {total_tests} tests passed![/green]")
        elif total_tests > 0:
            console.print(f"[yellow]⚠️ {total_passed}/{total_tests} tests passed, {total_failed} failed after {max_iterations} iterations[/yellow]")
        else:
            console.print("[red]❌ No tests executed[/red]")
        
        # Show report
        report = context.get("report")
        output = params.get("output")
        
        if output and report:
            output.write_text(report)
            console.print(f"[green]Report saved to {output}[/green]")
        elif report:
            # Display report
            console.print("[bold]Generated Report:[/bold]")
            console.print(Panel(
                Markdown(report),
                title="📊 Test Report", 
                border_style="cyan",
                expand=False,
                padding=(1, 2)
            ))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if settings.debug:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")


async def _run_pr_review_scenario(params: dict):
    """Run the GitHub PR review scenario."""
    try:
        # Get settings
        settings = get_settings()
        
        # Check GitHub configuration
        if not settings.github_token:
            console.print("[red]Error: GITHUB_TOKEN not configured. Please add it to .env file[/red]")
            return
        
        # Override repo settings if provided
        repo_owner = params.get("repo_owner") or settings.github_repo_owner
        repo_name = params.get("repo_name") or settings.github_repo_name
        
        if not repo_owner or not repo_name:
            console.print("[red]Error: Repository owner and name must be configured[/red]")
            console.print("Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME in .env or use --repo-owner --repo-name")
            return
        
        # Determine provider
        provider = params.get("provider")
        if not provider:
            # Auto-select provider based on available API keys
            available_providers = LLMProviderFactory.get_available_providers(settings)
            if not available_providers:
                console.print("[red]Error: No LLM providers configured. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY[/red]")
                return
            provider = available_providers[0]  # Use first available provider
        
        # Initialize LLM provider
        try:
            llm_provider = LLMProviderFactory.create_provider(provider, settings)
            console.print(f"[green]Using {provider} provider with model {llm_provider.get_model_name()}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating {provider} provider: {str(e)}[/red]")
            return
        
        # Create tools with GitHub integration
        tools = create_tools(settings, str(Path.cwd()), include_github=True)
        
        # Override GitHub tool settings if repo parameters provided
        if params.get("repo_owner") or params.get("repo_name"):
            tools["github"] = GitHubTool(
                token=settings.github_token,
                repo_owner=repo_owner,
                repo_name=repo_name
            )
        
        # Create orchestrator
        orchestrator = ActionOrchestrator(llm_provider, tools)
        
        # Create and execute scenario
        scenario = GitHubPRReviewScenario(orchestrator)
        
        # Prepare input data
        pr_number = params.get("pr_number")
        input_data = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat()
        }
        
        console.print(f"[bold blue]Starting PR #{pr_number} review scenario...[/bold blue]")
        
        # Execute scenario (dry run or full review)
        if params.get("dry_run"):
            console.print("[yellow]Running in dry-run mode (analysis only, no publishing)[/yellow]")
            result = await scenario.execute_dry_run(input_data)
        else:
            result = await scenario.execute(input_data)
        
        if not result.success:
            console.print(f"[red]Scenario failed: {result.error}[/red]")
            return
        
        # Display results
        context = result.context
        pr_info = context.get("pr_info", {})
        review_comments = context.get("review_comments", [])
        overall_feedback = context.get("overall_feedback", "No feedback available")
        score = context.get("score", 0)
        
        # Show summary
        console.print(f"\n[bold]📊 Review Summary for PR #{pr_number}[/bold]")
        console.print(f"**Title:** {pr_info.get('title', 'N/A')}")
        console.print(f"**Author:** {pr_info.get('user', 'N/A')}")
        console.print(f"**Score:** {score}/10")
        console.print(f"**Issues Found:** {len(review_comments)}")
        
        # Show feedback
        console.print(f"\n[bold]💭 Overall Feedback:[/bold]")
        console.print(Panel(
            overall_feedback,
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Show line-specific comments
        if review_comments:
            console.print(f"\n[bold]📝 Detailed Comments ({len(review_comments)}):[/bold]")
            for i, comment in enumerate(review_comments[:5], 1):  # Show first 5
                severity_color = {"error": "red", "warning": "yellow", "suggestion": "blue"}.get(
                    comment.get("severity", "suggestion"), "white"
                )
                console.print(f"\n[{severity_color}]{i}. {comment.get('filename')}:{comment.get('line_number')}[/{severity_color}]")
                console.print(f"   {comment.get('message', 'No message')}")
                if comment.get("suggestion"):
                    console.print(f"   💡 {comment['suggestion']}")
            
            if len(review_comments) > 5:
                console.print(f"\n[dim]... and {len(review_comments) - 5} more comments[/dim]")
        
        # Show publishing status
        if not params.get("dry_run"):
            review_id = context.get("review_id")
            if review_id:
                console.print(f"\n[green]✅ Review published to GitHub (ID: {review_id})[/green]")
                console.print(f"View at: https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}")
            else:
                console.print("\n[yellow]⚠️ Review analysis completed but publishing failed[/yellow]")
        else:
            console.print(f"\n[blue]ℹ️ Dry run completed. Use 'regoose review-pr {pr_number}' to publish review[/blue]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if settings.debug:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")


async def _run_mcp_pr_review_scenario(params: dict):
    """Run the MCP GitHub PR review scenario."""
    try:
        # Get settings
        settings = get_settings()
        
        # Check GitHub configuration
        if not settings.github_token:
            console.print("[red]Error: GITHUB_TOKEN not configured. Please add it to .env file[/red]")
            return
        
        # Override repo settings if provided
        repo_owner = params.get("repo_owner") or settings.github_repo_owner
        repo_name = params.get("repo_name") or settings.github_repo_name
        
        if not repo_owner or not repo_name:
            console.print("[red]Error: Repository owner and name must be configured[/red]")
            console.print("Set GITHUB_REPO_OWNER and GITHUB_REPO_NAME in .env or use --repo-owner --repo-name")
            return
        
        # Get base provider type and debug mode
        provider = params.get("provider", "openai")
        debug_mode = params.get("debug", False)
        
        # Create MCP GitHub Provider
        try:
            console.print(f"[yellow]Initializing MCP GitHub provider with {provider} base...[/yellow]")
            mcp_provider = MCPGitHubProvider(provider, settings)
            
            # Enable debug mode if requested
            if debug_mode:
                mcp_provider.set_debug_mode(True)
                console.print("[blue]🔍 Debug mode enabled - verbose output activated[/blue]")
            
            # Initialize MCP connection
            if not await mcp_provider.initialize():
                console.print("[red]Failed to initialize MCP GitHub provider[/red]")
                return
            
            console.print(f"[green]MCP GitHub provider ready with model {mcp_provider.get_model_name()}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error creating MCP provider: {str(e)}[/red]")
            return
        
        # Create tools (we still need basic tools for orchestrator)
        tools = create_tools(settings, str(Path.cwd()), include_github=True)
        
        # Override GitHub tool settings if repo parameters provided
        if params.get("repo_owner") or params.get("repo_name"):
            tools["github"] = GitHubTool(
                token=settings.github_token,
                repo_owner=repo_owner,
                repo_name=repo_name
            )
        
        # Create orchestrator with MCP provider
        orchestrator = ActionOrchestrator(mcp_provider, tools)
        
        # Create and execute MCP scenario
        scenario = MCPGitHubPRReviewScenario(orchestrator)
        
        # Prepare input data
        pr_number = params.get("pr_number")
        dry_run = params.get("dry_run", False)
        
        input_data = {
            "pr_number": pr_number,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat()
        }
        
        console.print(f"[bold blue]Starting MCP PR #{pr_number} review scenario...[/bold blue]")
        console.print("[cyan]Using GitHub MCP tools for direct AI interaction[/cyan]")
        if dry_run:
            console.print("[yellow]Running in dry-run mode (analysis only, no publishing)[/yellow]")
        
        # Execute MCP scenario (dry_run handled in scenario)
        if dry_run:
            result = await scenario.execute_dry_run(input_data)
        else:
            result = await scenario.execute(input_data)
        
        if not result.success:
            console.print(f"[red]MCP scenario failed: {result.error}[/red]")
            return
        
        # Display results
        context = result.context
        overall_feedback = context.get("overall_feedback", "No feedback available")
        score = context.get("score", 0)
        review_comments = context.get("review_comments", [])
        review_method = context.get("review_method", "MCP GitHub Tools")
        
        # Show summary
        console.print(f"\n[bold]🤖 MCP Review Summary for PR #{pr_number}[/bold]")
        console.print(f"**Method:** {review_method}")
        console.print(f"**Score:** {score}/10")
        console.print(f"**Issues Found:** {len(review_comments)}")
        
        # Show feedback
        console.print(f"\n[bold]💭 MCP Analysis:[/bold]")
        console.print(Panel(
            overall_feedback,
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Show line-specific comments
        if review_comments:
            console.print(f"\n[bold]📝 MCP Comments ({len(review_comments)}):[/bold]")
            for i, comment in enumerate(review_comments[:5], 1):  # Show first 5
                severity_color = {"error": "red", "warning": "yellow", "suggestion": "blue"}.get(
                    comment.get("severity", "suggestion"), "white"
                )
                console.print(f"\n[{severity_color}]{i}. {comment.get('filename')}:{comment.get('line_number')}[/{severity_color}]")
                console.print(f"   {comment.get('message', 'No message')}")
                if comment.get("suggestion"):
                    console.print(f"   💡 {comment['suggestion']}")
            
            if len(review_comments) > 5:
                console.print(f"\n[dim]... and {len(review_comments) - 5} more comments[/dim]")
        
        if dry_run:
            console.print(f"\n[green]✅ MCP PR analysis completed successfully![/green]")
            console.print("[yellow]ℹ️ Dry run completed. Use 'regoose review-pr-mcp {pr_number}' to publish review[/yellow]")
        else:
            console.print(f"\n[green]✅ MCP GitHub PR review completed and published![/green]")
        
        console.print(f"[blue]🔗 View PR: https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}[/blue]")
        
        # Cleanup MCP provider
        mcp_provider.cleanup()
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if settings.debug:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")


async def _interactive_mode():
    """Interactive mode implementation."""
    console.print(Panel(
        "[bold blue]Regoose Interactive Mode[/bold blue]\n"
        "Enter code, get tests, and see results in real-time!",
        border_style="cyan"
    ))
    
    try:
        settings = get_settings()
        
        # Auto-select provider
        available_providers = LLMProviderFactory.get_available_providers(settings)
        if not available_providers:
            console.print("[red]Error: No LLM providers configured. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY[/red]")
            return
        
        provider = available_providers[0]  # Use first available provider
        llm_provider = LLMProviderFactory.create_provider(provider, settings)
        console.print(f"[green]Using {provider} provider with model {llm_provider.get_model_name()}[/green]")
        
        while True:
            console.print("[bold]Options:[/bold]")
            console.print("1. Enter code directly")
            console.print("2. Load from file")
            console.print("3. Exit")
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
            
            if choice == "3":
                console.print("[blue]Goodbye![/blue]")
                break
            
            code = None
            
            if choice == "1":
                console.print("[bold]Enter your code (type 'END' on a new line to finish):[/bold]")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                code = "\n".join(lines)
            
            elif choice == "2":
                file_path = Prompt.ask("Enter file path")
                try:
                    code = Path(file_path).read_text()
                    console.print(f"[green]Loaded {len(code)} characters from {file_path}[/green]")
                except Exception as e:
                    console.print(f"[red]Error loading file: {e}[/red]")
                    continue
            
            if not code or not code.strip():
                console.print("[yellow]No code provided, try again.[/yellow]")
                continue
            
            # Run test generation scenario
            try:
                await _run_test_generation_scenario({
                    "code": code,
                    "provider": provider,
                    "max_iterations": 3
                })
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    except KeyboardInterrupt:
        console.print("[blue]Goodbye![/blue]")
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")


def _setup_configuration():
    """Setup configuration wizard."""
    console.print(Panel(
        "[bold blue]Regoose Configuration Setup[/bold blue]",
        border_style="cyan"
    ))
    
    env_file = Path(".env")
    env_content = []
    
    # Provider selection
    provider_choice = Prompt.ask(
        "Choose LLM provider",
        choices=["openai", "deepseek", "both"],
        default="deepseek"
    )
    
    if provider_choice in ["openai", "both"]:
        # OpenAI API Key
        openai_key = Prompt.ask("Enter your OpenAI API key (optional)", password=True, default="")
        if openai_key:
            env_content.append(f"OPENAI_API_KEY={openai_key}")
        
        # OpenAI Model selection
        openai_model = Prompt.ask(
            "Choose OpenAI model", 
            choices=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            default="gpt-4o-mini"
        )
        env_content.append(f"OPENAI_MODEL={openai_model}")
    
    if provider_choice in ["deepseek", "both"]:
        # DeepSeek API Key
        deepseek_key = Prompt.ask("Enter your DeepSeek API key (optional)", password=True, default="")
        if deepseek_key:
            env_content.append(f"DEEPSEEK_API_KEY={deepseek_key}")
        
        # DeepSeek Model selection
        deepseek_model = Prompt.ask(
            "Choose DeepSeek model",
            choices=["deepseek-chat", "deepseek-coder"],
            default="deepseek-chat"
        )
        env_content.append(f"DEEPSEEK_MODEL={deepseek_model}")
    
    # GitHub integration
    github_setup = Confirm.ask("Configure GitHub integration for PR reviews?", default=False)
    if github_setup:
        github_token = Prompt.ask("Enter your GitHub Personal Access Token (optional)", password=True, default="")
        if github_token:
            env_content.append(f"GITHUB_TOKEN={github_token}")
        
        github_owner = Prompt.ask("Enter GitHub repository owner", default="DronPascal")
        env_content.append(f"GITHUB_REPO_OWNER={github_owner}")
        
        github_name = Prompt.ask("Enter GitHub repository name", default="ai-advert-2025")
        env_content.append(f"GITHUB_REPO_NAME={github_name}")
    
    # Container runtime
    runtime = Prompt.ask(
        "Choose container runtime",
        choices=["podman", "docker"],
        default="podman"
    )
    env_content.append(f"CONTAINER_RUNTIME={runtime}")
    
    # Debug mode
    debug = Confirm.ask("Enable debug mode?", default=False)
    env_content.append(f"DEBUG={str(debug).lower()}")
    
    # Write .env file
    env_file.write_text("\\n".join(env_content))
    console.print(f"[green]Configuration saved to {env_file}[/green]")
    
    # Test configuration
    if Confirm.ask("Test configuration now?", default=True):
        try:
            settings = get_settings()
            console.print("[green]✅ Configuration is valid![/green]")
        except Exception as e:
            console.print(f"[red]❌ Configuration error: {e}[/red]")


async def _run_health_check(check_name: Optional[str] = None):
    """Run health checks and display results."""
    from rich.table import Table
    from rich.text import Text
    
    cli_logger.info("Running health checks", metadata={"specific_check": check_name})
    
    try:
        if check_name:
            results = await run_single_health_check(check_name)
        else:
            results = await run_health_checks()
        
        # Display results in a nice table
        table = Table(title="System Health Check")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Message", style="dim")
        table.add_column("Details", style="dim")
        
        for check_name, result in results.get("checks", {}).items():
            status = result["status"]
            
            # Color status based on result
            if status == "healthy":
                status_text = Text("✅ Healthy", style="green")
            elif status == "warning":
                status_text = Text("⚠️  Warning", style="yellow")
            elif status == "disabled":
                status_text = Text("⭕ Disabled", style="blue")
            elif status == "unhealthy":
                status_text = Text("❌ Unhealthy", style="red")
            else:
                status_text = Text("🔍 Unknown", style="dim")
            
            details = ""
            if "metadata" in result:
                metadata = result["metadata"]
                if isinstance(metadata, dict):
                    details = ", ".join([f"{k}: {v}" for k, v in metadata.items() if v is not None])
            
            table.add_row(
                check_name.replace("_", " ").title(),
                status_text,
                result.get("message", ""),
                details
            )
        
        console.print(table)
        
        # Overall status summary
        overall = results.get("overall_status", "unknown")
        if overall == "healthy":
            console.print("\n[bold green]🎉 All systems are healthy![/bold green]")
        elif overall == "warning":
            console.print("\n[bold yellow]⚠️  Some systems have warnings[/bold yellow]")
        elif overall == "unhealthy":
            console.print("\n[bold red]❌ Some systems are unhealthy[/bold red]")
        else:
            console.print(f"\n[bold dim]🔍 Overall status: {overall}[/bold dim]")
            
    except Exception as e:
        cli_logger.error(f"Health check failed: {str(e)}")
        console.print(f"[red]❌ Health check failed: {e}[/red]")


async def _run_code_improvement_scenario(params: dict):
    """Run the code improvement scenario."""
    try:
        # Extract parameters
        goal = params.get("goal")
        directory = params.get("directory", ".")
        max_iterations = params.get("max_iterations", 1)
        dry_run = params.get("dry_run", False)
        debug = params.get("debug", False)
        
        # Set debug logging if requested
        if debug:
            from .core.logging import setup_logging, LogLevel
            setup_logging(LogLevel.DEBUG)
            cli_logger.info("Debug mode enabled", metadata={"debug": True})
        
        with operation_context("code_improvement_command", "cli") as correlation_id:
            cli_logger.info(f"Starting code improvement", metadata={
                "goal": goal,
                "directory": directory,
                "max_iterations": max_iterations,
                "dry_run": dry_run,
                "correlation_id": correlation_id
            })
            
            # Display header
            console.print(Panel(
                f"[bold cyan]🔧 Regoose Code Improvement[/bold cyan]\n\n"
                f"[bold]Goal:[/bold] {goal}\n"
                f"[bold]Directory:[/bold] {directory}\n"
                f"[bold]Max Iterations:[/bold] {max_iterations}\n"
                f"[bold]Mode:[/bold] {'Analysis Only' if dry_run else 'Implementation'}\n" +
                (f"[bold]Correlation ID:[/bold] {correlation_id}" if debug else ""),
                title="Code Improvement Session",
                border_style="cyan"
            ))
            
            # Validate directory
            from pathlib import Path
            target_path = Path(directory).resolve()
            if not target_path.exists():
                console.print(f"[red]❌ Directory not found: {directory}[/red]")
                return
            if not target_path.is_dir():
                console.print(f"[red]❌ Path is not a directory: {directory}[/red]")
                return
            
            # Get settings and create provider
            settings = get_settings()
            
            # Create LLM provider
            provider_name = params.get("provider") or settings.default_provider
            llm_params = extract_llm_params(params)
            provider = LLMProviderFactory.create_provider(provider_name, settings, **llm_params)
            
            # Create tools with secure filesystem
            tools = create_tools(settings, str(target_path), secure_filesystem=True)
            
            # Create orchestrator
            orchestrator = ActionOrchestrator(provider, tools)
            
            # Create scenario
            scenario = CodeImprovementScenario(orchestrator)
            
            # Reset token tracking at start of operation
            token_tracker.reset()

            # Prepare input data
            input_data = {
                "goal": goal,
                "target_directory": str(target_path),
                "max_iterations": max_iterations,
                "dry_run": dry_run,
                "debug": debug
            }

            # Execute scenario
            console.print("\n[bold yellow]🔍 Starting analysis...[/bold yellow]")
            
            if max_iterations > 1:
                result = await scenario.execute_with_iterations(input_data)
            else:
                result = await scenario.execute(input_data)
            
            # Display results
            if result.success:
                console.print("\n[bold green]✅ Code improvement completed successfully![/bold green]")
                
                # Show artifacts generated
                if result.artifacts:
                    console.print("\n[bold]📋 Generated Reports:[/bold]")
                    for artifact_name, content in result.artifacts.items():
                        console.print(f"  • {artifact_name}")
                        if debug:
                            # In debug mode, show first few lines of each artifact
                            lines = content.split('\n')[:3]
                            preview = '\n'.join(lines)
                            console.print(f"    [dim]{preview}...[/dim]")
                
                # Show summary from context
                summary = result.context.get("summary")
                if summary:
                    console.print(f"\n[bold]📊 Summary:[/bold]\n{summary}")
                
                # Show validation results if available
                validation_results = result.context.get("validation_results", [])
                if validation_results:
                    console.print(f"\n[bold]🔍 Validation:[/bold]")
                    for vr in validation_results:
                        status = "✅" if vr.get("syntax_valid", False) else "❌"
                        console.print(f"  {status} {vr.get('file', 'Unknown file')}")

                # Show token usage summary
                token_summary = token_tracker.format_summary()
                console.print(f"\n{token_summary}")

            else:
                console.print(f"\n[bold red]❌ Code improvement failed: {result.error}[/bold red]")
                # Show token usage summary even on failure
                token_summary = token_tracker.format_summary()
                if token_tracker.total_tokens > 0:
                    console.print(f"\n{token_summary}")
                
            cli_logger.info("Code improvement scenario completed", metadata={
                "success": result.success,
                "correlation_id": correlation_id
            })
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Code improvement interrupted by user[/yellow]")
    except Exception as e:
        cli_logger.error(f"Code improvement scenario failed: {e}", error=str(e))
        console.print(f"[red]❌ Code improvement failed: {e}[/red]")


if __name__ == "__main__":
    app()
