#!/bin/bash

# Test OpenAI Responses API with tiktoken MCP (known working)
# This MCP server is proven to work with OpenAI Responses API

echo "Testing OpenAI Responses API with tiktoken MCP..."

# Environment variables (set these before running)
OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_api_key_here}"

# Check if API key is set
if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ Error: Set OPENAI_API_KEY environment variable"
    echo "Export your OpenAI API key: export OPENAI_API_KEY=sk-proj-..."
    exit 1
fi

echo "🔧 Using tiktoken MCP URL: https://gitmcp.io/openai/tiktoken"
echo "🔑 Using API Key: ${OPENAI_API_KEY:0:10}..."

# Create the curl request for AI Insights
curl -X POST "https://api.openai.com/v1/responses" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -d '{
       "model": "gpt-4",
       "tools": [
         {
           "type": "mcp",
           "server_url": "https://gitmcp.io/openai/tiktoken",
           "server_label": "tiktoken",
           "allowed_tools": [
             "fetch_tiktoken_documentation",
             "search_tiktoken_documentation", 
             "search_tiktoken_code",
             "fetch_generic_url_content"
           ],
           "require_approval": "never"
         }
       ],
       "instructions": "Ты — AI-эксперт. Используй tiktoken MCP для создания познавательного контента. Получи документацию о tiktoken, найди интересный факт о токенизации, и создай краткую сводку в 3-4 пункта на русском языке.",
       "input": "Создай AI Insights сводку о токенизации"
     }' \
     -w "\n\nHTTP Status: %{http_code}\nTotal Time: %{time_total}s\n" \
     -v

echo ""
echo "✅ Test completed!"
echo ""
echo "Expected responses:"
echo "- HTTP 200: Success (tiktoken MCP works correctly)"
echo "- HTTP 500: Server error (OpenAI issue)"
echo "- HTTP 401: Authentication error (check API key)"
echo "- HTTP 400: Bad request (malformed JSON or parameters)"
