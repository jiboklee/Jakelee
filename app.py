from flask import Flask, request, jsonify
import hmac, hashlib, time, os, requests

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://fapi.binance.com"

def place_order(symbol, side, amount):
    path = "/fapi/v1/order"
    url = BASE_URL + path
    timestamp = int(time.time() * 1000)
    params = f"symbol={symbol}&side={side.upper()}&type=MARKET&quantity={amount}&timestamp={timestamp}"

    signature = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    full_url = f"{url}?{params}&signature={signature}"
    headers = {"X-MBX-API-KEY": API_KEY}

    res = requests.post(full_url, headers=headers)
    return res.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Received webhook:", data)

    symbol = data.get("symbol")
    action = data.get("action")
    amount = data.get("amount", 30)

    if not all([symbol, action]):
        return "Invalid payload", 400

    result = place_order(symbol, action, amount)
    print("📤 Order result:", result)
    return jsonify(result)

@app.route("/")
def root():
    return "✅ Binance Auto-Trader Live"
