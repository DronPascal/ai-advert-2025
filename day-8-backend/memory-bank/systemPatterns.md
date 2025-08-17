# System Patterns: Crypto Daily Digest Service

## Core Architecture Pattern

### Hybrid MCP Architecture
The system implements a **Hybrid MCP Architecture** with multiple fallback patterns:

#### Primary Pattern: Remote MCP Orchestration
```
Python Service (Scheduler) 
    ↓ (Daily trigger)
OpenAI Responses API (Single call)
    ↓ (Parallel tool calls)
2x Remote MCP Servers (HTTPS) → External Data Sources
    ↓
Direct Telegram API (Not MCP) → Message Delivery
```

#### Fallback Pattern: Knowledge-Based Generation
```
Python Service (Scheduler)
    ↓ (Daily trigger)
OpenAI Responses API (No MCP tools)
    ↓ (Enhanced prompts)
AI Knowledge Base → Crypto Analysis
    ↓
Direct Telegram API → Message Delivery
```

**Benefits**:
- Dual-mode operation for reliability
- Infrastructure independence (fallback mode)
- Self-contained business logic in prompts
- Proven working alternative when primary fails

## Key Design Patterns

### 1. HTTP Bridge Pattern (VPS Infrastructure)
```bash
# Convert stdio-based MCP to HTTP endpoints
MCP Server (stdio) → HTTP Bridge → nginx Proxy → Cloudflare Tunnel → HTTPS
```

**Implementation**:
- **Node.js Bridge**: Spawns MCP process, handles JSONRPC over HTTP
- **Python Flask Bridge**: Module import + subprocess execution over HTTP  
- **nginx Proxy**: Path-based routing with rewrites
- **Cloudflare Tunnel**: HTTPS termination and public access

**Benefits**:
- Makes stdio-only MCPs accessible to OpenAI cloud
- Provides HTTPS without certificate management
- Enables horizontal scaling of MCP instances
- Centralized logging and monitoring

### 2. Automated Infrastructure Pattern
```bash
# Single script deployment from zero to production
VPS (Fresh) → deploy.sh → Complete MCP Infrastructure (30 min)
```

**Components**:
- **System Setup**: Package management, Docker, Node.js, Python
- **Repository Management**: Git cloning, dependency installation
- **Container Orchestration**: Docker Compose generation
- **Network Configuration**: nginx proxy, Docker networking
- **External Integration**: Cloudflare Tunnel setup

**Principles**:
- **Idempotent**: Can run multiple times safely
- **Atomic**: Either full success or clean failure
- **Documented**: Every step logged and explained
- **Recoverable**: Clear rollback and retry strategies

### 3. Agent Coordination Pattern
```python
# Single Responses API call coordinates everything
response = client.responses.create(
    model="gpt-4",
    tools=[web3_mcp, whitepapers_mcp, telegram_mcp],
    instructions="Gather data → Analyze → Format → Send",
    input="Generate daily crypto digest"
)
```

**Principles**:
- AI agent makes all coordination decisions
- No complex workflow orchestration in code
- Declarative instructions define business logic
- Fault tolerance through AI reasoning

### 2. Tool List Caching Pattern
```python
# Cache tool definitions between calls
body = {
    "previous_response_id": last_response_id,  # Reuse cached tools
    "tools": tools,  # Only refreshed when cache miss
    "instructions": instructions
}
```

**Benefits**:
- Reduced token usage and API costs
- Faster response times
- Consistent tool availability

### 3. Exponential Backoff Retry Pattern
```python
for attempt in range(max_retries):
    try:
        return execute_digest()
    except Exception as e:
        delay = min(60, 2 ** attempt)
        time.sleep(delay)
```

**Characteristics**:
- Progressive delay scaling: 1s, 2s, 4s, 8s...
- Maximum delay cap (60s)
- Logging for observability
- Graceful degradation

### 4. Environment-Based Configuration Pattern
```python
# All configuration via environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MCP_WEB3_URL = os.environ["MCP_WEB3_URL"]
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "22"))
```

**Security Benefits**:
- No secrets in source code
- Container-native configuration
- Easy deployment across environments
- Audit trail through environment management

## Component Relationships

