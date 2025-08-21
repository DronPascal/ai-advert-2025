# Regoose - AI Test Generation Agent

Regoose is an AI-powered test generation agent that automatically creates, runs, and validates tests for your code. Inspired by the [Goose](https://github.com/block/goose) architecture, it provides a scalable foundation for building multi-agent systems.

## Features

- 🤖 **AI-Powered Test Generation**: Uses LLMs to analyze code and generate comprehensive tests
- 🐳 **Containerized Execution**: Runs tests in isolated Podman containers for security
- 🔧 **MCP Integration**: Leverages Model Context Protocol for filesystem and shell operations
- 🎯 **Multi-Language Support**: Supports any programming language through LLM analysis
- 📊 **Rich Reports**: Generates detailed Markdown reports with test results
- ⚡ **Extensible Architecture**: Built for scaling into multi-agent systems

## Quick Start

1. **Installation**
   ```bash
   cd day-12-regoose
   pip install -e .
   ```

2. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Basic Usage**
   ```bash
   # Generate and run tests for code input
   regoose generate --code "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
   
   # Run tests from file
   regoose generate --file mycode.py
   
   # Interactive mode
   regoose interactive
   ```

## Architecture

Based on Goose patterns:
- **Providers**: Abstract LLM interactions (OpenAI, local models)
- **Tools**: MCP-powered filesystem and shell operations
- **Sessions**: Stateful conversation tracking
- **Executors**: Containerized test execution

## MCP Integration

- **Filesystem MCP**: File read/write operations
- **Shell MCP**: Command execution and container management
- **Extensible**: Add custom MCP servers for specialized operations

## Development

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black .
isort .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
