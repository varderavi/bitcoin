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
ROUTINE_PRE_VOLUME = 5000  # HBL અને અન્ય શેર્સ માટે પ્રી-માર્કેટ બેન્ચમાર્ક વોલ્યુમ

# યુઝર સર્ચ સ્ટેટ ટ્રેક કરવા માટે
user_status = {}

def now_ist():
    return datetime.now(IST)

# 📅 એક્સપાયરી ચેક કરવાનું લોજિક (સોમ-શુક્ર)
def get_expiry_alert():
    n = now_ist()
    weekday = n.weekday() # 0=સોમ, 1=મંગળ, 2=બુધ, 3=ગુરુ, 4=શુક્ર
    
    if weekday == 0: return "📅 <b>EXPIRY ALERT:</b> આજે <b>MIDCAP SELECT</b> ની એક્સપાયરી છે! 🎯"
    elif weekday == 1: return "📅 <b>EXPIRY ALERT:</b> આજે <b>FINNIFTY</b> ની ધાંસુ એક્સપાયરી છે! 🎯"
    elif weekday == 2: return "📅 <b>EXPIRY ALERT:</b> આજે <b>BANKNIFTY</b> નો મોટો દિવસ (Expiry) છે! 🎯"
    elif weekday == 3: return "📅 <b>EXPIRY ALERT:</b> આજે <b>NIFTY 50</b> નો મેઈન એક્સપાયરી ધડાકો છે! 🎯"
    elif weekday == 4: return "📅 <b>EXPIRY ALERT:</b> આજે <b>SENSEX</b> ની ધમાકેદાર એક્સપાયરી છે! 🎯"
    return ""

