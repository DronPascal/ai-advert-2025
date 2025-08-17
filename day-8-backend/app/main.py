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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# MCP Server URL
MCP_WEB3_URL = os.environ["MCP_WEB3_URL"]

# Direct Telegram API integration
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_USER_ID = os.environ["TELEGRAM_USER_ID"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def send_telegram_message(message: str) -> bool:
    """Send message directly to Telegram user via Bot API."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_USER_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            logger.info(f"Message sent successfully to Telegram user {TELEGRAM_USER_ID}")
            return True
        else:
            logger.error(f"Telegram API error: {result}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {str(e)}")
        return False

# Remote MCP Tools Configuration
tools = [
    {
        "type": "mcp",
        "server_url": MCP_WEB3_URL,
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
]

# System instructions for MCP-enhanced analysis
SYSTEM_INSTRUCTIONS = """
Ты — опытный крипто-аналитик. Используй доступный web3research MCP для получения актуальных данных.

ПРОЦЕСС:
1. Используй инструменты web3research MCP для получения:
   - Актуальных цен и рыночных данных 
   - Последних новостей криптовалютного рынка
   - Исследований по ключевым проектам
   - Анализа трендов и настроений рынка

2. На основе полученных данных создай структурированную сводку

ФОРМАТ СВОДКИ:
• **Рынок**: общий тренд, цены BTC/ETH, доминация
• **Новости**: ключевые события за день
• **Проекты**: обновления крупных протоколов  
• **Институты**: движения крупных игроков
• **Технологии**: новые решения и обновления
• **Прогноз**: краткосрочные ожидания

ПРАВИЛА:
- Максимум 800 символов
- Используй конкретные данные от MCP
- Человекочитаемый стиль с буллетами
- В конце отправь готовую сводку в Telegram

Начинай с исследования актуальной ситуации через web3research MCP.
"""

def run_crypto_digest() -> Tuple[str, str]:
    """
    Execute daily crypto digest using Responses API with Web3 MCP integration.
    
    Returns:
        Tuple of (response_id, digest_text)
    """
    try:
        logger.info("Starting crypto digest generation with Web3 MCP...")
        current_date = datetime.now().strftime('%d.%m.%Y')
        current_time = datetime.now().strftime('%H:%M')
        
        # Prepare request body with remote MCP tools
        body = {
            "model": MODEL,
            "tools": tools,  # Include remote MCP configuration
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": f"Создай ежедневную криптосводку за {current_date}. "
                    f"Текущее время: {current_time} Europe/Amsterdam. "
                    f"Используй web3research MCP для получения актуальных данных, "
                    f"затем создай структурированную сводку и отправь её в Telegram.",
        }
        
        # Make API call with MCP tools
        logger.info("Calling OpenAI Responses API with Web3 MCP...")
        logger.info(f"MCP Server URL: {MCP_WEB3_URL}")
        logger.info(f"Tools configured: {len(tools[0]['allowed_tools'])} tools available")
        
        response = client.responses.create(**body)
        
        # Extract response data
        response_id = response.id
        digest_text = getattr(response, "output_text", "").strip()
        
        logger.info(f"AI Response completed. ID: {response_id}")
        logger.info(f"Generated digest preview: {digest_text[:200]}...")
        
        # Send digest to Telegram
        if digest_text:
            logger.info("Sending digest to Telegram...")
            telegram_success = send_telegram_message(digest_text)
            
            if telegram_success:
                logger.info("✅ Crypto digest successfully sent to Telegram!")
            else:
                logger.error("❌ Failed to send digest to Telegram")
                raise Exception("Telegram delivery failed")
        else:
            logger.error("❌ No digest content generated by AI")
            raise Exception("Empty digest content")
        
        return response_id, digest_text
        
    except Exception as e:
        logger.error(f"Error in run_crypto_digest: {str(e)}")
        raise

def run_with_retries(max_retries: int = 3) -> Tuple[str, str]:
    """
    Run crypto digest with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (response_id, output_text)
    """
    for attempt in range(max_retries + 1):
        try:
            return run_crypto_digest()
            
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
        logger.info("=== Crypto Daily Digest Service Started (Web3 MCP Mode) ===")
        logger.info(f"Model: {MODEL}")
        logger.info(f"Web3 MCP URL: {MCP_WEB3_URL}")
        logger.info(f"Timezone: Europe/Amsterdam")
        
        # Run digest generation with retries
        response_id, digest_text = run_with_retries()
        
        logger.info("=== Crypto digest completed successfully ===")
        logger.info(f"Final response ID: {response_id}")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
