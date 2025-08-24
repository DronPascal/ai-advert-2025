# Regoose - AI Test Generation Agent

Regoose is an AI-powered test generation agent that automatically creates, runs, and validates tests for your code. Inspired by the [Goose](https://github.com/block/goose) architecture, it provides a scalable foundation for building multi-agent systems.

## Features

- 🤖 **AI-Powered Test Generation**: Uses LLMs to analyze code and generate comprehensive tests
- 🔍 **AI GitHub PR Reviews**: Automated code review with line-specific comments and intelligent scoring
- 🔧 **Native MCP GitHub Integration**: Direct AI access to 26 GitHub tools via Model Context Protocol
- 🎭 **Dual Review Modes**: Traditional API-based and revolutionary MCP-powered reviews
- 🐳 **Containerized Execution**: Runs tests in isolated Podman containers for security
- 🚀 **Multi-Provider Support**: OpenAI, DeepSeek, and local LLM providers with auto-selection
- 🎯 **Multi-Language Support**: Supports any programming language through LLM analysis
- 📊 **Rich Reports**: Generates detailed Markdown reports with test results
- ⚡ **Action/Scenario Architecture**: Scalable composition of AI operations
- 🔄 **Iterative Test Improvement**: AI learns from failures and automatically improves tests

## Quick Start

1. **Installation**
   ```bash
   cd day-12-regoose
   pip install -e .
   ```

2. **Configuration**
   ```bash
   regoose setup
   # Configure LLM providers (OpenAI/DeepSeek) and GitHub integration
   ```

3. **Basic Usage**
   ```bash
   # Generate and run tests with provider selection
   regoose generate --code "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)" --provider openai
   regoose generate --file mycode.py --provider deepseek
   
   # GitHub PR Reviews (Revolutionary!)
   regoose review-pr 123 --dry-run                    # Traditional mode
   regoose review-pr-mcp 123 --provider openai        # MCP mode with AI autonomy
   
   # Interactive mode
   regoose interactive
   ```

## Architecture

Revolutionary Action/Scenario architecture:
- **Actions**: Atomic operations (AnalyzeCode, GenerateTests, MCPPRReview)
- **Scenarios**: Composed workflows (TestGeneration, GitHubPRReview)  
- **Orchestrator**: Smart dependency management and coordination
- **Providers**: Multi-LLM support (OpenAI, DeepSeek, Local, MCP)
- **MCP Integration**: Native GitHub tools and filesystem operations
- **Containers**: Isolated test execution environment

## MCP Integration

### Core MCP Tools:
- **Filesystem MCP**: File read/write operations
- **Shell MCP**: Command execution and container management
- **Container MCP**: Podman/Docker orchestration

### Revolutionary GitHub MCP:
- **26 Native GitHub Tools**: Direct AI access to GitHub operations
- **Autonomous AI Operations**: LLM calls tools without intermediate code
- **Line-Specific Comments**: Precise feedback placement on code lines
- **Real-time PR Analysis**: Dynamic pull request reading and processing
- **Intelligent Publishing**: Smart review creation with severity classification

### MCP Server Setup:
```bash
# Install GitHub MCP server
npm install -g @modelcontextprotocol/server-github

# Configure in .env
GITHUB_TOKEN=your_personal_access_token
```

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
