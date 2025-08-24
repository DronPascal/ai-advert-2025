# Regoose Architecture

Regoose is built with a revolutionary Action/Scenario architecture that enables scalable AI operations, inspired by [Goose](https://github.com/block/goose) and [LangGraph](https://github.com/langchain-ai/langgraph) patterns with native MCP GitHub integration.

## Core Components

### 1. CLI Interface (`regoose/cli.py`)
- **Command-line interface** for user interaction
- **Multiple Commands**: `generate`, `review-pr`, `review-pr-mcp`, `interactive`, `setup`
- **Provider Selection**: `--provider openai|deepseek|auto` for LLM choice
- **GitHub Integration**: Native PR review commands with dry-run and debug modes
- **Setup wizard** for multi-provider and GitHub configuration  
- Built with Typer and Rich for excellent UX

### 2. Action/Scenario Architecture (`regoose/actions/`, `regoose/scenarios/`)
- **Actions**: Atomic, reusable operations (AnalyzeCode, GenerateTests, RunTests, MCPPRReview)
- **Scenarios**: Composed workflows (TestGenerationScenario, GitHubPRReviewScenario, MCPGitHubPRReviewScenario)
- **Orchestrator**: Smart dependency management and action coordination
- **Session**: Stateful conversation and execution tracking  
- **Configuration**: Multi-provider and GitHub settings management

### 3. LLM Providers (`regoose/providers/`)
- **Abstract Provider Interface**: Pluggable LLM support
- **OpenAI Provider**: Production-ready OpenAI integration (GPT-4o-mini)
- **DeepSeek Provider**: High-performance DeepSeek integration (deepseek-chat)
- **Local Provider**: Support for Ollama, LM Studio, etc.
- **MCP Provider**: Revolutionary Model Context Protocol integration
- **MCPGitHubProvider**: Specialized GitHub MCP with 26 native tools
- **Provider Factory**: Auto-selection, fallback logic, and multi-provider support

### 4. MCP Tools (`regoose/tools/`)
- **Filesystem Tool**: File operations via MCP protocol
- **Shell Tool**: Command execution with safety controls
- **Container Tool**: Podman/Docker orchestration
- **GitHub Tool**: Traditional GitHub API integration (PyGithub)
- All tools implement common `BaseTool` interface

### 5. GitHub MCP Integration (Revolutionary)
- **Native GitHub Tools**: 26 tools for autonomous AI operations
- **JSON-RPC Communication**: Direct MCP server communication via subprocess
- **AI Tool Calling**: LLM autonomously selects and calls GitHub tools
- **Line-Specific Comments**: Precise code feedback placement
- **Real-time Operations**: Dynamic PR reading, analysis, and publishing
- **Authentication**: Seamless GitHub Personal Access Token integration

## Key Design Patterns

### Multi-Provider Pattern
```python
# Pluggable LLM providers with auto-selection
llm = LLMProviderFactory.create_provider("openai", settings)
llm = LLMProviderFactory.create_provider("deepseek", settings)
llm = LLMProviderFactory.create_provider("auto", settings)  # Auto-selects best available

# Revolutionary MCP GitHub integration
mcp_provider = MCPGitHubProvider("openai", settings)
await mcp_provider.initialize()  # Starts MCP server with 26 GitHub tools
```

### Action/Scenario Pattern
```python
# Atomic actions for reusability
analyze_action = AnalyzeCodeAction()
test_action = GenerateTestsAction()  
github_action = MCPPRReviewAction()

# Composed scenarios for complex workflows
scenario = TestGenerationScenario(orchestrator)
result = await scenario.execute(input_data)

# GitHub MCP scenario with AI autonomy
mcp_scenario = MCPGitHubPRReviewScenario(orchestrator)
result = await mcp_scenario.execute({"pr_number": 123, "repo_owner": "org", "repo_name": "repo"})
```

### MCP GitHub Tool Pattern
```python
# AI autonomously calls GitHub tools via MCP
# No intermediate Python code - direct AI → GitHub API communication
tools_available = [
    "get_pull_request", "get_pull_request_files", "create_pull_request_review",
    "create_pull_request_review_comment", "search_code", # ... 21 more tools
]

# AI decides which tools to use and calls them directly
response = await mcp_provider.generate(
    prompt="Review PR #123 and place line-specific comments",
    tools=tools_available
)
```

### Session Management
```python
# Stateful execution tracking with Action/Scenario context
orchestrator = ActionOrchestrator(llm_provider, tools)
scenario = TestGenerationScenario(orchestrator)
result = await scenario.execute_with_improvements(input_data, max_iterations=3)
```

## Security Model

### Container Isolation
- All test execution happens in isolated Podman containers
- Security-first defaults: `--cap-drop ALL`, `--security-opt no-new-privileges`
- Read-only filesystem where possible
- Automatic cleanup of temporary resources

### Input Validation
- Code analysis before execution
- Timeout controls on all operations
- Safe handling of user-provided code
- Structured LLM outputs with validation

## Scalability Features

### Horizontal Scaling
- **Multi-Agent System**: Distribute work across specialized agents
- **Message Bus**: Async communication between components  
- **Orchestration Strategies**: Sequential, parallel, pipeline, graph execution
- **Provider Auto-Selection**: Fallback between local/remote LLMs

### Extensibility Points
- **Custom Providers**: Add new LLM backends
- **Custom Tools**: Extend MCP tool capabilities
- **Custom Agents**: Specialize for different domains
- **Custom Orchestration**: New execution strategies

## Data Flow

1. **Input**: User provides code via CLI
2. **Analysis**: LLM analyzes code structure and requirements
3. **Generation**: AI generates comprehensive test suite
4. **Isolation**: Tests executed in secure container environment
5. **Collection**: Results parsed and aggregated
6. **Reporting**: Markdown report with detailed analysis

## Future Roadmap

### Phase 1: Core Stability ✅
- Basic test generation and execution
- OpenAI integration
- Container isolation
- CLI interface

### Phase 2: Multi-Provider Support ✅
- Local LLM integration
- Provider auto-selection
- Enhanced configuration

### Phase 3: Multi-Agent Framework ✅
- Agent orchestration
- Message bus communication
- Graph execution patterns

### Phase 4: GitHub Integration ✅ 
- AI-powered GitHub PR reviews
- Native MCP GitHub integration with 26 tools
- Line-specific code comments
- Multi-provider LLM support (OpenAI, DeepSeek)
- Intelligent scoring and severity classification

### Phase 5: Advanced Features (Future)
- Web interface for team collaboration
- CI/CD integrations (GitHub Actions, Jenkins)
- Advanced test strategies (property-based, mutation testing)
- Performance optimization and caching
- Enterprise features and analytics

## Dependencies

### Core Dependencies
- **OpenAI**: LLM provider integration (GPT-4o-mini)
- **DeepSeek**: Alternative LLM provider integration
- **Pydantic**: Configuration and data validation
- **Typer + Rich**: CLI and user interface
- **AsyncIO**: Async execution support
- **PyGithub**: Traditional GitHub API integration

### Container Dependencies  
- **Podman/Docker**: Secure test execution
- **Python-on-whales**: Container orchestration

### MCP Dependencies
- **@modelcontextprotocol/server-github**: GitHub MCP server (npm package)
- **Node.js**: Required for MCP server execution
- **GitHub Personal Access Token**: Authentication for GitHub operations

### Testing Dependencies
- **Pytest**: Test framework and execution
- **Pytest-html**: HTML report generation
- **Pytest-json-report**: Structured result parsing

## Performance Characteristics

- **Startup Time**: < 2 seconds for basic operations
- **Test Generation**: 5-30 seconds depending on code complexity
- **GitHub PR Review**: 10-60 seconds depending on PR size and complexity
- **MCP Server Initialization**: 2-5 seconds for GitHub tools setup
- **Test Execution**: Variable based on test complexity
- **Memory Usage**: Minimal host footprint (containers handle execution)
- **Concurrency**: Async-first design supports multiple operations
- **AI Autonomy**: Direct tool calling eliminates intermediate API overhead

This revolutionary architecture provides a solid foundation for scaling from simple test generation to complex AI-powered development workflows with autonomous GitHub operations.
