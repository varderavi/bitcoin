import requests
import pytz
import xml.etree.ElementTree as ET
import time
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = "8874026729:AAEgzZr0UslgaKGdPiUjZMONNuFCKL-pqsY"
CHAT_ID   = "1358803794"

IST = pytz.timezone("Asia/Kolkata")
ROUTINE_PRE_VOLUME = 5000  

user_status = {}

def now_ist():
    return datetime.now(IST)

def get_expiry_alert():
    n = now_ist()
    weekday = n.weekday() 
    if weekday == 0: return "📅 <b>EXPIRY ALERT:</b> આજે <b>MIDCAP SELECT</b> ની એક્સપાયરી છે! 🎯"
    elif weekday == 1: return "📅 <b>EXPIRY ALERT:</b> આજે <b>FINNIFTY</b> ની ધાંસુ એક્સપાયરી છે! 🎯"
    elif weekday == 2: return "📅 <b>EXPIRY ALERT:</b> આજે <b>BANKNIFTY</b> નો મોટો દિવસ (Expiry) છે! 🎯"
    elif weekday == 3: return "📅 <b>EXPIRY ALERT:</b> આજે <b>NIFTY 50</b> નો મેઈન એક્સપાયરી ધડાકો છે! 🎯"
    elif weekday == 4: return "📅 <b>EXPIRY ALERT:</b> આજે <b>SENSEX</b> ની ધમાકેદાર એક્સપાયરી છે! 🎯"
    return ""

