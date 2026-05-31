import requests
import os
import pytz
import xml.etree.ElementTree as ET
from datetime import datetime

# ============================================
# SETTINGS
# ============================================
BOT_TOKEN = "8874026729:AAEgzZr0UslgaKGdPiUjZMONNuFCKL-pqsY"
CHAT_ID   = "1358803794"
SYMBOL    = "BTC-USD"
MOVE      = 50

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

def is_morning_report_time():
    n = now_ist()
    # સવારે ૯:૦૦ થી ૯:૧૫ ની વચ્ચે રન થાય ત્યારે ટ્રુ (True) થશે
    mins = n.hour * 60 + n.minute
    return 540 <= mins < 555

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print("Telegram Response:", r.json().get("ok"))
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_crypto_news():
    query = "Bitcoin"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        news_items = []
        for item in root.findall(".//item")[:2]: # ટોપ ૨ ક્રિપ્ટો ન્યૂઝ હેડલાઇન્સ
            title = item.find("title").text
            link = item.find("link").text
            clean_title = title.split(" - ")[0]
            source = title.split(" - ")[-1] if " - " in title else "Crypto News"
            news_items.append(f"• 📰 <b>{clean_title}</b> ({source})\n  🔗 <a href='{link}'>વાંચવા માટે અહીં ક્લિક કરો</a>")
        
        if news_items:
            return "\n\n📢 <b>LATEST CRYPTO NEWS:</b>\n" + "\n".join(news_items)
        return "\n\n📢 <b>LATEST CRYPTO NEWS:</b>\n• હાલમાં કોઈ ફ્રેશ ક્રિપ્ટો ન્યૂઝ મળ્યા નથી."
    except Exception as e:
        print(f"News fetch error: {e}")
        return ""

def fetch_data():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=5m&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes  = [x for x in res["indicators"]["quote"][0]["close"]  if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price   = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        return round(price, 2), closes, volumes, round(prev_close, 2)
    except Exception as e:
        print(f"Fetch error: {e}"); return None, [], [], None

def calc_ema(data, p):
    if len(data) < p: return None
    k = 2/(p+1); e = sum(data[:p])/p
    for v in data[p:]: e = v*k + e*(1-k)
    return round(e, 2)

def calc_rsi(data, p=14):
    if len(data) < p+1: return None
    g = sum(max(data[i]-data[i-1],0) for i in range(len(data)-p,len(data)))
    l = sum(max(data[i-1]-data[i],0) for i in range(len(data)-p,len(data)))
    ag, al = g/p, l/p
    return round(100 - 100/(1+ag/al), 1) if al else 100.0

price, closes, volumes, prev_close = fetch_data()
if not price or len(closes) < 22:
    print("Not enough data."); exit(0)

ema9  = calc_ema(closes, 9)
ema21 = calc_ema(closes, 21)
rsi   = calc_rsi(closes, 14)

avg_vol = sum(volumes[-6:-1])/5 if len(volumes)>=6 else 0
vol_x = round(volumes[-1]/avg_vol, 1) if avg_vol else 0

news_details = fetch_crypto_news()

# ---------------------------------------------------------
# 🔥 ૧. રોજ સવારે ૯:૦૫ વાગ્યે મોર્નિંગ પ્રિડિક્શન રિપોર્ટ મોકલવો
# ---------------------------------------------------------
if is_morning_report_time():
    change24h = round(price - prev_close, 2)
    p_change24h = round((change24h / prev_close) * 100, 2)
    
    trend_emoji = "📈" if change24h >= 0 else "📉"
    
    # RSI ના આધારે આજના દિવસનું પ્રોજેક્શન
    if rsi >= 60:
        projection = "🔥 <b>આજનો અંદાજ (Projection):</b> બિટકોઈન અત્યારે ઓવર-બૉટ (Strong Bullish) ઝોનમાં છે. માર્કેટમાં તેજીનું જોર વધારે હોવાથી આજે નવો ઉછાળો જોવા મળી શકે છે."
    elif rsi <= 40:
        projection = "⚠️ <b>આજનો અંદાજ (Projection):</b> RSI નબળાઈ દર્શાવે છે (Bearish Momentum). માર્કેટ પર થોડું પ્રેશર હોવાથી આજે પ્રોફિટ બુકિંગ કે ઘટાડો આવી શકે છે."
    else:
        projection = "⚖️ <b>આજનો અંદાજ (Projection):</b> RSI એકદમ ન્યુટ્રલ રેન્જમાં છે. બિટકોઈન આજે મોટાભાગે સાઇડવેઝ રેન્જમાં જ રન કરે તેવી શક્યતા છે."

    msg_morning = f"""☀️ {trend_emoji} <b>BTC-USD MORNING CRYPTO OUTLOOK</b>
🎯 <i>(બોટ ટેસ્ટિંગ અને ડેઇલી માર્કેટ અપડેટ)</i>

💰 <b>Live Bitcoin Price:</b> ${price:,}
🔄 <b>24H Change:</b> {change24h:+} ({p_change24h:+}%)
📊 <b>Current RSI:</b> {rsi} | <b>EMA9/21:</b> {ema9}/{ema21}

--------------------------------------------------
{projection}
--------------------------------------------------{news_details}

⚡ 24/7 Crypto Monitoring Active ✓
⏰ {now_ist().strftime('%d %b %Y  %H:%M IST')}"""

    send_telegram(msg_morning)
    print("Morning Bitcoin Report Sent!")
    exit(0)

# ---------------------------------------------------------
# ૨. દિવસ દરમિયાન બાકીના સમયે લાઈવ ટ્રેન્ડ સ્કેન કરવો
# ---------------------------------------------------------
buy_signal  = (ema9 > ema21) and (45 <= rsi <= 65) and (price > ema9)
sell_signal = (ema9 < ema21) and (35 <= rsi <= 55) and (price < ema9)

if not buy_signal and not sell_signal:
    print("સિગ્નલ મેચ થતું નથી. WAIT.")
    exit(0)

sig = "BUY" if buy_signal else "SELL"
emoji = "🟢📈" if buy_signal else "🔴📉"

t1  = round(price + (MOVE if sig == "BUY" else -MOVE), 2)
sl  = round(price + (-MOVE if sig == "BUY" else MOVE), 2)

msg = f"""{emoji} <b>{SYMBOL} {sig} SIGNAL!</b>

💰 <b>Price:</b> ${price:,}
📊 <b>EMA9:</b> {ema9} | <b>EMA21:</b> {ema21}
📉 <b>RSI:</b> {rsi} | <b>Vol:</b> {vol_x}x

🎯 <b>Entry:</b>    ${price:,}
✅ <b>Target 1:</b>  ${t1:,}
🛑 <b>Stop Loss:</b> ${sl:,}{news_details}

⚡ 24/7 Live Crypto Agent Running ✓
⏰ {now_ist().strftime('%d %b %Y  %H:%M IST')}"""

send_telegram(msg)
print(f"Live Signal Sent: {sig}")