### Application Layer (Backend)
- **APScheduler**: Manages daily execution timing in Europe/Amsterdam
- **OpenAI Client**: Handles Responses API communication with retry logic
- **Telegram API**: Direct HTTP calls for message delivery (bypasses MCP)
- **Environment Management**: Configuration via .env files

### Infrastructure Layer (VPS)
- **Docker Compose**: Orchestrates 4 containers (bridges + proxy + tunnel)
- **nginx Proxy**: HTTP routing with path rewrites (/web3, /whitepapers)
- **Cloudflare Tunnel**: HTTPS public access without port forwarding
- **Docker Network**: Container-to-container communication (mcp-network)

### MCP Bridge Layer
- **web3-mcp-bridge**: Node.js HTTP wrapper for web3-research-mcp
  - TypeScript compilation (npm run build)
  - Process spawning for stdio MCP
  - JSONRPC request/response translation
  - Health checks and error handling
- **whitepapers-mcp-bridge**: Python Flask wrapper for crypto-whitepapers-mcp
  - Module installation (pip install -e)
  - Subprocess execution for MCP CLI
  - HTTP endpoint exposure (/tools/list, /tools/call)
  - Exception handling and logging

### External Integration Layer
- **Cloudflare DNS**: Domain resolution and CDN
- **VPS Provider**: Ubuntu 24.04 hosting environment
- **GitHub**: MCP repository sources (cloned during deployment)
- **Docker Hub**: Base images for containerization

## Data Flow Patterns

### Primary Flow (Remote MCP)
```
1. Scheduler Trigger (22:00 Amsterdam)
   ↓
2. OpenAI Responses API Call
   ↓ (Parallel MCP tool calls)
3. HTTPS → Cloudflare → nginx → Bridge Containers
   ├─ web3-mcp-bridge:3001 → web3-research-mcp (9 tools)
   └─ whitepapers-mcp-bridge:3002 → crypto-whitepapers-mcp
   ↓
4. AI Analysis & Synthesis
   ↓
5. Direct Telegram API Call
   ↓
6. Message Delivery to User ID 7789201703
```

### Fallback Flow (Knowledge-Based)
```
1. Scheduler Trigger (22:00 Amsterdam)
   ↓
2. OpenAI Responses API Call (No MCP tools)
   ↓
3. Enhanced Prompts + AI Knowledge Base
   ↓
4. Crypto Market Analysis (Built-in knowledge)
   ↓
5. Direct Telegram API Call
   ↓
6. Message Delivery to User ID 7789201703
```

### Bridge Communication Pattern
```
HTTP Request → Bridge Server → Spawn MCP Process → stdio Communication
     ↓               ↓                ↓                    ↓
JSON over HTTP → Express/Flask → subprocess/spawn → JSONRPC stdin/stdout
     ↓               ↓                ↓                    ↓
HTTP Response ← JSON Response ← Process Output ← JSONRPC Response
```

## Error Handling Patterns

### Circuit Breaker Pattern (Future)
For production deployment, implement circuit breaker for MCP calls:
- **Closed**: Normal operation
- **Open**: Stop calls after failure threshold  
- **Half-Open**: Test recovery with limited calls

### Graceful Degradation
- **Primary Source Failure**: Continue with available MCP servers
- **Partial Data**: Generate digest with available information
- **Delivery Failure**: Log and attempt retry with different method

## Observability Patterns

### Structured Logging
```python
logger.info("Digest generation started", extra={
    "timestamp": datetime.now().isoformat(),
    "mcp_servers": ["web3", "whitepapers", "telegram"],
    "response_id": response_id
})
```

### Health Check Pattern
```dockerfile
HEALTHCHECK --interval=60s --timeout=10s \
    CMD python -c "import sys; print('Health OK'); sys.exit(0)"
```

### Metrics Collection Points
- Execution duration and success rate
- MCP server response times and availability  
- Token usage and API costs
- Digest delivery confirmation rates

## Security Patterns

### Principle of Least Privilege
- **MCP Tools**: Only essential tools in `allowed_tools`
- **Container**: Non-root user execution
- **Network**: Minimal required ports and protocols

### Defense in Depth
- **API Keys**: Environment-only, never in code
- **Transport**: HTTPS-only for all external calls
- **Validation**: Input sanitization for MCP responses
- **Audit**: Comprehensive logging for security events
