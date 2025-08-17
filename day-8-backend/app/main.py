#!/usr/bin/env python3
"""
Daily crypto digest using OpenAI Responses API with Web3 MCP integration
"""
import os
import sys
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Tuple
from openai import OpenAI

# Configure logging (console only for demo)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# MCP Server URL - using working tiktoken MCP for demo
MCP_TIKTOKEN_URL = "https://gitmcp.io/openai/tiktoken"

# Direct Telegram API integration
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_USER_ID = os.environ["TELEGRAM_USER_ID"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def send_telegram_message(message: str) -> bool:
    """Send message directly to Telegram user via Bot API (DEMO MODE)."""
    try:
        # DEMO MODE: Just log the message instead of sending to Telegram
        logger.info("="*60)
        logger.info("📱 TELEGRAM MESSAGE (DEMO MODE):")
        logger.info("="*60)
        logger.info(f"TO: User {TELEGRAM_USER_ID}")
        logger.info(f"MESSAGE:\n{message}")
        logger.info("="*60)
        
        logger.info(f"✅ Message would be sent to Telegram user {TELEGRAM_USER_ID}")
        return True
            
    except Exception as e:
        logger.error(f"Error in demo telegram function: {str(e)}")
        return False

# Remote MCP Tools Configuration
tools = [
    {
        "type": "mcp",
        "server_url": MCP_TIKTOKEN_URL,
        "server_label": "tiktoken",
        "allowed_tools": [
            "fetch_tiktoken_documentation",
            "search_tiktoken_documentation", 
            "search_tiktoken_code",
            "fetch_generic_url_content"
        ],
        "require_approval": "never"
    }
]

# System instructions for tiktoken MCP analysis
SYSTEM_INSTRUCTIONS = """
Ты — AI-эксперт и технический писатель. Используй tiktoken MCP для создания познавательного ежедневного контента.

ПРОЦЕСС:
1. Используй tiktoken MCP инструменты для получения информации:
   - fetch_tiktoken_documentation: получи основную документацию
   - search_tiktoken_documentation: найди интересные детали  
   - search_tiktoken_code: изучи примеры кода
   - fetch_generic_url_content: получи дополнительные материалы

2. Создай познавательную сводку об AI/токенизации

ФОРМАТ СВОДКИ:
🤖 **AI Insights Daily**

• **Технология дня**: что такое tiktoken и зачем нужен
• **Практическое применение**: как используется в GPT моделях
• **Интересный факт**: малоизвестная особенность токенизации
• **Совет разработчику**: практический пример использования
• **AI тренд**: связь с современными языковыми моделями

ПРАВИЛА:
- Максимум 1000 символов
- Используй данные от tiktoken MCP
- Простой язык, интересно для широкой аудитории
- Добавь эмодзи для читаемости
- В конце отправь сводку в Telegram

Начинай с изучения tiktoken через MCP инструменты.
"""

def run_ai_insights() -> Tuple[str, str]:
    """
    Execute daily AI insights using Responses API with tiktoken MCP integration.
    
    Returns:
        Tuple of (response_id, insights_text)
    """
    try:
        logger.info("Starting AI insights generation with tiktoken MCP...")
        current_date = datetime.now().strftime('%d.%m.%Y')
        current_time = datetime.now().strftime('%H:%M')
        
        # Prepare request body with remote MCP tools
        body = {
            "model": MODEL,
            "tools": tools,  # Include remote MCP configuration
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": f"Создай ежедневную AI Insights сводку за {current_date}. "
                    f"Текущее время: {current_time} Europe/Amsterdam. "
                    f"Используй tiktoken MCP для получения информации о токенизации, "
                    f"затем создай познавательную сводку и отправь её в Telegram.",
        }
        
        # Make API call with MCP tools
        logger.info("Calling OpenAI Responses API with tiktoken MCP...")
        logger.info(f"MCP Server URL: {MCP_TIKTOKEN_URL}")
        logger.info(f"Tools configured: {len(tools[0]['allowed_tools'])} tools available")
        
        response = client.responses.create(**body)
        
        # Extract response data
        response_id = response.id
        insights_text = getattr(response, "output_text", "").strip()
        
        logger.info(f"AI Response completed. ID: {response_id}")
        logger.info(f"Generated insights preview: {insights_text[:200]}...")
        
        # Send insights to Telegram
        if insights_text:
            logger.info("Sending insights to Telegram...")
            telegram_success = send_telegram_message(insights_text)
            
            if telegram_success:
                logger.info("✅ AI Insights successfully sent to Telegram!")
            else:
                logger.error("❌ Failed to send insights to Telegram")
                raise Exception("Telegram delivery failed")
        else:
            logger.error("❌ No insights content generated by AI")
            raise Exception("Empty insights content")
        
        return response_id, insights_text
        
    except Exception as e:
        logger.error(f"Error in run_ai_insights: {str(e)}")
        raise

def run_with_retries(max_retries: int = 3) -> Tuple[str, str]:
    """
    Run AI insights with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (response_id, output_text)
    """
    for attempt in range(max_retries + 1):
        try:
            return run_ai_insights()
            
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(e)}")
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
            
            import time
            time.sleep(wait_time)

if __name__ == "__main__":
    try:
        logger.info("=== AI Insights Daily Service Started (tiktoken MCP Mode) ===")
        logger.info(f"Model: {MODEL}")
        logger.info(f"tiktoken MCP URL: {MCP_TIKTOKEN_URL}")
        logger.info(f"Timezone: Europe/Amsterdam")
        
        # Run insights generation with retries
        response_id, insights_text = run_with_retries()
        
        logger.info("=== AI Insights completed successfully ===")
        logger.info(f"Final response ID: {response_id}")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
