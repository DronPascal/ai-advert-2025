#!/usr/bin/env python3
"""
Simple daily AI insights without MCP - maximum reliability
"""
import os
import sys
import logging
import requests
from datetime import datetime
from typing import Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
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

def run_simple_insights() -> Tuple[str, str]:
    """Generate daily insights using only OpenAI knowledge - no MCP needed."""
    try:
        logger.info("Starting simple AI insights generation (no MCP)...")
        current_date = datetime.now().strftime('%d.%m.%Y')
        
        body = {
            "model": MODEL,
            "instructions": "Создай краткую ежедневную AI-сводку о технологиях. 3 пункта, максимум 250 символов, добавь 🤖 эмодзи.",
            "input": f"Создай AI insights за {current_date} о современных технологиях ИИ.",
            "max_output_tokens": 300
        }
        
        logger.info("Calling OpenAI Responses API (simple mode)...")
        response = client.responses.create(**body)
        
        response_id = response.id
        insights_text = getattr(response, "output_text", "").strip()
        
        logger.info(f"AI Response completed. ID: {response_id}")
        logger.info(f"Generated insights preview: {insights_text[:100]}...")
        
        if insights_text:
            logger.info("Sending insights to Telegram...")
            telegram_success = send_telegram_message(insights_text)
            
            if telegram_success:
                logger.info("✅ Simple AI Insights successfully sent!")
            else:
                logger.error("❌ Failed to send insights")
                raise Exception("Telegram delivery failed")
        else:
            logger.error("❌ No insights content generated")
            raise Exception("Empty insights content")
        
        return response_id, insights_text
        
    except Exception as e:
        logger.error(f"Error in run_simple_insights: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("=== Simple AI Insights Service Started (No MCP) ===")
        logger.info(f"Model: {MODEL}")
        logger.info("Mode: Knowledge-based generation only")
        
        response_id, insights_text = run_simple_insights()
        
        logger.info("=== Simple AI Insights completed successfully ===")
        logger.info(f"Final response ID: {response_id}")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
