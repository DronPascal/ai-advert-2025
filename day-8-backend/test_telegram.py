#!/usr/bin/env python3
"""
Test Telegram message sending
"""
import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_message():
    """Test sending a message to Telegram."""
    
    # Check environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    user_id = os.getenv("TELEGRAM_USER_ID", "7789201703")
    
    if not bot_token or bot_token == "demo_token":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set or in demo mode")
        logger.info("ℹ️ Set environment variable: export TELEGRAM_BOT_TOKEN=your_real_bot_token")
        return False
    
    logger.info(f"🤖 Testing Telegram bot: {bot_token[:10]}...")
    logger.info(f"👤 Sending to user ID: {user_id}")
    
    # Test message
    test_message = """
🧪 <b>Тест Telegram Бота</b>

✅ Ваш бот работает правильно!
📅 Время: сейчас
🤖 Сообщение от AI Insights Daily Service

<i>Это тестовое сообщение для проверки работы бота.</i>
"""
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": user_id,
            "text": test_message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        logger.info("📤 Sending test message...")
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            message_id = result.get("result", {}).get("message_id")
            logger.info(f"✅ Test message sent successfully!")
            logger.info(f"📨 Message ID: {message_id}")
            logger.info("📱 Check your Telegram app for the test message")
            return True
        else:
            logger.error(f"❌ Telegram API error: {result}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Failed to send message: {str(e)}")
        if "401" in str(e):
            logger.error("🔑 Invalid bot token. Check your TELEGRAM_BOT_TOKEN")
        elif "403" in str(e):
            logger.error("🚫 Bot was blocked by user or can't send messages")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

def get_bot_info():
    """Get information about the bot."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token or bot_token == "demo_token":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            bot_info = result.get("result", {})
            logger.info("🤖 Bot information:")
            logger.info(f"  Name: {bot_info.get('first_name')}")
            logger.info(f"  Username: @{bot_info.get('username')}")
            logger.info(f"  ID: {bot_info.get('id')}")
            logger.info(f"  Can read all group messages: {bot_info.get('can_read_all_group_messages')}")
            return True
        else:
            logger.error(f"❌ API error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to get bot info: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Telegram Bot Test")
    logger.info("=" * 50)
    
    # Get bot info first
    if get_bot_info():
        logger.info("")
        # Test message sending
        if test_telegram_message():
            logger.info("✅ All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Message test failed")
            sys.exit(1)
    else:
        logger.error("❌ Bot info test failed")
        sys.exit(1)
