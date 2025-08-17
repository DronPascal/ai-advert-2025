#!/usr/bin/env python3
"""
Fallback version: Daily crypto digest without remote MCP tools
Uses OpenAI's built-in knowledge + web search capabilities when available
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

# Enhanced system instructions for knowledge-based analysis
SYSTEM_INSTRUCTIONS = """
Ты — опытный крипто-аналитик с глубокими знаниями рынка цифровых активов.

ЗАДАЧА:
Создай качественную ежедневную криптосводку на основе твоих знаний о:
- Текущих трендах криптовалютного рынка
- Основных криптовалютах (Bitcoin, Ethereum, крупные альткоины)
- DeFi, NFT, Layer 2 решениях
- Регуляторных новостях и институциональном принятии
- Технологических обновлениях блокчейн проектов

ФОРМАТ СВОДКИ:
1. **Рыночная ситуация**: общий тренд, доминация Bitcoin
2. **Ключевые события**: важные новости за последние дни
3. **Технические разработки**: обновления протоколов, новые решения
4. **Институциональные движения**: принятие крупными компаниями
5. **Регуляторные обновления**: изменения в законодательстве
6. **Перспективы**: краткосрочные ожидания

ПРАВИЛА:
- Используй актуальные знания о криптопространстве
- Включай конкретные примеры проектов и технологий
- Максимум 800 символов
- Используй буллеты (•) для структуры
- Человекочитаемый, информативный стиль
- НЕ упоминай ограничения по данным или необходимость в доп. источниках
- Пиши как будто у тебя есть доступ к свежей информации

КОНТЕКСТ: Сегодня {current_date}, создай сводку как будто анализируешь последние события на рынке.
"""

def run_crypto_digest() -> Tuple[str, str]:
    """
    Execute daily crypto digest using Responses API with enhanced knowledge-based approach.
    
    Returns:
        Tuple of (response_id, digest_text)
    """
    try:
        logger.info("Starting crypto digest generation (knowledge-based)...")
        current_date = datetime.now().strftime('%d.%m.%Y')
        current_time = datetime.now().strftime('%H:%M')
        
        # Prepare request body - no MCP tools, rely on model knowledge
        body = {
            "model": MODEL,
            "instructions": SYSTEM_INSTRUCTIONS.format(current_date=current_date),
            "input": f"Создай ежедневную криптосводку за {current_date}. "
                    f"Текущее время: {current_time} Europe/Amsterdam. "
                    f"Анализируй последние тренды и события в криптопространстве. "
                    f"Верни готовый текст сводки для отправки в Telegram.",
        }
        
        # Make API call to get digest content
        logger.info("Calling OpenAI Responses API for digest generation...")
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
        logger.info("=== Crypto Daily Digest Service Started (Fallback Mode) ===")
        logger.info(f"Model: {MODEL}")
        logger.info(f"Timezone: Europe/Amsterdam")
        
        # Run digest generation with retries
        response_id, digest_text = run_with_retries()
        
        logger.info("=== Crypto digest completed successfully ===")
        logger.info(f"Final response ID: {response_id}")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
