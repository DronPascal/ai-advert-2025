# Quick Test: OpenAI Responses API + Web3 MCP

## Simple curl command for testing

**Prerequisites**: 
- Set your OpenAI API key: `export OPENAI_API_KEY=sk-proj-...`
- Ensure Web3 MCP is running at: `https://mcp.azazazaza.work/web3`

### Basic Test Command

```bash
curl -X POST "https://api.openai.com/v1/responses" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -d '{
       "model": "gpt-4",
       "tools": [
         {
           "type": "mcp",
           "server_url": "https://mcp.azazazaza.work/web3",
           "server_label": "web3research",
           "allowed_tools": ["search", "research-with-keywords"],
           "require_approval": "never"
         }
       ],
       "instructions": "Use web3research MCP to get current Bitcoin price and create a brief 2-sentence summary.",
       "input": "What is the current Bitcoin price?"
     }'
```

### Expected Responses

- **200 OK**: MCP integration working correctly
- **500 Internal Server Error**: OpenAI remote MCP issue (known problem)
- **401 Unauthorized**: Check your API key
- **400 Bad Request**: Check JSON syntax

### Full Test Script

Run the complete test script:
```bash
./test_web3_mcp_curl.sh
```

### Debugging

If you get 500 errors, the MCP endpoints are working but OpenAI's remote MCP integration has issues. You can verify MCP endpoints directly:

```bash
# Test MCP health
curl https://mcp.azazazaza.work/web3/health

# Test MCP tools
curl -X POST https://mcp.azazazaza.work/web3/tools/list \
     -H "Content-Type: application/json" \
     -d '{}'
```

Both should return 200 OK responses if the MCP infrastructure is working correctly.
