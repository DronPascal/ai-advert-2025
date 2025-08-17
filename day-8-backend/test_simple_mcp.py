#!/usr/bin/env python3
"""
Test script with simplified MCP configuration
"""
import os
import logging
from datetime import datetime
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment - читаем из .env файла вручную
OPENAI_API_KEY = None
MCP_WEB3_URL = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                OPENAI_API_KEY = line.split('=', 1)[1].strip()
            elif line.startswith('MCP_WEB3_URL='):
                MCP_WEB3_URL = line.split('=', 1)[1].strip()
except FileNotFoundError:
    logger.error(".env file not found")
    exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found")
    exit(1)
if not MCP_WEB3_URL:
    logger.error("MCP_WEB3_URL not found")
    exit(1)

MODEL = "gpt-4"
client = OpenAI(api_key=OPENAI_API_KEY)

# Test with simplified MCP configuration
def test_with_simple_mcp():
    """Test with one simplified MCP tool"""
    try:
        logger.info(f"Testing with single MCP: {MCP_WEB3_URL}")
        
        # Very simple MCP configuration
        tools = [
            {
                "type": "mcp",
                "server_label": "web3research",
                "server_url": MCP_WEB3_URL,
                "allowed_tools": ["search"],  # Only one tool
                "require_approval": "never"
            }
        ]
        
        body = {
            "model": MODEL,
            "tools": tools,
            "instructions": "Use web3research search tool to find Bitcoin price info. Return simple text summary.",
            "input": "Search for Bitcoin price information using the search tool.",
        }
        
        logger.info("Calling OpenAI Responses API with MCP...")
        response = client.responses.create(**body)
        
        response_id = response.id
        digest_text = getattr(response, "output_text", "").strip()
        
        logger.info(f"✅ Success! Response ID: {response_id}")
        logger.info(f"Generated text: {digest_text}")
        
        return response_id, digest_text
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        # Log the full exception details
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    test_with_simple_mcp()
