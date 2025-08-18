# Technical Context: Crypto Daily Digest Service

## Technology Stack

### Core Technologies
- **Python 3.11**: Main application runtime with slim Docker base image
- **OpenAI Responses API**: AI orchestration and MCP tool coordination  
- **APScheduler**: Robust task scheduling with timezone support
- **Docker**: Containerized deployment with health checks
- **pytz**: Timezone handling for Europe/Amsterdam scheduling

### Dependencies
```python
# Core API client
openai>=1.50.0,<2.0.0

# Scheduling infrastructure  
APScheduler>=3.10.0,<4.0.0

# Time handling
pytz>=2023.3
python-dateutil>=2.8.0
```

## Architecture Constraints

### Remote MCP Integration
- **HTTP Requirement**: All MCP servers must expose HTTP endpoints (not stdio)
- **Public Accessibility**: OpenAI cloud must reach MCP servers via internet
- **Authentication**: Bearer token or header-based auth for secure MCP access
- **Tool Filtering**: Use `allowed_tools` to limit MCP surface area and reduce costs

### MCP Server Requirements

#### Deployed MCP Infrastructure ✅
**VPS Location**: weaselcloud-21551 (Ubuntu 24.04)  
**Access**: HTTPS via Cloudflare Tunnel

1. **web3-research-mcp**: Market data, token analysis, research reports
   - **Status**: ✅ DEPLOYED and FUNCTIONAL
   - **URL**: `https://mcp.azazazaza.work/web3`
   - **Tools Available**: 9 tools (search, create-research-plan, research-with-keywords, etc.)
   - **Implementation**: Node.js HTTP bridge with TypeScript compilation
   - **Container**: `web3-mcp-bridge` on port 3001

2. **crypto-whitepapers-mcp**: PDF analysis and knowledge base queries  
   - **Status**: ⚠️ DEPLOYED, PARTIALLY FUNCTIONAL
   - **URL**: `https://mcp.azazazaza.work/whitepapers`
   - **Tools Available**: Health check working, tools/list needs format fix
   - **Implementation**: Python Flask HTTP bridge with proper module installation
   - **Container**: `whitepapers-mcp-bridge` on port 3002

3. **Telegram Integration**: Direct Bot API (NOT MCP)
   - **Status**: ✅ IMPLEMENTED
   - **Implementation**: Direct HTTP calls to Telegram Bot API
   - **Configuration**: Bot token + user ID 7789201703

## VPS Deployment Architecture

### Infrastructure Overview
```
Internet → Cloudflare DNS → Cloudflare Tunnel → VPS (Ubuntu 24.04)
                                                    ↓
                                               nginx-proxy:80
                                                    ↓
                            ┌─────────────────────────────────────┐
                            │                                     │
              web3-mcp-bridge:3001              whitepapers-mcp-bridge:3002
                            │                                     │
                    web3-research-mcp                   crypto-whitepapers-mcp
                   (Node.js/TypeScript)                    (Python/Flask)
```

### Deployment Components

#### 1. Automated Deployment Script
**File**: `vps-deployment/deploy.sh`
- **Purpose**: Complete VPS setup from scratch
- **Features**:
  - User privilege checks (prevents root execution)
  - System package updates (apt-get)
  - Docker & Docker Compose installation
  - Node.js 18.x installation via NodeSource repository
  - Python 3.11 environment setup
  - MCP repository cloning and dependency installation
  - HTTP bridge creation (Node.js and Python)
  - Docker Compose configuration generation
  - Cloudflare Tunnel integration
  - Systemd service creation for auto-start

#### 2. Docker Environment
**Network**: `mcp-network` (bridge driver)
**Containers**:
- `web3-mcp-bridge`: Node.js Alpine with TypeScript compilation
- `whitepapers-mcp-bridge`: Python 3.11-slim with Flask
- `nginx-proxy`: nginx:alpine for HTTP routing
- `cloudflared-tunnel`: Cloudflare tunnel client

#### 3. HTTP Bridge Implementation

##### web3-research-mcp Bridge (Node.js)
```javascript
// Converts stdio MCP to HTTP endpoints
app.post('/tools/list', async (req, res) => {
    const mcp = spawn('node', ['dist/server.js'], { 
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: '/app/web3-research-mcp'
    });
    // JSONRPC request/response handling
});
```

##### crypto-whitepapers-mcp Bridge (Python/Flask)
```python
# Converts stdio MCP to HTTP endpoints  
@app.route('/tools/list', methods=['POST'])
def tools_list():
    result = subprocess.run(
        [sys.executable, '-m', 'crypto_whitepapers_mcp.cli'],
        input=json.dumps(mcp_request),
        text=True, capture_output=True, timeout=30
    )
```

### Network Configuration

#### nginx Proxy Setup
```nginx
events { worker_connections 1024; }
http {
    upstream web3_backend { server web3-mcp-bridge:3001; }
    upstream whitepapers_backend { server whitepapers-mcp-bridge:3002; }
    
    server {
        listen 80;
        location /web3/ {
            rewrite ^/web3/(.*) /$1 break;
            proxy_pass http://web3_backend;
        }
        location /whitepapers/ {
            rewrite ^/whitepapers/(.*) /$1 break;
            proxy_pass http://whitepapers_backend;
        }
    }
}
```

