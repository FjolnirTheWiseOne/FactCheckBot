import os
import requests
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    
    filters
)

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    await update.message.reply_text(
        "Welcome! I can help fact-check news articles.\n\n"
        "Simply send me a URL or use /check <url> command."
    )

async def check_url(url: str) -> str:
    """Call the FastAPI backend to analyze the article."""
    try:
        resp = requests.post(f"{API_URL}/check", json={"url": url})
        resp.raise_for_status()  # Raise exception for non-200 status codes
        data = resp.json()
        return (
            f"📰 Title: {data.get('title')}\n"
            f"🎯 Trust Score: {data.get('trust_score')}%\n"
            f"✍️ Verdict: {data.get('verdict')}"
        )
    except Exception as e:
        return f"❌ Error checking article: {str(e)}"

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /check command."""
    if not context.args:
        await update.message.reply_text(
            "Please send a URL after the command, e.g. /check <url>"
        )
        return
    
    url = context.args[0]
    if not URL_PATTERN.match(url):
        await update.message.reply_text("Please provide a valid URL starting with http:// or https://")
        return

    await update.message.reply_text("🔍 Analyzing article...")
    result = await check_url(url)
    await update.message.reply_text(result)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URLs sent directly to the bot."""
    text = update.message.text
    urls = URL_PATTERN.findall(text)
    
    if not urls:
        await update.message.reply_text(
            "I couldn't find a URL in your message. "
            "Please send me a news article URL or use /check <url>"
        )
        return
    
    await update.message.reply_text("🔍 Analyzing article...")
    result = await check_url(urls[0])  # Analyze first URL found
    await update.message.reply_text(result)

import asyncio

def run_bot():
    """Run the bot with proper error handling."""
    app = None
    try:
        # Create application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("check", check_command))
        
        # Message handler for direct URLs
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))
        
        print("Starting bot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        if app:
            print("Shutting down...")
            app.stop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        if app:
            print("Emergency shutdown...")
            app.stop()
        exit(1)

if __name__ == "__main__":
    # Token validation
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment or .env file")
        exit(1)
    elif TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN_HERE":
        print("Error: Please replace the placeholder with your actual Telegram bot token in .env")
        exit(1)
    
    run_bot()
