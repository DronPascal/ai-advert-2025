"""Command-line interface for Regoose."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from .core.agent import RegooseAgent
from .core.config import get_settings
from .providers.openai_provider import OpenAIProvider

app = typer.Typer(
    name="regoose",
    help="AI-powered test generation agent",
    add_completion=False
)
console = Console()


@app.command()
def generate(
    code: Optional[str] = typer.Option(None, "--code", "-c", help="Code to generate tests for"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="File containing code"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Testing framework"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for report"),
):
    """Generate tests for provided code."""
    asyncio.run(_generate_tests(code, file, language, framework, output))


@app.command()
def interactive():
    """Start interactive mode."""
    asyncio.run(_interactive_mode())


@app.command()
def setup():
    """Setup Regoose configuration."""
    _setup_configuration()


async def _generate_tests(
    code: Optional[str],
    file: Optional[Path],
    language: Optional[str],
    framework: Optional[str],
    output: Optional[Path]
):
    """Generate tests implementation."""
    try:
        # Get settings
        settings = get_settings()
        
        # Initialize agent
        llm_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens
        )
        
        agent = RegooseAgent(llm_provider, settings)
        
        # Get code input
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
        
        # Generate tests
        console.print("[bold blue]Starting test generation...[/bold blue]")
        tests, analysis = await agent.analyze_and_generate_tests(code, language, framework)
        
        if not tests:
            console.print("[red]No tests were generated![/red]")
            return
        
        # Display analysis
        console.print(Panel(analysis, title="Analysis", border_style="green"))
        
        # Run tests with iterative improvement
        max_iterations = 3
        iteration = 1
        
        while iteration <= max_iterations:
            console.print(f"[bold blue]Running generated tests... (Iteration {iteration})[/bold blue]")
            results = await agent.run_tests_in_container(tests)
            
            # Check if all tests passed
            total_tests = sum(r.passed + r.failed + r.errors for r in results)
            total_passed = sum(r.passed for r in results)
            total_failed = sum(r.failed for r in results)
            
            if total_passed == total_tests and total_tests > 0:
                console.print(f"[green]✅ All {total_tests} tests passed![/green]")
                break
            elif total_tests > 0 and iteration < max_iterations:
                console.print(f"[yellow]⚠️  {total_passed}/{total_tests} tests passed, {total_failed} failed[/yellow]")
                
                # Analyze failures and regenerate tests
                console.print("[bold yellow]🔄 Analyzing test failures and regenerating...[/bold yellow]")
                
                # Extract failure information
                failure_info = []
                for result in results:
                    if result.failed > 0 and result.details:
                        for detail in result.details:
                            if isinstance(detail, dict) and 'raw_output' in detail:
                                failure_info.append(detail['raw_output'])
                
                # Regenerate tests with failure context
                improved_tests, new_analysis = await agent.improve_tests_from_failures(
                    code, tests, failure_info, language, framework
                )
                
                if improved_tests:
                    tests = improved_tests
                    console.print(Panel(new_analysis, title="Improved Analysis", border_style="yellow"))
                    iteration += 1
                else:
                    console.print("[red]❌ Could not improve tests automatically[/red]")
                    break
            else:
                if total_tests > 0:
                    console.print(f"[red]❌ {total_passed}/{total_tests} tests passed after {max_iterations} iterations[/red]")
                else:
                    console.print("[red]❌ No tests executed[/red]")
                break
        
        # Generate final report
        report = await agent.generate_report(tests, results)
        
        # Save report
        if output:
            output.write_text(report)
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            # Display report
            console.print("[bold]Generated Report:[/bold]")
            # Pretty print the report in a panel
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


async def _interactive_mode():
    """Interactive mode implementation."""
    console.print(Panel(
        "[bold blue]Regoose Interactive Mode[/bold blue]\n"
        "Enter code, get tests, and see results in real-time!",
        border_style="cyan"
    ))
    
    try:
        settings = get_settings()
        llm_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens
        )
        agent = RegooseAgent(llm_provider, settings)
        
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
            
            # Generate and run tests
            try:
                tests, analysis = await agent.analyze_and_generate_tests(code)
                console.print(Panel(analysis, title="Analysis", border_style="green"))
                
                if Confirm.ask("Run the generated tests?", default=True):
                    # Run tests with iterative improvement (same as CLI)
                    max_iterations = 3
                    iteration = 1
                    
                    while iteration <= max_iterations:
                        console.print(f"[bold blue]Running tests... (Iteration {iteration})[/bold blue]")
                        results = await agent.run_tests_in_container(tests)
                        
                        total_tests = sum(r.passed + r.failed + r.errors for r in results)
                        total_passed = sum(r.passed for r in results)
                        total_failed = sum(r.failed for r in results)
                        
                        if total_passed == total_tests and total_tests > 0:
                            console.print(f"[green]✅ All {total_tests} tests passed![/green]")
                            break
                        elif total_tests > 0 and iteration < max_iterations:
                            console.print(f"[yellow]⚠️  {total_passed}/{total_tests} tests passed, {total_failed} failed[/yellow]")
                            
                            if Confirm.ask("Try to improve tests automatically?", default=True):
                                console.print("[bold yellow]🔄 Analyzing failures and regenerating...[/bold yellow]")
                                
                                # Extract failure information
                                failure_info = []
                                for result in results:
                                    if result.failed > 0 and result.details:
                                        for detail in result.details:
                                            if isinstance(detail, dict) and 'raw_output' in detail:
                                                failure_info.append(detail['raw_output'])
                                
                                # Regenerate tests with failure context
                                improved_tests, new_analysis = await agent.improve_tests_from_failures(
                                    code, tests, failure_info
                                )
                                
                                if improved_tests:
                                    tests = improved_tests
                                    console.print(Panel(new_analysis, title="Improved Analysis", border_style="yellow"))
                                    iteration += 1
                                else:
                                    console.print("[red]❌ Could not improve tests automatically[/red]")
                                    break
                            else:
                                break
                        else:
                            if total_tests > 0:
                                console.print(f"[red]❌ {total_passed}/{total_tests} tests passed after {max_iterations} iterations[/red]")
                            else:
                                console.print("[red]❌ No tests executed[/red]")
                            break
                    
                    # Generate final report
                    report = await agent.generate_report(tests, results)
                    console.print(f"[bold]Results: {total_passed}/{total_tests} tests passed[/bold]")
                    
                    if Confirm.ask("View full report?", default=False):
                        console.print(Panel(
                            Markdown(report),
                            title="📊 Detailed Test Report", 
                            border_style="cyan",
                            expand=False,
                            padding=(1, 2)
                        ))
                    
                    if Confirm.ask("Save report to file?", default=False):
                        filename = Prompt.ask("Enter filename", default="regoose_report.md")
                        Path(filename).write_text(report)
                        console.print(f"[green]Report saved to {filename}[/green]")
            
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
    
    # OpenAI API Key
    api_key = Prompt.ask("Enter your OpenAI API key", password=True)
    if api_key:
        env_content.append(f"OPENAI_API_KEY={api_key}")
    
    # Model selection
    model = Prompt.ask(
        "Choose OpenAI model", 
        choices=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        default="gpt-4o-mini"
    )
    env_content.append(f"OPENAI_MODEL={model}")
    
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


if __name__ == "__main__":
    app()
