# Regoose Architecture

Regoose is built with a modular, scalable architecture inspired by [Goose](https://github.com/block/goose) and [LangGraph](https://github.com/langchain-ai/langgraph) patterns.

## Core Components

### 1. CLI Interface (`regoose/cli.py`)
- **Command-line interface** for user interaction
- **Interactive mode** for real-time testing
- **Setup wizard** for configuration
- Built with Typer and Rich for excellent UX

### 2. Core Agent (`regoose/core/`)
- **RegooseAgent**: Main orchestrator for test generation workflow
- **Session**: Stateful conversation and execution tracking  
- **Configuration**: Environment-based settings management
- Follows Goose's session-based architecture patterns

### 3. LLM Providers (`regoose/providers/`)
- **Abstract Provider Interface**: Pluggable LLM support
- **OpenAI Provider**: Production-ready OpenAI integration
- **Local Provider**: Support for Ollama, LM Studio, etc.
- **Provider Factory**: Auto-selection and fallback logic

### 4. MCP Tools (`regoose/tools/`)
- **Filesystem Tool**: File operations via MCP protocol
- **Shell Tool**: Command execution with safety controls
- **Container Tool**: Podman/Docker orchestration
- All tools implement common `BaseTool` interface

### 5. Multi-Agent Framework (`regoose/framework/`)
- **BaseAgent**: Foundation for specialized agents
- **Orchestrator**: Coordinates multi-agent workflows
- **Message Bus**: Communication system between agents
- **Execution Strategies**: Sequential, parallel, pipeline, graph
- Inspired by LangGraph's graph-based execution

## Key Design Patterns

### Provider Pattern
```python
# Pluggable LLM providers
llm = LLMProviderFactory.create_provider("openai", settings)
llm = LLMProviderFactory.create_provider("local", settings)
```

### Tool Pattern (MCP Integration)
```python
# Unified tool interface
result = await filesystem.execute("write_file", path="test.py", content=code)
result = await shell.execute("pytest test.py")
```

### Session Management
```python
# Stateful execution tracking
session = agent.create_session()
session.add_message("user", "Generate tests for this code")
session.add_test_result(test_result)
```

### Multi-Agent Orchestration
```python
# Graph-based agent coordination
plan = orchestrator.create_execution_plan(
    strategy=OrchestrationStrategy.GRAPH,
    agents=["analyzer", "generator", "validator"],
    dependencies={"validator": ["analyzer", "generator"]}
)
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

### Phase 4: Advanced Features (Future)
- Web interface
- CI/CD integrations
- Advanced test strategies
- Performance optimization
- Team collaboration features

## Dependencies

### Core Dependencies
- **OpenAI**: LLM provider integration
- **Pydantic**: Configuration and data validation
- **Typer + Rich**: CLI and user interface
- **AsyncIO**: Async execution support

### Container Dependencies  
- **Podman/Docker**: Secure test execution
- **Python-on-whales**: Container orchestration

### Testing Dependencies
- **Pytest**: Test framework and execution
- **Pytest-html**: HTML report generation
- **Pytest-json-report**: Structured result parsing

## Performance Characteristics

- **Startup Time**: < 2 seconds for basic operations
- **Test Generation**: 5-30 seconds depending on code complexity
- **Test Execution**: Variable based on test complexity
- **Memory Usage**: Minimal host footprint (containers handle execution)
- **Concurrency**: Async-first design supports multiple operations

This architecture provides a solid foundation for scaling from simple test generation to complex multi-agent development workflows.
