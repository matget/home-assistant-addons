import asyncio
import csv
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
import requests
import schedule
import gspread
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from telegram import (
    Bot,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[["/btc", "/csv"], ["/update", "/gptnews"], ["/history", "/help"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Load Home Assistant config options
with open('/data/options.json') as f:
    options = json.load(f)
    
# Save the service account JSON to a local file
json_keys = options.get("JSON_KEYS")
if not json_keys:
    raise ValueError("Missing JSON_KEYS in configuration.")

with open("/app/btc-bot-keys.json", "w") as f:
    f.write(json_keys)

GSHEET_URL = options.get("GSHEET_URL")
GSHEET_CREDENTIALS = "/app/btc-bot-keys.json"
CSV_WAITING = 1

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDENTIALS, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(GSHEET_URL).sheet1

def get_all_rows():
    return sheet.get_all_records()

def append_row_to_sheet(row_dict):
    row = [row_dict["Date"], row_dict["Price"], row_dict["Score"]]
    row.extend([row_dict[k] for k in [
        "supply_demand", "regulation", "macro_economy", 
        "news_sentiment", "whales_activity", "tech_events", "adoption"
    ]])
    sheet.append_row(row)

TOKEN = options.get("TOKEN")
CHAT_ID = options.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Missing TOKEN or CHAT_ID in options.json")

bot = Bot(token=TOKEN)

hebrew_labels = {
    "supply_demand": "ביקוש/היצע",
    "regulation": "רגולציה",
    "macro_economy": "מצב כלכלה עולמית",
    "news_sentiment": "חדשות/פסיכולוגיה",
    "whales_activity": "פעילות לוויתנים",
    "tech_events": "אירועים טכנולוגיים",
    "adoption": "שימוש/אימוץ עולמי"
}

def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url).json()
    return response['bitcoin']['usd']

def interpret_score(score):
    if score >= 8:
        return "📈 התחזית חיובית מאוד – השוק מראה סימני עלייה חזקים."
    elif score >= 6.5:
        return "🙂 מגמה חיובית מתונה – שוק יציב עם נטייה לעלייה."
    elif score >= 5:
        return "😐 המצב נייטרלי – אין מגמה ברורה, יש לעקוב."
    elif score >= 3.5:
        return "⚠️ מגמה שלילית – יש סימנים ללחץ בשוק."
    else:
        return "🔻 תחזית שלילית מאוד – סיכון מוגבר ונטייה לירידות."


def get_all_rows():
    return sheet.get_all_records()

def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["bitcoin"]["usd"]
    
def generate_history_plot():
    dates, prices, scores = [], [], []
    try:
        rows = get_all_rows()  # קריאה מהגיליון
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        return
    for row in rows:
        dates.append(row["Date"])
        try:
            prices.append(float(str(row["Price"]).replace(',', '').strip()))
        except:
            prices.append(0)
        try:
            scores.append(float(row["Score"]))
        except:
            scores.append(0)
    if not prices or not scores:
        return

    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price (USD)', color='tab:blue')
    ax1.plot(dates, prices, color='tab:blue', marker='o')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    if price_range == 0:
        ax1.set_ylim(min_price - 1, max_price + 1)
    else:
        ax1.set_ylim(min_price - price_range * 0.1, max_price + price_range * 0.1)
    plt.xticks(rotation=45)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Impact Score', color='tab:green')
    ax2.plot(dates, scores, color='tab:green', marker='x')
    ax2.tick_params(axis='y', labelcolor='tab:green')
    fig.tight_layout()
    plt.title("BTC Price & Impact Score History")
    plt.savefig("btc_update.png", bbox_inches='tight')
    plt.close()

# ----------- btc -----------
async def handle_btc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 מעדכן נתוני ביטקוין...")
    await send_update_to(update.effective_chat.id)
async def send_update_to(chat_id):
    try:
        rows = get_all_rows()  # קריאה מהגיליון במקום CSV
        if not rows:
            await bot.send_message(chat_id=chat_id, text="⚠️ אין נתונים בגיליון Google Sheets.")
            return
        last = rows[-1]  # השורה האחרונה
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"⚠️ שגיאה בגישה ל-Google Sheets: {e}")
        return
    # חילוץ נתונים
    now = last.get("Date", "לא ידוע")
    try:
        price = float(str(last["Price"]).replace(',', '').strip())
    except:
        price = 0
    try:
        score = float(str(last["Score"]).strip())
    except:
        score = 0
    categories = {}
    for k in [
        "supply_demand", "regulation", "macro_economy",
        "news_sentiment", "whales_activity", "tech_events", "adoption"
    ]:
        try:
            categories[k] = float(str(last.get(k, 0)).strip())
        except:
            categories[k] = 0
    # ניסוח הודעה
    message = f"*עדכון ביטקוין יומי* - {now}\n\n"
    message += f"*מחיר נוכחי:* ${price:,.0f}\n"
    message += f"*ציון השפעה משוקלל:* {score}/10\n\n"
    for k, v in categories.items():
        hebrew = hebrew_labels.get(k, k)
        message += f"- {hebrew}: {v}/10\n"
    summary = interpret_score(score)
    message += f"\n\n*סיכום:* {summary}"
    # גרף היסטוריה
    generate_history_plot()
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
    try:
        with open("btc_update.png", "rb") as f:
            await bot.send_photo(chat_id=chat_id, photo=f)
    except FileNotFoundError:
        await bot.send_message(chat_id=chat_id, text="⚠️ לא ניתן להציג גרף (btc_update.png לא נמצא)")

# ----------- update -----------
async def handle_update_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = (
        "Please analyze the current global situation of Bitcoin and rate the following 7 categories on a scale of 1 to 10,\n"
        "based on their current influence on the Bitcoin price **today**:\n\n"
        "Categories:\n"
        "- supply_demand (supply, demand, trading volume, exchange inflows)\n"
        "- regulation (new regulations, government or institutional policy changes)\n"
        "- macro_economy (interest rates, inflation, Fed decisions, economic news)\n"
        "- news_sentiment (media/public mood, Twitter trends, Google Trends)\n"
        "- whales_activity (large BTC wallet movements)\n"
        "- tech_events (Bitcoin Core upgrades, protocol changes)\n"
        "- adoption (corporate/governmental adoption, new integrations)\n\n"
        "please learn the weights of each category: supply_demand: 0.25, regulation: 0.20, macro_economy: 0.20, news_sentiment: 0.10, whales_activity: 0.10, tech_events: 0.075, adoption: 0.075\n"
        "after that, please make text box (for east to copy) as following pattern nad replace the <score> with the values you calculated:\n\n"
        "supply_demand: <score>\n"
        "regulation: <score>\n"
        "macro_economy: <score>\n"
        "news_sentiment: <score>\n"
        "whales_activity: <score>\n"
        "tech_events: <score>\n"
        "adoption: <score>\n"
        "score_weighted: <final_score>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 פתח את ChatGPT", url="https://chat.openai.com/")]
    ])
    await update.message.reply_text(
        text=f"{prompt}",
        reply_markup=keyboard
    )