# 🔍 લાઈવ ડેટા એન્જિન
def fetch_live_data(symbol, interval="5m", timeframe_range="2d", include_prepost=False):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={timeframe_range}&includePrePost={'true' if include_prepost else 'false'}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes = [x for x in res["indicators"]["quote"][0]["close"] if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        pre_price = res["meta"].get("preMarketPrice", price)
        
        name = symbol
        if symbol == "^NSEI": name = "NIFTY 50"
        elif symbol == "^NSEBANK": name = "BANK NIFTY"
        elif symbol == "^BSESN": name = "SENSEX"
        elif symbol == "HBLENGINE.NS": name = "HBL POWER"
        
        return round(price, 2), closes, volumes, round(prev_close, 2), round(pre_price, 2), name
    except:
        return None, [], [], None, None, symbol

def fetch_google_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        for item in root.findall(".//item")[:1]:
            title = item.find("title").text.split(" - ")[0]
            link = item.find("link").text
            return f"\n\n📰 <b>LATEST NEWS:</b>\n• <b>{title}</b>\n  🔗 <a href='{link}'>વાંચવા માટે ક્લિક કરો</a>"
    except:
        pass
    return ""

# =========================================================
# 🎯 ૧. સવારે ૦૯:૧૦ વાગ્યાનો વોલ્યુમ શોકર અને ન્યૂઝ ધડાકો
# =========================================================
def run_morning_910_scan():
    n = now_ist()
    # જો શનિ-રવિ હોય તો ઇન્ડિયન માર્કેટ સ્કેન બંધ રાખવું
    if n.weekday() >= 5: return
    
    price, closes, volumes, prev_close, pre_price, name = fetch_live_data("HBLENGINE.NS", "1m", "1d", include_prepost=True)
    if price:
        pre_market_vol = sum([v for v in volumes if v is not None])
        vol_multiple = round(pre_market_vol / ROUTINE_PRE_VOLUME, 1) if pre_market_vol else 0
        news = fetch_google_news("HBL Power")
        
        # જો વોલ્યુમ રૂટિન કરતાં ૩ ગણું વધારે હોય અથવા કોઈ ફ્રેશ ન્યૂઝ હોય તો જ મોટી એલર્ટ
        if vol_multiple >= 3.0 or news != "":
            change = round(pre_price - prev_close, 2)
            p_change = round((change / prev_close) * 100, 2)
            direction = "🟢 GAP-UP" if change >= 0 else "🔴 GAP-DOWN"
            expiry_text = get_expiry_alert()
            
            msg = f"""🔥🚨 <b>09:10 AM MORNING HBL BREAKOUT ALERT!</b>

📊 <b>Pre-Open Price:</b> ₹{pre_price} ({direction} {p_change:+}%)\n📊 <b>Pre-Market Volume:</b> {pre_market_vol:,} shares (<b>{vol_multiple}x Routine</b>)
------------------------------------------
💡 <b>વોલ્યુમ એલર્ટ:</b> કરંટ વોલ્યુમ સામાન્ય દિવસો કરતાં ઘણું અલગ છે! 9:15 એ ઓપનિંગ થતાં જ મોટી મુવમેન્ટ આવી શકે છે.{news}
------------------------------------------
{expiry_text}
⏰ {n.strftime('%H:%M IST')}"""
            send_telegram_msg(msg)

def get_report(symbol, is_crypto=False):
    price, closes, _, prev_close, _, name = fetch_live_data(symbol)
    if not price: return f"❌ '{symbol}' નો લાઈવ ડેટા મળી શક્યો નહિ. કૃપા કરીને સાચો સિમ્બોલ ચેક કરો."
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    sign = "$" if is_crypto else "₹"
    emoji = "🟢📈" if change >= 0 else "🔴📉"
    
    news = fetch_google_news("Bitcoin Crypto" if is_crypto else name)
    expiry_text = "" if is_crypto else get_expiry_alert()
    if expiry_text: expiry_text = f"\n\n{expiry_text}"
    
    return f"""{emoji} <b>{name} LIVE REPORT</b>

💰 <b>Live Price:</b> {sign}{price:,}
🔄 <b>Today's Change:</b> {change:+} ({p_change:+}%){expiry_text}{news}
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
            [{"text": "💎 SENSEX", "callback_data": "m_sensex"}, {"text": "🔍 Search Stock", "callback_data": "m_search"}]
        ]
    }
    send_telegram_msg("👋 <b>નમસ્તે રવિ! (Market Master Panel)</b>\n\nતમારા ૫ મુખ્ય ઇમ્પોર્ટન્ટ પોઇન્ટ્સ અને લાઈવ અપડેટ્સ માટે નીચેના બટન પર ક્લિક કરો. અથવા કોઈ નવો શેર શોધવા સર્ચ બટન દબાવો:", reply_markup=markup)

def handle_callback(callback_id, data):
    global user_status
    text = ""
    
    if data == "m_hbl": text = get_report("HBLENGINE.NS")
    elif data == "m_btc": text = get_report("BTC-USD", is_crypto=True)
    elif data == "m_nifty": text = get_report("^NSEI")
    elif data == "m_bnifty": text = get_report("^NSEBANK")
    elif data == "m_sensex": text = get_report("^BSESN")
    elif data == "m_search":
        user_status[CHAT_ID] = "WAITING_FOR_SEARCH"
        text = "🔍 <b>Script Search Activated:</b>\n\nકૃપા કરીને તમે જે શેરનો લાઈવ ભાવ જોવા માંગતા હોવ તેનું નામ લખીને મોકલો (દા.ત. <code>tatamotors</code>, <code>reliance</code>, <code>tcs</code>):"
    
    if text: send_telegram_msg(text)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})

def handle_search_text(user_text):
    global user_status
    query = user_text.upper().strip()
    
    # કોમન મેપિંગ ફોર્મેટ
    mapping = {
        "RELIANCE": "RELIANCE.NS", "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS",
        "TCS": "TCS.NS", "SBI": "SBIN.NS", "SBIN": "SBIN.NS", "HDFC": "HDFCBANK.NS"
    }
    symbol = mapping.get(query, f"{query}.NS")
    
    send_telegram_msg(f"⏳ 🔄 <b>'{query}'</b> નો લાઈવ ડેટા અને ન્યૂઝ સર્ચ થઈ રહ્યા છે...")
    text = get_report(symbol)
    send_telegram_msg(text)
    user_status[CHAT_ID] = None # સ્ટેટ ક્લિયર કરો

# ============================================
# MAIN LOOP (૧૧૦ સેકન્ડ પોલિંગ સાયકલ)
# ============================================
print("Market Master engine active...")

# સવારે બરાબર ૯:૧૦ વાગ્યે ઓટોમેટિક વોલ્યુમ/ન્યૂઝ સ્કેન ટ્રિગર કરવું
n_check = now_ist()
if n_check.hour == 9 and (10 <= n_check.minute <= 12):
    run_morning_910_scan()

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
                        # જો યુઝરે સર્ચ બટન દબાવ્યા પછી નામ લખ્યું હોય
                        if user_status.get(CHAT_ID) == "WAITING_FOR_SEARCH":
                            handle_search_text(user_msg)
                        else:
                            # જો ડાયરેક્ટ કોઈ નામ લખે તો પણ બેકઅપ સર્ચ ચાલુ રાખવું
                            handle_search_text(user_msg)
                            
                elif "callback_query" in update:
                    handle_callback(update["callback_query"]["id"], update["callback_query"]["data"])
    except:
        pass
    time.sleep(1)
