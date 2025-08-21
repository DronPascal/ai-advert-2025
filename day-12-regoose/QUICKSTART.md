# Regoose Quick Start Guide

Get up and running with Regoose in 5 minutes!

## Prerequisites

- Python 3.10+ installed
- Podman or Docker installed
- OpenAI API key

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
   Enter your OpenAI API key when prompted.

4. **Install MCP servers (optional but recommended)**
   ```bash
   python scripts/install_mcp.py
   ```

## Quick Test

Generate tests for a simple function:

```bash
regoose generate --code "def add(a, b): return a + b"
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

1. **Analysis**: AI analyzes your code structure and functionality
2. **Generation**: Creates comprehensive tests with edge cases
3. **Execution**: Runs tests in isolated Podman container
4. **Report**: Generates detailed Markdown report with results

## Next Steps

- Explore different programming languages
- Try the interactive mode
- Check out `examples/` directory
- Read the full documentation in `README.md`

## Troubleshooting

**Container errors?**
- Make sure Podman/Docker is running
- Check container runtime in `.env`: `CONTAINER_RUNTIME=podman`

**API errors?**
- Verify your OpenAI API key in `.env`
- Check your account has sufficient credits

**Import errors?**
- Make sure you installed with: `pip install -e .`
- Check Python version: `python --version` (needs 3.10+)

Need help? Check the full documentation or create an issue!
