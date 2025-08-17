#!/usr/bin/env python3
"""
Test script without MCP tools to verify OpenAI Responses API basic functionality
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
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                OPENAI_API_KEY = line.split('=', 1)[1].strip()
                break
except FileNotFoundError:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in .env file or environment")
    exit(1)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# Initialize client
client = OpenAI(api_key=OPENAI_API_KEY)

# Simple test without MCP tools
def test_without_mcp():
    """Test Responses API without any MCP tools"""
    try:
        logger.info("Testing Responses API without MCP tools...")
        
        # Simple request without tools
        body = {
            "model": MODEL,
            "instructions": """
Ты — крипто-аналитик. Создай краткую сводку по криптовалютному рынку на основе общих знаний.

ЗАДАЧА:
Сформируй краткую сводку: 3-5 пунктов о текущем состоянии крипторынка.

ПРАВИЛА:
- Используй общие знания о Bitcoin, Ethereum и основных трендах
- Максимум 500 символов
- Только буллеты (•)
- Человекочитаемый текст

ФОРМАТ: Просто готовый текст сводки.
            """,
            "input": f"Создай криптосводку за {datetime.now().strftime('%d.%m.%Y')}. " + 
                    "Используй общие знания о рынке криптовалют.",
        }
        
        logger.info("Calling OpenAI Responses API...")
        response = client.responses.create(**body)
        
        # Extract response
        response_id = response.id
        digest_text = getattr(response, "output_text", "").strip()
        
        logger.info(f"✅ Success! Response ID: {response_id}")
        logger.info(f"Generated text: {digest_text}")
        
        return response_id, digest_text
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_without_mcp()
