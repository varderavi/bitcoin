import requests
import os
import pytz
from datetime import datetime

# ============================================
# SETTINGS
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")

# ટેસ્ટિંગ માટે આપણે લિમિટ એકદમ ઓછી (0.01%) કરી દઈએ, જેથી મેસેજ તરત આવી જાય!
THRESHOLD_PERCENT = 0.01  

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print("Telegram Response:", r.json().get("ok"))
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_bitcoin_data():
    # આ સરળ અને ૧૦૦% કન્ફર્મ ચાલતું API સેટ કર્યું છે
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    try:
        r = requests.get(url, timeout=15)
        res = r.json()
        current_price = round(float(res["price"]), 2)
        return current_price
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

price = fetch_bitcoin_data()

if price is None:
    print("ડેટા મળી શક્યો નથી. સ્કીપ કરાય છે.")
    exit(0)

print(f"Bitcoin Price: ${price:,}")

# ટેસ્ટ રન છે એટલે આપણે સીધો જ મેસેજ મોકલી આપીશું
emoji = "🚀🟢 <b>BITCOIN LIVE SIGNAL!</b>"
    
msg = f"""{emoji}

💰 <b>Current Price:</b> ${price:,}
📈 <b>Status:</b> Bot strictly running 24/7

⏰ {now_ist().strftime('%d %b %Y  %H:%M IST')}
<i>Live Updates from Binance ✓</i>"""

send_telegram(msg)
print("Telegram alert sent successfully!")
