# Project Brief: Crypto Daily Digest Service

## Core Mission
Automate daily cryptocurrency market analysis and delivery through intelligent agent orchestration using OpenAI Responses API with remote MCP servers.

## Key Requirements

### Functional Requirements
- **Daily Schedule**: Execute at 22:00 Europe/Amsterdam timezone
- **Data Sources**: Aggregate from web3-research-mcp and crypto-whitepapers-mcp
- **Content Generation**: Create concise 5-7 bullet point market summaries via GPT-4/5
- **Delivery**: Send formatted digest to Telegram via mcp-communicator-telegram
- **Orchestration**: Single Responses API call coordinates all MCP interactions

### Technical Requirements
- **Architecture**: Containerized Python service (Docker 24/7)
- **API Integration**: OpenAI Responses API with remote MCP tools
- **Scheduling**: APScheduler or cron-based execution
- **Reliability**: Retry logic with exponential backoff
- **Caching**: Response ID persistence for tool list optimization
- **Monitoring**: Comprehensive logging and health checks

### Business Value
- **Automation**: Eliminate manual crypto market monitoring
- **Consistency**: Daily digest delivery without human intervention  
- **Intelligence**: AI-powered analysis combining market data with whitepaper insights
- **Scalability**: Foundation for multi-channel crypto intelligence

## Success Criteria
1. **Reliability**: 99%+ daily delivery success rate
2. **Quality**: Relevant, concise, and actionable market insights
3. **Performance**: Complete analysis and delivery within 5 minutes
4. **Maintainability**: Zero-touch operations with observable failure modes

## Constraints
- **Remote MCP Requirement**: All MCP servers must be HTTP-accessible from OpenAI cloud
- **API Limits**: Respect OpenAI rate limits and token usage
- **Security**: No secrets in code, environment-based configuration only
- **Resource Efficiency**: Minimal container footprint and cost
