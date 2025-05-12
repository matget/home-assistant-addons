import os
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Missing TOKEN or CHAT_ID environment variable")

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text="✅ Bitcoin bot is now running!")