#### Cloudflare Tunnel Configuration
- **Domain**: mcp.azazazaza.work
- **Service Mapping**:
  - `/web3` → nginx-proxy:80/web3
  - `/whitepapers` → nginx-proxy:80/whitepapers
- **HTTPS Termination**: Handled by Cloudflare
- **Authentication**: Tunnel token-based

### Deployment Issues & Solutions

#### Common Issues Encountered
1. **User Privileges**: Script must run as non-root user with sudo
2. **Directory Creation**: Bridge directories need explicit mkdir before file creation
3. **Docker Group**: User must be added to docker group for container management
4. **Python Modules**: MCP packages need proper installation with pip install -e
5. **Entry Points**: MCP entry points vary (dist/server.js vs src/module/cli.py)
6. **Requirements Files**: Some MCP repos missing requirements.txt files

#### Troubleshooting Commands
```bash
# Check container status
docker-compose ps

# View container logs
docker logs web3-mcp-bridge
docker logs whitepapers-mcp-bridge

# Test local endpoints
curl http://localhost:3001/health
curl http://localhost:3002/health

# Test MCP tools
curl -X POST http://localhost:3001/tools/list -H "Content-Type: application/json" -d '{}'

# Check Docker networking
docker network inspect mcp-network
docker exec nginx-proxy ping web3-mcp-bridge
```

## Development Setup

### Environment Configuration
```bash
# Required environment variables
OPENAI_API_KEY=sk-proj-...

# Deployed MCP Server URLs (HTTPS via Cloudflare Tunnel)
MCP_WEB3_URL=https://mcp.azazazaza.work/web3
MCP_WHITEPAPER_URL=https://mcp.azazazaza.work/whitepapers

# Direct Telegram Integration  
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_USER_ID=7789201703

# Optional configuration
OPENAI_MODEL=gpt-4
SCHEDULE_HOUR=22
SCHEDULE_MINUTE=0
```

### Docker Infrastructure
- **Base Image**: `python:3.11-slim` for minimal footprint
- **Multi-stage**: Optimized for production deployment
- **Health Checks**: Built-in container health monitoring
- **Logging**: Structured logs to `/var/log/` with rotation
- **Caching**: Response ID persistence in `/tmp/` for optimization

## Technical Constraints

### API Limitations
- **OpenAI Rate Limits**: Respect Responses API quotas and usage patterns
- **Token Management**: Optimize prompt size and tool list caching
- **Cost Control**: Use `previous_response_id` to cache tool lists between calls

### Operational Requirements
- **Timezone Precision**: Europe/Amsterdam for consistent 22:00 execution
- **Retry Logic**: Exponential backoff for network failures (max 3 attempts)
- **Resource Limits**: 512MB memory, 0.5 CPU cores maximum
- **Log Management**: 10MB rotation, 3 file retention

### Security Considerations
- **No Secrets in Code**: All sensitive data via environment variables
- **Container Security**: Non-root user, minimal attack surface
- **Network Security**: HTTPS-only for all external communications
- **Data Privacy**: No persistent storage of market data or user information

## Development Tools

### Local Development
```bash
# Development compose with mock servers
docker-compose -f docker-compose.dev.yml up

# Test execution
./scripts/test.sh

# Direct scheduler test
docker-compose exec crypto-digest python scheduler.py --test
```

### Monitoring & Debugging
- **Health Endpoint**: Container health checks every 60s
- **Log Aggregation**: JSON-structured logging for external tools
- **Performance Tracking**: Execution time and success rate monitoring
- **Error Alerting**: Failed execution detection and notification

## Known Technical Challenges

### OpenAI Remote MCP Integration (CRITICAL)
- **Challenge**: OpenAI Responses API + remote MCP tools cause 500 errors
- **Status**: ❌ BLOCKED - All attempts result in server errors
- **Evidence**: MCP endpoints work perfectly when tested directly
- **Request IDs**: req_c8d729517aa4db0f5a76ed48d10bbbb4, req_f644bde7c218e6621d0f7e7fff2cf30f
- **Workaround**: Fallback mode without MCP tools (functional)
- **Alternative**: Direct MCP integration or Chat API function calling

### MCP Server HTTP Wrappers (RESOLVED)
- **Challenge**: Most MCP servers designed for stdio transport
- **Solution**: ✅ COMPLETED - Custom HTTP bridges implemented
  - Node.js bridge for web3-research-mcp (TypeScript compilation working)
  - Python Flask bridge for crypto-whitepapers-mcp (module installation working)
- **Deployment**: ✅ COMPLETED - VPS deployment with Cloudflare Tunnel

### Network Reliability
- **Challenge**: Remote MCP calls can fail or timeout  
- **Solution**: Comprehensive retry logic implemented
- **Status**: ✅ RESOLVED - HTTP endpoints stable and responding
- **Monitoring**: Docker health checks and nginx proxy logs

### Cost Optimization
- **Challenge**: Daily Responses API calls can accumulate costs
- **Solution**: Tool list caching, prompt optimization, selective tool access
- **Measurement**: Token usage tracking and cost per digest calculation
- **Current**: Using fallback mode to avoid MCP integration costs

### Docker Networking (MINOR)
- **Challenge**: Container DNS resolution issues (nslookup fails)
- **Impact**: Does not affect functionality (ping works, HTTP requests work)
- **Status**: Acceptable - services communicate correctly despite DNS warnings
