from flask import Flask, request, jsonify
import os
import json
import requests
import hmac
import hashlib
import time  # 꼭 있어야 합니다!

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

@app.route('/')
def home():
    return "Binance Auto Trading Server is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print("[Webhook Triggered] 🔔")
        print("Payload:", data)

        symbol = data.get("symbol")
        action = data.get("action")
        amount = data.get("amount")

        if not symbol or not action or not amount:
            print("[❌ ERROR] Missing required field in payload")
            return jsonify({"error": "Missing symbol/action/amount"}), 400

        response = place_order(symbol, action, amount)
        print("[✅ Order Response]:", response)
        return jsonify(response)

    except Exception as e:
        print("[❌ Exception]:", str(e))
        return jsonify({"error": str(e)}), 500

def place_order(symbol, action, amount):
    url = "https://fapi.binance.com/fapi/v1/order"

    params = {
        "symbol": symbol,
        "side": "BUY" if action == "buy" else "SELL",
        "type": "MARKET",
        "quantity": amount,
        "timestamp": int(round(time.time() * 1000))
    }

    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    res = requests.post(url, params=params, headers=headers)
    return res.json()

# ✅ 반드시 추가해야 함 (Render에서 포트 인식)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