# ----------- csv -----------
async def start_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Please paste the GPT output in the expected format (category scores + score_weighted):")
    return CSV_WAITING
async def receive_csv_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    pattern = r"(supply_demand|regulation|macro_economy|news_sentiment|whales_activity|tech_events|adoption|score_weighted):\s*([\d.]+)"
    matches = re.findall(pattern, text)
    if len(matches) < 8:
        await update.message.reply_text("❌ Missing fields. Please make sure all 7 categories and score_weighted are included.")
        return ConversationHandler.END
    try:
        scores = {key: float(value) for key, value in matches}
    except ValueError:
        await update.message.reply_text("⚠️ All values must be numeric.")
        return ConversationHandler.END
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    price = get_btc_price()
    row = {
        "Date": now,
        "Price": price,
        "Score": scores["score_weighted"],
        "supply_demand": scores["supply_demand"],
        "regulation": scores["regulation"],
        "macro_economy": scores["macro_economy"],
        "news_sentiment": scores["news_sentiment"],
        "whales_activity": scores["whales_activity"],
        "tech_events": scores["tech_events"],
        "adoption": scores["adoption"]
    }
    try:
        append_row_to_sheet(row)  # כתיבה לגוגל שיטס במקום לקובץ
        await update.message.reply_text("✅ הנתונים נרשמו בהצלחה בגיליון!")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בשמירה ל-Google Sheets:\n{e}")
    return ConversationHandler.END
