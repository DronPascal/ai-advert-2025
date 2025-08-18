#!/bin/bash

# Test script for crypto digest service
set -e

echo "🚀 Crypto Digest Service Test Script"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from env.example...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✅ Created .env file. Please edit it with your actual values.${NC}"
    else
        echo -e "${RED}❌ env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# Function to check environment variables
check_env() {
    local var_name=$1
    local var_value=${!var_name}
    
    if [ -z "$var_value" ] || [ "$var_value" = "your_openai_api_key_here" ]; then
        echo -e "${RED}❌ $var_name is not set or has default value${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $var_name is configured${NC}"
        return 0
    fi
}

# Load environment variables
source .env

echo ""
echo "🔧 Checking configuration..."

# Check required environment variables
env_ok=true
check_env "OPENAI_API_KEY" || env_ok=false
check_env "MCP_WEB3_URL" || env_ok=false
check_env "MCP_WHITEPAPER_URL" || env_ok=false
check_env "TELEGRAM_BOT_TOKEN" || env_ok=false
check_env "TELEGRAM_USER_ID" || env_ok=false

if [ "$env_ok" = false ]; then
    echo -e "${RED}❌ Please configure required environment variables in .env${NC}"
    exit 1
fi

echo ""
echo "🐳 Building Docker image..."
docker-compose build

echo ""
echo "📋 Running test execution..."
echo "This will immediately trigger the crypto digest process."
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test cancelled."
    exit 0
fi

# Run test
echo ""
echo "🧪 Starting test execution..."
docker-compose --profile test run --rm crypto-digest-test

echo ""
echo "📊 Test completed. Check the logs above for results."
echo ""
echo "🔍 To check logs:"
echo "   docker-compose logs crypto-digest"
echo ""
echo "🚀 To start the service:"  
echo "   docker-compose up -d"
echo ""
echo "⏹️  To stop the service:"
echo "   docker-compose down"

