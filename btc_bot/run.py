import json
from telegram import Bot

with open('/data/options.json', 'r') as f:
    options = json.load(f)

TOKEN = options.get("TOKEN")
CHAT_ID = options.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Missing TOKEN or CHAT_ID in options.json")

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text="... Bitcoin bot is now running!")