def fetch_live_data(symbol, interval="5m", timeframe_range="2d", include_prepost=False):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={timeframe_range}&includePrePost={'true' if include_prepost else 'false'}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes = [x for x in res["indicators"]["quote"][0]["close"] if x is not None]
        highs  = [x for x in res["indicators"]["quote"][0]["high"] if x is not None]
        lows   = [x for x in res["indicators"]["quote"][0]["low"] if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        pre_price = res["meta"].get("preMarketPrice", price)
        
        name = symbol
        if symbol == "^NSEI": name = "NIFTY 50"
        elif symbol == "^NSEBANK": name = "BANK NIFTY"
        elif symbol == "^BSESN": name = "SENSEX"
        elif symbol == "^NSMIDCP": name = "NIFTY MIDCAP 100"
        elif symbol == "^NSE91": name = "NIFTY NEXT 50"
        elif symbol == "HBLENGINE.NS": name = "HBL POWER"
        
        day_high = round(highs[-1], 2) if highs else price
        day_low = round(lows[-1], 2) if lows else price
        
        return round(price, 2), closes, volumes, round(prev_close, 2), round(pre_price, 2), name, day_high, day_low
    except:
        return None, [], [], None, None, symbol, None, None

def calc_ema(data, p):
    if len(data) < p: return None
    k = 2/(p+1); e = sum(data[:p])/p
    for v in data[p:]: e = v*k + e*(1-k)
    return round(e, 2)

def calc_rsi(data, p=14):
    if len(data) < p+1: return "N/A"
    g = sum(max(data[i]-data[i-1],0) for i in range(len(data)-p,len(data)))
    l = sum(max(data[i-1]-data[i],0) for i in range(len(data)-p,len(data)))
    ag, al = g/p, l/p
    return round(100 - 100/(1+ag/al), 1) if al else 100.0

def fetch_google_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        for item in root.findall(".//item")[:1]:
            title = item.find("title").text.split(" - ")[0]
            link = item.find("link").text
            return f"\n\n📢 <b>LATEST NEWS:</b>\n• <b>{title}</b>\n  🔗 <a href='{link}'>વાંચવા માટે ક્લિક કરો</a>"
    except:
        pass
    return ""

# =========================================================
# 🔄 ડાયનેમિક સેન્ટિમેન્ટ અને એન્ટ્રી/એક્ઝિટ એન્જિન (શેર્સ અને ઇન્ડેક્સ બંને માટે)
# =========================================================
def generate_advanced_report(symbol, is_crypto=False):
    price, closes, _, prev_close, _, name, d_high, d_low = fetch_live_data(symbol)
    if not price: return f"❌ '{symbol}' નો લાઈવ ડેટા મળી શક્યો નહિ."
    
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    sign = "$" if is_crypto else "₹"
    
    # ડિફોલ્ટ સેટિંગ્સ
    sentiment = "⚖️ SIDEWAYS / NEUTRAL"
    action = "👀 માર્કેટ અત્યારે કન્ફ્યુઝન ઝોનમાં છે, શાંતિ રાખો અને વેટ કરો."
    
    # ડાયનેમિક રેન્જ બફર પકડવું (ઇન્ડેક્સ માટે મોટો બફર અને શેર માટે નાનો)
    buffer = 20 if "NIFTY" in name or "SENSEX" in name else (30 if is_crypto else 1.5)
    buy_above = round(max(ema9 or price, d_high) + buffer, 2)
    entry_logic_text = f"💡 <b>SUGGESTED ENTRY POINT:</b>\n🚀 <b>Buy Breakout:</b> {sign}{buy_above:,} ની ઉપર મજબૂત ગ્રીન કેન્ડલ ક્લોઝ થાય તો જ નવો ટ્રેડ લેવો."
    
    # 🧠 ટ્રેન્ડ અને રિસ્ક-રેવોર્ડ 1:2 કેલ્ક્યુલેશન
    if ema9 and ema21 and rsi != "N/A":
        # ૧. તેજીનો ટ્રેન્ડ (Bullish)
        if price > ema9 and price > ema21 and rsi >= 55:
            sentiment = "🚀 STRONG BULLISH"
            action = f"🟢 <b>BUY / HOLD:</b> આખા માર્કેટમાં જબરદસ્ત તેજીનો માહોલ છે. પોઝિશન હોલ્ડ રાખવી અથવા કરંટ ભાવથી એન્ટ્રી કરી શકાય."
            t_val = 100 if is_crypto else (150 if "BANK" in name else (80 if "NIFTY" in name or "SENSEX" in name else 10))
            sl_val = 50 if is_crypto else (75 if "BANK" in name else (40 if "NIFTY" in name or "SENSEX" in name else 5))
            entry_logic_text = f"🎯 <b>Logic Target (+{sign}{t_val}):</b> {sign}{round(price+t_val,2):,} [R:R 1:2]\n🛑 <b>Logic Stop Loss (-{sign}{sl_val}):</b> {sign}{round(price-sl_val,2):,}"
            
        elif price > ema9 and 50 <= rsi < 55:
            sentiment = "🟢 MILD BULLISH"
            action = f" odds <b>BUY ON DIPS:</b> મોમેન્ટમ પોઝિટિવ તરફ જઈ રહ્યું છે. નાના ડીપ પર એડ કરી શકાય."
            t_val = 100 if is_crypto else (150 if "BANK" in name else (80 if "NIFTY" in name or "SENSEX" in name else 10))
            sl_val = 50 if is_crypto else (75 if "BANK" in name else (40 if "NIFTY" in name or "SENSEX" in name else 5))
            entry_logic_text = f"🎯 <b>Logic Target (+{sign}{t_val}):</b> {sign}{round(price+t_val,2):,} [R:R 1:2]\n🛑 <b>Logic Stop Loss (-{sign}{sl_val}):</b> {sign}{round(price-sl_val,2):,}"
            
        # ૨. મંદીનો ટ્રેન્ડ (Bearish) -> 🔥 હોલ્ડિંગ સેલ સજેશન લોજિક
        elif price < ema9 and price < ema21 and rsi <= 42:
            sentiment = "⚠️ BEARISH PRESSURE"
            
            # શેર અને ઇન્ડેક્સ બંને માટે કોમન સેલ સજેશન
            if "NIFTY" in name or "SENSEX" in name:
                action = f"🔴 <b>AVOID NEW BUY:</b> આખો ઇન્ડેક્સ ભારે મંદીના સકંજામાં છે. નવી કોઈ જ બાયિંગ એન્ટ્રી અત્યારે ભૂલથી પણ ન કરવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> આખા માર્કેટનો ટ્રેન્ડ નેગેટિવ હોવાથી, જો તમારા પર્સનલ શેર હોલ્ડિંગ્સમાં કડાકો આવતો હોય તો મોટું નુકસાન રોકવા પ્રોફિટ બુક અથવા <b>SELL (Exit)</b> કરવાનું ખાસ સજેશન છે!"
            else:
                action = f"🔴 <b>AVOID NEW BUY:</b> આ સ્ક્રિપ્ટમાં ભારે સેલિંગ પ્રેશર છે, નવી ખરીદી ટાળવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> જો તમારી પાસે આનું હોલ્ડિંગ પડ્યું હોય, તો કેપિટલ બચાવવા કરંટ ભાવથી <b>SELL (Exit)</b> કરવાનું સ્ટ્રોન્ગ સજેશન છે!"
                
            t_val = 100 if is_crypto else (150 if "BANK" in name else (80 if "NIFTY" in name or "SENSEX" in name else 10))
            sl_val = 50 if is_crypto else (75 if "BANK" in name else (40 if "NIFTY" in name or "SENSEX" in name else 5))
            entry_logic_text = f"🎯 <b>Short Target (-{sign}{t_val}):</b> {sign}{round(price-t_val,2):,} [R:R 1:2]\n🛑 <b>Short Stop Loss (+{sign}{sl_val}):</b> {sign}{round(price+sl_val,2):,}"

    news = fetch_google_news("Bitcoin Crypto" if is_crypto else name)
    expiry_text = get_expiry_alert() if not is_crypto else ""
    if expiry_text: expiry_text = f"\n\n{expiry_text}"
    
    emoji = "🟢📈" if change >= 0 else "🔴📉"
    
    return f"""{emoji} <b>{name} LIVE REPORT & SENTIMENT</b>

💰 <b>Live Price:</b> {sign}{price:,} ({change:+} | {p_change:+}-%)
🔼 <b>Day High:</b> {sign}{d_high:,} | 🔽 <b>Day Low:</b> {sign}{d_low:,}
📉 <b>RSI (14):</b> {rsi} | 📈 <b>EMA9:</b> {ema9 or 'N/A'}
------------------------------------------
🔥 <b>Intraday Sentiment:</b> {sentiment}
👉 <b>કરંટ પ્રાઈઝથી શું કરવું?:</b> {action}
------------------------------------------
{entry_logic_text}{expiry_text}{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

# ============================================
# TELEGRAM UI & INTERACTIONS
# ============================================
def send_telegram_msg(text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def send_main_menu():
    markup = {
        "inline_keyboard": [
            [{"text": "⚡ HBL Power", "callback_data": "m_hbl"}, {"text": "🪙 Bitcoin (24/7)", "callback_data": "m_btc"}],
            [{"text": "📊 NIFTY 50", "callback_data": "m_nifty"}, {"text": "📈 BANK NIFTY", "callback_data": "m_bnifty"}],
            [{"text": "💎 SENSEX", "callback_data": "m_sensex"}, {"text": "🚀 NIFTY NEXT 50", "callback_data": "m_next50"}],
            [{"text": "🔥 MIDCAP 100", "callback_data": "m_midcap"}, {"text": "🔍 Search Stock", "callback_data": "m_search"}]
        ]
    }
    send_telegram_msg("👋 <b>નમસ્તે રવિ! (Market Master Panel)</b>\n\nબધા જ ઇન્ડેક્સ અને શેર્સમાં હવે સેન્ટિમેન્ટ, પ્રાઈઝ રેન્જ અને હોલ્ડિંગ સેલિંગ એલર્ટ ૧૦૦% જોડી દીધું છે. નીચે ક્લિક કરો:", reply_markup=markup)

def handle_callback(callback_id, data):
    global user_status
    text = ""
    if data == "m_hbl": text = generate_advanced_report("HBLENGINE.NS")
    elif data == "m_btc": text = generate_advanced_report("BTC-USD", is_crypto=True)
    elif data == "m_nifty": text = generate_advanced_report("^NSEI")
    elif data == "m_bnifty": text = generate_advanced_report("^NSEBANK")
    elif data == "m_sensex": text = generate_advanced_report("^BSESN")
    elif data == "m_next50": text = generate_advanced_report("^NSE91")
    elif data == "m_midcap": text = generate_advanced_report("^NSMIDCP")
    elif data == "m_search":
        user_status[CHAT_ID] = "WAITING_FOR_SEARCH"
        text = "🔍 <b>Script Search Activated:</b>\n\nકૃપા કરીને નામ મોકલો:"
    
    if text: send_telegram_msg(text)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})

def handle_search_text(user_text):
    global user_status
    query = user_text.upper().strip()
    mapping = {
        "RELIANCE": "RELIANCE.NS", "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS",
        "TCS": "TCS.NS", "SBI": "SBIN.NS", "HDFC": "HDFCBANK.NS"
    }
    symbol = mapping.get(query, f"{query}.NS")
    text = generate_advanced_report(symbol)
    send_telegram_msg(text)
    user_status[CHAT_ID] = None 

# ============================================
# MAIN LOOP
# ============================================
print("Master engine with FULL Index & Stock Down-Trend Logic Active...")
offset = 0
start_time = time.time()

while time.time() - start_time < 110:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
        r = requests.get(url, timeout=10).json()
        if "result" in r:
            for update in r["result"]:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    user_msg = update["message"]["text"]
                    if user_msg.lower() in ["hi", "hello", "menu"]:
                        send_main_menu()
                    else:
                        handle_search_text(user_msg)
                elif "callback_query" in update:
                    handle_callback(update["callback_query"]["id"], update["callback_query"]["data"])
    except:
        pass
    time.sleep(1)
