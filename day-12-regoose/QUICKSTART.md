# Regoose Quick Start Guide

Get up and running with Regoose in 5 minutes!

## Prerequisites

- Python 3.10+ installed
- Podman or Docker installed
- OpenAI API key (or DeepSeek API key)
- GitHub Personal Access Token (for PR reviews)

## Installation

1. **Clone/Navigate to the project**
   ```bash
   cd day-12-regoose
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Set up configuration**
   ```bash
   regoose setup
   ```
   Configure your LLM provider (OpenAI/DeepSeek) and optionally GitHub integration for PR reviews.

4. **Install MCP servers (for GitHub integration)**
   ```bash
   npm install -g @modelcontextprotocol/server-github
   python scripts/install_mcp.py
   ```

## Quick Test

### Generate Tests
```bash
# Generate tests with OpenAI
regoose generate --code "def add(a, b): return a + b"

# Generate tests with DeepSeek
regoose generate --code "def add(a, b): return a + b" --provider deepseek
```

### GitHub PR Review (Revolutionary!)
```bash
# Traditional PR review
regoose review-pr 123 --dry-run

# Revolutionary MCP-powered PR review with AI autonomy
regoose review-pr-mcp 123 --provider openai --debug
```

## Interactive Mode

For a more interactive experience:

```bash
regoose interactive
```

## Example with File

1. **Create a test file**
   ```python
   # my_code.py
   def fibonacci(n):
       if n <= 1:
           return n
       return fibonacci(n-1) + fibonacci(n-2)
   ```

2. **Generate tests**
   ```bash
   regoose generate --file my_code.py --output report.md
   ```

## Demo

Run the built-in demo:

```bash
   python scripts/demo.py
```

## What happens?

### Test Generation Flow:
1. **Analysis**: AI analyzes your code structure and functionality
2. **Generation**: Creates comprehensive tests with edge cases
3. **Execution**: Runs tests in isolated Podman container
4. **Iteration**: AI learns from failures and improves tests automatically
5. **Report**: Generates detailed Markdown report with results

### GitHub PR Review Flow:
1. **PR Analysis**: AI reads pull request and changed files
2. **Code Review**: Analyzes code quality, patterns, and potential issues
3. **Line-Specific Comments**: Places precise feedback on exact code lines
4. **Intelligent Scoring**: Provides 1-10 rating with severity classification
5. **Publication**: Publishes review directly to GitHub via MCP tools

## Next Steps

- **Explore GitHub Integration**: Set up PR reviews for your repositories
- **Try Multi-Provider Support**: Compare OpenAI vs DeepSeek results
- **Use Debug Mode**: `--debug` flag for detailed MCP operation logs
- **Try Interactive Mode**: Real-time AI conversation for test generation
- **Explore Examples**: Check out `examples/` directory
- **Read Full Documentation**: `README.md` and `ARCHITECTURE.md`

## Troubleshooting

**Container errors?**
- Make sure Podman/Docker is running
- Check container runtime in `.env`: `CONTAINER_RUNTIME=podman`

**API errors?**
- Verify your OpenAI/DeepSeek API key in `.env`
- Check your account has sufficient credits

**GitHub integration errors?**
- Verify `GITHUB_TOKEN` in `.env` (Personal Access Token)
- Ensure token has repo read/write permissions
- Install GitHub MCP server: `npm install -g @modelcontextprotocol/server-github`
- Use `--debug` flag to see detailed MCP operations

**MCP errors?**
- Check if MCP server is installed: `which npx`
- Verify GitHub token permissions (pull requests scope required)
- Try `--dry-run` mode first to test without publishing

**Import errors?**
- Make sure you installed with: `pip install -e .`
- Check Python version: `python --version` (needs 3.10+)

Need help? Check the full documentation or create an issue!
