#!/bin/bash

# Test OpenAI Responses API with Web3 MCP
# Based on OpenAI documentation: https://platform.openai.com/docs/guides/tools-remote-mcp

echo "Testing OpenAI Responses API with Web3 MCP..."

# Environment variables (set these before running)
OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_api_key_here}"
MCP_WEB3_URL="${MCP_WEB3_URL:-https://mcp.azazazaza.work/web3}"

# Check if API key is set
if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ Error: Set OPENAI_API_KEY environment variable"
    echo "Export your OpenAI API key: export OPENAI_API_KEY=sk-proj-..."
    exit 1
fi

echo "🔧 Using MCP URL: $MCP_WEB3_URL"
echo "🔑 Using API Key: ${OPENAI_API_KEY:0:10}..."

# Create the curl request
curl -X POST "https://api.openai.com/v1/responses" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -d '{
       "model": "gpt-4",
       "tools": [
         {
           "type": "mcp",
           "server_url": "'$MCP_WEB3_URL'",
           "server_label": "web3research",
           "allowed_tools": [
             "search",
             "create-research-plan", 
             "research-with-keywords",
             "fetch-content",
             "generate-report"
           ],
           "require_approval": "never"
         }
       ],
       "instructions": "Ты — крипто-аналитик. Используй web3research MCP для получения актуальных данных о криптовалютном рынке. Получи информацию о текущих ценах Bitcoin и Ethereum, а также последние новости. Создай краткую сводку в 3-4 пункта.",
       "input": "Проанализируй текущую ситуацию на криптовалютном рынке"
     }' \
     -w "\n\nHTTP Status: %{http_code}\nTotal Time: %{time_total}s\n" \
     -v

echo ""
echo "✅ Test completed!"
echo ""
echo "Expected responses:"
echo "- HTTP 200: Success (MCP tools work correctly)"
echo "- HTTP 500: Server error (MCP integration issue)"
echo "- HTTP 401: Authentication error (check API key)"
echo "- HTTP 400: Bad request (malformed JSON or parameters)"
