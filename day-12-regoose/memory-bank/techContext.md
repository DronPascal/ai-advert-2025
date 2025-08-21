# Technical Context - Regoose

## Technology Stack

### Core Language & Runtime
- **Python 3.10+**: Main implementation language
  - Chosen for AI/ML ecosystem compatibility
  - Rich async/await support for concurrent operations
  - Excellent library ecosystem for LLM integration
  - Strong typing support with Pydantic

### AI & Language Models
- **OpenAI API**: Primary LLM provider
  - GPT-4o-mini for cost-effective test generation
  - GPT-4o for complex analysis when needed
  - Structured output support for reliable parsing
- **Local LLM Support**: Ollama, LM Studio integration
  - Privacy-preserving option for sensitive code
  - Cost reduction for high-volume usage
  - Offline development capability

### Container Technology
- **Podman**: Primary container runtime
  - Rootless operation for enhanced security
  - Docker compatibility with better security defaults
  - No daemon requirement
- **Docker**: Alternative container runtime
  - Broader ecosystem support
  - Established CI/CD integration patterns

### Development Dependencies

#### Core Framework
```toml
openai = ">=1.51.0"           # LLM API integration
pydantic = ">=2.5.0"          # Data validation and settings
typer = ">=0.9.0"             # CLI framework
rich = ">=13.7.0"             # Rich terminal output
```

#### Testing & Quality
```toml
pytest = ">=8.0.0"            # Test framework
pytest-html = ">=4.1.1"      # HTML test reports
pytest-json-report = ">=1.5.0" # Structured test results
black = ">=23.12.1"           # Code formatting
isort = ">=5.13.2"            # Import sorting
```

#### Container Management
```toml
python-on-whales = ">=0.71.0" # Docker/Podman wrapper
```

#### Development Tools
```toml
python-dotenv = ">=1.0.0"     # Environment management
```

## Architecture Overview

### Modular Design
```
regoose/
├── core/          # Agent logic and session management
├── providers/     # LLM provider abstractions
├── tools/         # MCP tool implementations
├── framework/     # Multi-agent system components
└── cli.py         # Command-line interface
```

### Key Design Principles

#### Single Responsibility
- Each module has a focused purpose
- Clear separation between LLM logic and execution
- Distinct abstraction layers

#### Dependency Injection
- Provider pattern for LLM services
- Configurable tool implementations
- Testable component isolation

#### Async-First
- All I/O operations are async
- Non-blocking user interface
- Concurrent test execution capability

## Integration Patterns

### Model Context Protocol (MCP)
**Purpose**: Standardized tool integration

Current Implementation:
- **Filesystem Tool**: File operations with safety checks
- **Shell Tool**: Command execution with timeout controls
- **Container Tool**: Podman/Docker orchestration

Future Extensions:
- **Git Tool**: Version control operations
- **Database Tool**: Schema and data testing
- **API Tool**: REST/GraphQL endpoint testing

### LLM Provider Integration
**Abstraction Pattern**:
```python
class LLMProvider(ABC):
    async def generate(self, messages: List[Dict], **kwargs) -> LLMResponse
    def get_model_name(self) -> str
    def get_max_tokens(self) -> int
```

**Current Providers**:
- **OpenAI Provider**: Production-ready API integration
- **Local Provider**: Ollama/LM Studio support

**Future Providers**:
- **Anthropic Provider**: Claude integration
- **Azure OpenAI**: Enterprise deployment option
- **Google Provider**: PaLM/Gemini support

## Security Architecture

### Container Isolation
```bash
# Security-first container execution
podman run --rm \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --read-only \
  -v $test_dir:/app:ro \
  python:3.11-slim pytest /app
```

**Security Features**:
- No privileged operations
- Read-only file system where possible
- Minimal capability set
- Automatic cleanup

### Input Validation
- **Pydantic Models**: Type-safe configuration
- **Size Limits**: Code input length restrictions
- **Timeout Controls**: Prevent resource exhaustion
- **Sanitization**: Safe handling of user inputs

### API Key Management
- **Environment Variables**: Secure credential storage
- **No Logging**: API keys never logged or stored
- **Rotation Support**: Easy credential updates

## Development Environment

### Setup Requirements
```bash
# System dependencies
python >= 3.10
podman || docker
node.js (for MCP servers)

# Python environment
pip install -e .
pip install -e .[dev]  # Development dependencies
```

### Configuration Management
```bash
# Environment configuration
.env                   # Local settings
.env.example          # Template with documentation
pyproject.toml        # Project metadata and dependencies
```

### Development Workflow
```bash
# Code quality
black .               # Code formatting
isort .               # Import organization
pytest                # Test execution
mypy regoose/         # Type checking
```

## Performance Characteristics

### Latency Targets
- **Test Generation**: 5-30 seconds (depends on code complexity)
- **Container Startup**: < 5 seconds
- **Test Execution**: Variable (depends on test complexity)
- **Report Generation**: < 2 seconds

### Throughput Considerations
- **Concurrent Sessions**: Supports multiple simultaneous users
- **Container Pooling**: Reuse containers for efficiency
- **Async Operations**: Non-blocking I/O throughout

### Resource Usage
- **Memory**: Minimal host footprint (containers handle execution)
- **CPU**: Efficient async operations
- **Storage**: Temporary test files cleaned automatically
- **Network**: Only for LLM API calls

## Scalability Design

### Horizontal Scaling
- **Stateless Design**: No persistent state between sessions
- **Container Isolation**: Natural process boundaries
- **Message Bus**: Async communication between components
- **Provider Abstraction**: Load balancing across LLM services

### Multi-Agent Framework
```python
# Future multi-agent workflows
orchestrator = AgentOrchestrator()
orchestrator.register_agent(AnalyzerAgent())
orchestrator.register_agent(GeneratorAgent())
orchestrator.register_agent(ValidatorAgent())

plan = ExecutionPlan(
    strategy=OrchestrationStrategy.GRAPH,
    agents=["analyzer", "generator", "validator"],
    dependencies={"validator": ["analyzer", "generator"]}
)
```

## Deployment Patterns

### Local Development
- Single-user CLI tool
- Local container execution
- File-based configuration

### Team Integration
- Shared container registry
- Standardized test patterns
- Version-controlled configuration

### CI/CD Integration
- GitHub Actions workflows
- Docker-in-Docker support
- Artifact generation and storage

## Monitoring & Observability

### Logging Strategy
- **Structured Logging**: JSON format for machine parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Context Preservation**: Session IDs for tracing
- **Sensitive Data**: No API keys or user code in logs

### Error Tracking
- **Exception Handling**: Graceful degradation patterns
- **User-Friendly Messages**: Clear error descriptions
- **Debug Information**: Detailed context for troubleshooting
- **Recovery Suggestions**: Actionable next steps

### Performance Metrics
- **Generation Time**: LLM response latency
- **Execution Time**: Container operation duration
- **Success Rate**: Test generation and execution reliability
- **Resource Usage**: Memory and CPU utilization

## Future Technical Roadmap

### Phase 2: Enhanced Performance
- Container pooling and reuse
- Parallel test execution
- Caching strategies
- Performance monitoring

### Phase 3: Advanced Integration
- Database connectivity for persistent sessions
- Web interface with real-time updates
- Advanced debugging and profiling tools
- Team collaboration features

### Phase 4: AI Enhancement
- Fine-tuned models for specific domains
- Learning from user feedback
- Predictive test generation
- Cross-project knowledge sharing

This technical foundation provides a robust, secure, and scalable platform for AI-powered test generation that can evolve with changing requirements and technologies.
