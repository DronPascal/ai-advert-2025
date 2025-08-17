"""
Crypto Daily Digest Service
Uses OpenAI Responses API with remote MCP servers to gather crypto data and send Telegram updates via direct API.
"""

import os
import json
import time
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

# Remote MCP endpoints (HTTPS accessible from OpenAI cloud)
MCP_WEB3_URL = os.environ["MCP_WEB3_URL"]           # e.g. https://your-web3-mcp-server.com
MCP_WHITEPAPER_URL = os.environ["MCP_WHITEPAPER_URL"] # e.g. https://your-whitepapers-mcp-server.com

# Direct Telegram API integration
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_USER_ID = os.environ["TELEGRAM_USER_ID"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Remote MCP tools configuration (only for data gathering)
tools = [
    {
        "type": "mcp",
        "server_label": "web3research",
        "server_url": MCP_WEB3_URL,
        "allowed_tools": [
            "search", 
            "fetch-content", 
            "token-research", 
            "generate-report",
            "market-analysis"
        ],
        "require_approval": "never"
    },
    {
        "type": "mcp",
        "server_label": "whitepapers",
        "server_url": MCP_WHITEPAPER_URL,
        "allowed_tools": [
            "search_whitepapers", 
            "load_whitepaper", 
            "query_knowledge_base", 
            "list_projects"
        ],
        "require_approval": "never"
    }
]

# Direct Telegram API function
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

# System instructions
SYSTEM_INSTRUCTIONS = """
Ты — крипто-аналитик, который создает ежедневные сводки по криптовалютному рынку.

ЗАДАЧА:
1) Получи свежие данные из web3research (рыночные метрики, новости, сентимент, анализ токенов)
2) При необходимости подтверди ключевые положения выдержками из whitepapers (используй whitepapers MCP для поиска релевантной информации)
3) Сформируй краткую сводку: 5–7 пунктов, максимально конкретно, без воды
4) Верни ТОЛЬКО текст сводки - приложение само отправит его в Telegram

ПРАВИЛА:
- Не делай долгих списков, не повторяйся
- Не используй markdown-таблицы, только буллеты (•)
- Фокусируйся на ключевых движениях рынка, важных событиях и трендах
- Включай конкретные цифры и проценты когда доступно
- Не вставляй сырые JSON/URL в финальное сообщение
- Финальное сообщение должно быть человекочитаемым и информативным
- Максимум 800 символов в итоговом сообщении
- НЕ упоминай про отправку в Telegram - просто верни готовый текст

ИСТОЧНИКИ ДАННЫХ:
- web3research: рыночные данные, цены, объемы, новости
- whitepapers: техническая информация о проектах, токеномика

ФОРМАТ ОТВЕТА: Просто готовый текст сводки, без дополнительных комментариев.

Начинай работу немедленно.
"""


def run_crypto_digest(previous_response_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Execute daily crypto digest using Responses API with remote MCP and send via Telegram.
    
    Args:
        previous_response_id: Previous response ID to cache tools list
        
    Returns:
        Tuple of (response_id, digest_text)
    """
    try:
        logger.info("Starting crypto digest generation...")
        
        # Prepare request body
        body = {
            "model": MODEL,
            "tools": tools,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": f"Создай ежедневную криптосводку за {datetime.now().strftime('%d.%m.%Y')}. "
                    f"Текущее время: {datetime.now().strftime('%H:%M')} Europe/Amsterdam. "
                    f"Верни готовый текст сводки для отправки в Telegram.",
        }
        
        # Add previous response ID for tools caching if available
        if previous_response_id:
            body["previous_response_id"] = previous_response_id
            logger.info(f"Using cached tools from previous response: {previous_response_id}")
        
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


def run_with_retries(max_retries: int = 3, previous_response_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Run crypto digest with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        previous_response_id: Previous response ID for caching
        
    Returns:
        Tuple of (response_id, output_text)
    """
    for attempt in range(max_retries + 1):
        try:
            return run_crypto_digest(previous_response_id)
            
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(e)}")
                raise
            
            # Calculate exponential backoff delay
            delay = min(60, 2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)


def load_last_response_id() -> Optional[str]:
    """Load the last response ID from file for caching."""
    try:
        with open('/tmp/last_response_id.txt', 'r') as f:
            response_id = f.read().strip()
            logger.info(f"Loaded previous response ID: {response_id}")
            return response_id
    except FileNotFoundError:
        logger.info("No previous response ID found")
        return None
    except Exception as e:
        logger.warning(f"Error loading previous response ID: {str(e)}")
        return None


def save_last_response_id(response_id: str) -> None:
    """Save the response ID to file for future caching."""
    try:
        with open('/tmp/last_response_id.txt', 'w') as f:
            f.write(response_id)
        logger.info(f"Saved response ID: {response_id}")
    except Exception as e:
        logger.warning(f"Error saving response ID: {str(e)}")


def main():
    """Main entry point for the crypto digest service."""
    logger.info("=== Crypto Daily Digest Service Started ===")
    logger.info(f"Model: {MODEL}")
    logger.info(f"Timezone: {os.getenv('TZ', 'UTC')}")
    
    try:
        # Load previous response ID for caching
        previous_response_id = load_last_response_id()
        
        # Run crypto digest with retries
        response_id, output_text = run_with_retries(
            max_retries=3, 
            previous_response_id=previous_response_id
        )
        
        # Save new response ID for future caching
        save_last_response_id(response_id)
        
        logger.info("=== Crypto Daily Digest Completed Successfully ===")
        logger.info(f"Final response ID: {response_id}")
        
        if output_text:
            logger.info(f"Output text length: {len(output_text)} characters")
        else:
            logger.info("No output text (likely sent directly via Telegram MCP)")
            
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()

