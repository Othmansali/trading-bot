import os
import logging
import requests
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# Setup logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

# Config from environment variables

TELEGRAM_TOKEN = os.environ[“TELEGRAM_BOT_TOKEN”]
CHAT_ID = os.environ[“TELEGRAM_CHAT_ID”]
ANTHROPIC_KEY = os.environ[“ANTHROPIC_API_KEY”]

STOCKS = [“BULL”, “SOFI”, “UPST”]

# Get stock price

def get_price(symbol):
try:
url = f”https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d”
r = requests.get(url, headers={“User-Agent”: “Mozilla/5.0”}, timeout=15)
data = r.json()[“chart”][“result”][0]
meta = data[“meta”]
price = meta[“regularMarketPrice”]
prev = meta[“previousClose”]
high52 = meta.get(“fiftyTwoWeekHigh”, 0)
low52 = meta.get(“fiftyTwoWeekLow”, 0)
change = ((price - prev) / prev) * 100
closes = [c for c in data[“indicators”][“quote”][0].get(“close”, []) if c]
rsi = calc_rsi(closes)
return {“symbol”: symbol, “price”: price, “change”: change,
“high52”: high52, “low52”: low52, “rsi”: rsi}
except Exception as e:
logger.error(f”Price error {symbol}: {e}”)
return None

# Calculate RSI

def calc_rsi(closes, period=14):
if len(closes) < period + 1:
return 50
deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
gains = sum(d for d in deltas[-period:] if d > 0) / period
losses = sum(-d for d in deltas[-period:] if d < 0) / period or 0.001
return round(100 - (100 / (1 + gains/losses)), 1)

# AI Analysis

def analyze(stocks_data):
summary = “”
for s in stocks_data:
if s:
summary += f”{s[‘symbol’]}: price=${s[‘price’]:.2f}, change={s[‘change’]:+.1f}%, RSI={s[‘rsi’]}, 52w_high=${s[‘high52’]:.2f}, 52w_low=${s[‘low52’]:.2f}\n”

```
prompt = f"""You are an expert stock trader. Analyze these stocks and give clear Arabic recommendations.
```

Data:
{summary}

Context:

- BULL (Webull): fintech platform, 26M users, revenue $571M +46% YoY, near all-time low $4.79
- SOFI: neobank, GAAP profitable, 13M members, short seller pressure, earnings May 4
- UPST: AI lending, revenue +65% YoY, applying for bank charter

For each stock provide in Arabic:

1. القرار: اشتري / بيع / انتظر
1. للـ Options: Call أو Put مع Strike و Expiry (2 أسابيع - شهر)
1. السبب (جملتين)
1. الهدف و Stop Loss

Keep it concise and actionable.”””

```
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
msg = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1000,
    messages=[{"role": "user", "content": prompt}]
)
return msg.content[0].text
```

# Send Telegram message

async def send_msg(text, bot):
chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
for chunk in chunks:
await bot.send_message(chat_id=CHAT_ID, text=chunk)

# Daily report

async def daily_report(context):
logger.info(“Running daily report…”)
stocks_data = [get_price(s) for s in STOCKS]
analysis = analyze(stocks_data)
now = datetime.now().strftime(”%Y-%m-%d %H:%M”)
msg = f”🤖 AI Trading Report\n📅 {now}\n\n{analysis}\n\n⚠️ هذا تحليل AI للمساعدة فقط”
await send_msg(msg, context.bot)

# Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“🤖 AI Trading Bot\n\nالأوامر:\n/analyze - تحليل AI الآن\n/prices - الأسعار الحالية\n/help - المساعدة”
)

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = “📊 الأسعار الحالية:\n\n”
for symbol in STOCKS:
data = get_price(symbol)
if data:
emoji = “📈” if data[‘change’] > 0 else “📉”
msg += f”{emoji} {symbol}: ${data[‘price’]:.2f} ({data[‘change’]:+.1f}%) RSI:{data[‘rsi’]}\n”
await update.message.reply_text(msg)

async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“⏳ جاري التحليل…”)
stocks_data = [get_price(s) for s in STOCKS]
analysis = analyze(stocks_data)
await send_msg(f”🤖 تحليل AI:\n\n{analysis}”, context.bot)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“📚 الأوامر:\n/prices - الأسعار\n/analyze - تحليل AI كامل\n/start - البداية”
)

# Main

def main():
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler(“start”, start))
app.add_handler(CommandHandler(“prices”, prices))
app.add_handler(CommandHandler(“analyze”, analyze_cmd))
app.add_handler(CommandHandler(“help”, help_cmd))

```
scheduler = AsyncIOScheduler()
# Daily at 9:30 AM UTC (market open)
scheduler.add_job(daily_report, "cron", hour=9, minute=30, args=[app])
# Daily at 4:05 PM UTC (market close)
scheduler.add_job(daily_report, "cron", hour=16, minute=5, args=[app])
scheduler.start()

logger.info("Bot started!")
app.run_polling()
```

if **name** == “**main**”:
main()
