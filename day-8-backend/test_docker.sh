#!/bin/bash

echo "🧪 Docker Test Script for AI Insights"
echo "======================================"

echo "📋 Checking environment variables..."
docker-compose run --rm crypto-digest env | grep -E "(OPENAI_MODEL|SCHEDULE|TELEGRAM)" | sort

echo ""
echo "🧪 Testing simple version (no MCP)..."
docker-compose run --rm crypto-digest python3 main_simple.py

echo ""
echo "🤖 Testing MCP version (with tiktoken)..."  
docker-compose run --rm crypto-digest python3 main.py

echo ""
echo "⏰ Testing scheduler (immediate run)..."
docker-compose --profile test run --rm crypto-digest-test

echo ""
echo "✅ All tests completed!"
