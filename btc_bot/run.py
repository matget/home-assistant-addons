import asyncio
import requests
import csv
import os
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import matplotlib.pyplot as plt
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import re
from telegram.ext import ConversationHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup

reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[["/btc", "/csv"], ["/update", "/gptnews"], ["/history", "/help"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

CSV_WAITING = 1

import json
with open('/data/options.json', 'r') as f:
    options = json.load(f)

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


def generate_history_plot():
    file_path = "/data/impact_inputs.csv"
    dates, prices, scores = [], [], []

    try:
        with open(file_path, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dates.append(row["Date"])
                try:
                    prices.append(float(row["Price"].replace(',', '').strip()))
                except:
                    prices.append(0)
                scores.append(float(row["Score"].strip()))
    except FileNotFoundError:
        return

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
        # קריאת השורה האחרונה מקובץ impact_inputs.csv
        with open("/data/impact_inputs.csv", newline='', encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
            if not rows:
                await bot.send_message(chat_id=chat_id, text="⚠️ אין נתונים בקובץ impact_inputs.csv")
                return
            last = rows[-1]
    except FileNotFoundError:
        await bot.send_message(chat_id=chat_id, text="⚠️ הקובץ impact_inputs.csv לא נמצא.")
        return
    # חילוץ נתונים
    now = last["Date"]
    price = float(last["Price"])
    score = float(last["Score"])
    categories = {k: float(last[k]) for k in [
        "supply_demand", "regulation", "macro_economy",
        "news_sentiment", "whales_activity", "tech_events", "adoption"
    ]}
    # ניסוח הודעה
    message = f"*עדכון ביטקוין יומי* - {now}\n\n"
    message += f"*מחיר נוכחי:* ${price:,.0f}\n"
    message += f"*ציון השפעה משוקלל:* {score}/10\n\n"
    for k, v in categories.items():
        hebrew = hebrew_labels.get(k, k)
        message += f"- {hebrew}: {v}/10\n"
    summary = interpret_score(score)
    message += f"\n\n*סיכום:* {summary}"
    generate_history_plot()
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
    with open("btc_update.png", "rb") as f:
        await bot.send_photo(chat_id=chat_id, photo=f)

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

# ----------- gptnews -----------
async def handle_gptnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = "אשמח שתיתן לי כמה כותרות עדכניות בנוגע לחדשות ביטקוין ותחזית לשער הביטקוין לשבוע הקרוב."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 פתח את ChatGPT", url="https://chat.openai.com/")]
    ])
    message = f"{prompt}"
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)

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

    scores = {key: float(value) for key, value in matches}
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

    file_path = "/data/impact_inputs.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    await update.message.reply_text("✅ Data saved successfully!")
    return ConversationHandler.END

csv_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("csv", start_csv)],
    states={CSV_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_csv_data)]},
    fallbacks=[],
)

# ----------- history -----------
async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = "/data/impact_inputs.csv"
    if not os.path.isfile(file_path):
        await update.message.reply_text("⚠️ No data found.")
        return
    try:
        with open(file_path, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if not rows:
                await update.message.reply_text("⚠️ File is empty.")
                return
            text = "📊 Historical Impact Scores:\n\n"
            for row in rows[-5:]:
                text += f"{row['Date']}\n"
                text += f"Price: ${row['Price']}, Score: {row['Score']}/10\n"
                text += f" - supply_demand: {row['supply_demand']}\n"
                text += f" - regulation: {row['regulation']}\n"
                text += f" - macro_economy: {row['macro_economy']}\n"
                text += f" - news_sentiment: {row['news_sentiment']}\n"
                text += f" - whales_activity: {row['whales_activity']}\n"
                text += f" - tech_events: {row['tech_events']}\n"
                text += f" - adoption: {row['adoption']}\n\n"
            await update.message.reply_text(text[:4090])  # נחתוך אם חורג ממגבלה
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ----------- start -----------

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Use the buttons below or type a command.",
        reply_markup=reply_keyboard
    )

# ----------- reminder -----------
async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text="🕘 Reminder:\nDon’t forget to update today’s Bitcoin data using /update → GPT → /csv"
    )

# ----------- help -----------
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Bitcoin GPT Bot – Commands Overview*\n\n"
        "Available commands:\n"
        "/btc – Send a daily update with current BTC price, weighted impact score, and chart.\n"
        "/update – Get a ready-to-copy GPT prompt to analyze Bitcoin's current global state.\n"
        "/csv – Paste GPT output in the correct format to update the impact data CSV file.\n"
        "/gptnews – Open ChatGPT with a prompt to get headlines and a Bitcoin forecast.\n"
        "/history – present the full table with all the historic values.\n"
        "/help – Show this help message.\n\n"
        "📊 All analysis is based on data saved in 'impact_inputs.csv'.\n"
        "You should do the following on daily basis: /update → copy to GPT → copy from GPT → /csv → paste → /btc\n\n"
        "Good luck and enjoy the data! 🚀"
    )

    await update.message.reply_text(help_text, reply_markup=reply_keyboard)
# ----------------------------------------------------------------------------------------

def start_bot_listener():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("btc", handle_btc_command))
    app.add_handler(CommandHandler("gptnews", handle_gptnews))
    app.add_handler(CommandHandler("update", handle_update_prompt))
    app.add_handler(csv_conv_handler)
    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(CommandHandler("history", handle_history))
    print("📡 Bot is listening...")
    app.run_polling()

if __name__ == "__main__":
    import sys
    import asyncio
    if len(sys.argv) > 1 and sys.argv[1] == "listen":
        start_bot_listener()
    elif len(sys.argv) > 1 and sys.argv[1] == "remind":
        asyncio.run(send_daily_reminder(context=type("obj", (), {"bot": bot})))
    else:
        asyncio.run(send_update_to(CHAT_ID))
