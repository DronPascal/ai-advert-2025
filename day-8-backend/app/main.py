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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    """Send message directly to Telegram user via Bot API."""
    try:
        # Check if we're in demo mode
        if TELEGRAM_BOT_TOKEN == "demo_token":
            logger.info("="*60)
            logger.info("📱 TELEGRAM MESSAGE (DEMO MODE):")
            logger.info("="*60)
            logger.info(f"TO: User {TELEGRAM_USER_ID}")
            logger.info(f"MESSAGE:\n{message}")
            logger.info("="*60)
            logger.info("ℹ️ Set real TELEGRAM_BOT_TOKEN to send actual messages")
            return True
        
        # Real Telegram API call
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
            logger.info(f"✅ Message sent successfully to Telegram user {TELEGRAM_USER_ID}")
            return True
        else:
            logger.error(f"❌ Telegram API error: {result}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Failed to send Telegram message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending Telegram message: {str(e)}")
        return False

# Remote MCP Tools Configuration - LIMITED for context efficiency
tools = [
    {
        "type": "mcp",
        "server_url": MCP_TIKTOKEN_URL,
        "server_label": "tiktoken",
        "allowed_tools": [
            "search_tiktoken_documentation"  # Only search, not full fetch
        ],
        "require_approval": "never"
    }
]

# System instructions - COMPACT for context efficiency
SYSTEM_INSTRUCTIONS = """
Создай краткую AI сводку на основе tiktoken. 

1. Найди 1 факт о токенизации через search_tiktoken_documentation
2. Сформулируй в 3 пункта:
• Что такое tiktoken (кратко)
• Интересный факт о BPE
• Практический совет

Максимум 300 символов. Русский язык. Добавь 🤖 эмодзи.
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
            "tools": tools,
            "instructions": SYSTEM_INSTRUCTIONS,
            "input": f"Создай AI сводку за {current_date}. Используй search_tiktoken_documentation для поиска фактов.",
            "max_output_tokens": 500  # Limit output to save context
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
