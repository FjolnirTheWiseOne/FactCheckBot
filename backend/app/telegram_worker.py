import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def start(update, context):
    update.message.reply_text("Welcome! Send me a news URL and I will check it.")

def check(update, context):
    if not context.args:
        update.message.reply_text("Please send a URL after the command, e.g. /check <url>")
        return
    url = context.args[0]
    try:
        resp = requests.post(f"{API_URL}/check", json={"url": url})
        data = resp.json()
        reply = f"Title: {data['title']}\nTrust Score: {data['trust_score']}\nVerdict: {data['verdict']}"
    except Exception as e:
        reply = f"Error checking article: {e}"
    update.message.reply_text(reply)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check", check))
    updater.start_polling()
    print("Bot started. Listening for messages...")
    updater.idle()

if __name__ == "__main__":
    main()
