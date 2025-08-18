#!/bin/bash

# Test script for tiktoken + DeepWiki MCP integration

echo "🚀 Testing tiktoken + DeepWiki MCP Integration"
echo "=============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ No .env file found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
echo "✅ Checking environment variables..."

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set"
    exit 1
fi

if [ -z "$TELEGRAM_USER_ID" ]; then
    echo "❌ TELEGRAM_USER_ID not set"
    exit 1
fi

echo "✅ Environment variables configured"

# Test with Python directly
echo ""
echo "🐍 Testing with Python (immediate execution)..."
echo "Expected behavior:"
echo "1. AI searches tiktoken documentation"
echo "2. AI asks DeepWiki for additional knowledge"
echo "3. AI creates unified technical summary"
echo "4. Summary sent to Telegram"

cd app
python3 main.py
cd ..

echo ""
echo "🔍 Check logs above for:"
echo "✓ 'tiktoken + DeepWiki integration' messages"
echo "✓ 'Tools configured: 2 tools from 2 MCP servers'"
echo "✓ HTTP 200 OK response"
echo "✓ Successful Telegram delivery"
echo ""
echo "📱 Check your Telegram for the technical summary! 🤖🔍📚"