csv_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("csv", start_csv)],
    states={CSV_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_csv_data)]},
    fallbacks=[],
)

# ----------- history -----------
async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = get_all_rows()
        if not rows:
            await update.message.reply_text("⚠️ No data found in Google Sheets.")
            return
        text = "📊 *Historical Impact Scores:*\n\n"
        for row in rows[-5:]:  # 5 השורות האחרונות
            text += f"{row['Date']}\n"
            text += f"Price: ${row['Price']}, Score: {row['Score']}/10\n"
            text += f" - supply_demand: {row['supply_demand']}\n"
            text += f" - regulation: {row['regulation']}\n"
            text += f" - macro_economy: {row['macro_economy']}\n"
            text += f" - news_sentiment: {row['news_sentiment']}\n"
            text += f" - whales_activity: {row['whales_activity']}\n"
            text += f" - tech_events: {row['tech_events']}\n"
            text += f" - adoption: {row['adoption']}\n\n"
        await update.message.reply_text(text[:4090], parse_mode=None)
    except Exception as e:
        await update.message.reply_text(f"❌ Error accessing Google Sheets: {e}")


# ----------- start -----------
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Use the buttons below or type a command.",
        reply_markup=reply_keyboard
    )

# ----------- reminder -----------
async def push_reminder(chat_id):
    try:
        print("🟢 [push_reminder] Started")
        await bot.send_message(chat_id=chat_id, text="🕘 Reminder:\nDon’t forget to update today’s Bitcoin data using /update → GPT → /csv")
        print("✅ [push_reminder] Sent")
    except Exception as e:
        print(f"❌ [push_reminder] ERROR: {e}")

# ----------- Push News -----------
async def push_news(chat_id):
    try:
        print("🟢 [push_news] Started")
        price = get_btc_price()
        await bot.send_message(chat_id=chat_id, text=f"🤑 Current BTC Value: {price}")
        print("✅ [push_news] Sent")
    except Exception as e:
        print(f"❌ [push_news] ERROR: {e}")
    
# ----------- scheduler -----------
def scheduler_thread():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def send_news():
            print("📤 Sending scheduled BTC update")
            loop.call_soon_threadsafe(asyncio.create_task, push_news(CHAT_ID))

        def send_reminder():
            print("🔔 Sending daily reminder")
            loop.call_soon_threadsafe(asyncio.create_task, push_reminder(CHAT_ID))

        schedule.every(1).minutes.do(send_news)
        schedule.every(1).day.at("10:00").do(send_reminder)

        print("📅 Scheduler started: reminder at 10:00, news every 2h")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print(f"❌ Scheduler thread crashed: {e}")

        
# ----------- help -----------
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Bitcoin GPT Bot – Commands Overview*\n\n"
        "Available commands:\n"
        "/btc – BTC Status.\n"
        "/update – Get GPT prompt for scores.\n"
        "/csv – Update CSV file.\n"
        "/gptnews – GPT prompt for BTC news\n"
        "/history – Present full csv.\n"
        "/help – Show this help message.\n\n"
        "You should do the following on daily basis:\n"
        "/update → copy to GPT → copy from GPT → /csv → paste\n\n"
        "Good luck and enjoy the data! 🚀"
    )
    await update.message.reply_text(help_text, reply_markup=reply_keyboard)
    
# ----------------------------------------------------------------------------------------  
def start_bot_listener():
    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        print(f"{now}: 🟢 Starting Telegram bot listener...")
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", handle_start))
        app.add_handler(CommandHandler("btc", handle_btc_command))
        app.add_handler(CommandHandler("update", handle_update_prompt))
        app.add_handler(CommandHandler("help", handle_help_command))
        app.add_handler(CommandHandler("history", handle_history))
        app.add_handler(csv_conv_handler)
        print(f"{now}: 📡 Bot is listening...")
        app.run_polling()
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
# ----------------------------------------------------------------------------------------  

if __name__ == "__main__":
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"{now}: Main On")
    threading.Thread(target=scheduler_thread, daemon=True).start()
    start_bot_listener()
