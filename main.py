from flask import Flask, request, jsonify
import os
import json
import requests
import hmac
import hashlib
import time

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("❌ API_KEY or API_SECRET is not set in environment variables")

@app.route('/')
def home():
    return "Binance Auto Trading Server is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    print("=== [Webhook Activated] ===")
    try:
        data = request.get_data(as_text=True)
        print("[Raw Body]:", data)

        try:
            json_data = json.loads(data)
        except Exception as e:
            print("[❌ ERROR] JSON 파싱 실패:", e)
            return jsonify({"error": "Invalid JSON"}), 400

        print("[Parsed JSON]:", json_data)

        symbol = json_data.get("symbol")
        action = json_data.get("action")
        amount = float(json_data.get("amount"))
        entry_price = float(json_data.get("price"))

        if not symbol or not action or not amount or not entry_price:
            return jsonify({"error": "Missing required fields"}), 400

        # 투자 전문가 기준 추천 TP/SL 비율 (익절 +1.2%, 손절 -0.8%)
        tp = round(entry_price * (1.012 if action == "buy" else 0.988), 2)
        sl = round(entry_price * (0.992 if action == "buy" else 1.012), 2)

        print(f"[🔍] {action.upper()} {symbol} @ {entry_price} → TP: {tp}, SL: {sl}")

        # 레버리지 설정
        set_leverage(symbol, leverage=10)

        # 시장가 주문
        market_res = place_market_order(symbol, action, amount)
        print("[✅ Market Order]:", market_res)

        # TP/SL 지정가 주문
        tp_order = place_limit_order(symbol, "sell" if action == "buy" else "buy", amount, tp)
        sl_order = place_stop_market_order(symbol, "sell" if action == "buy" else "buy", amount, sl)

        return jsonify({
            "market_order": market_res,
            "tp_order": tp_order,
            "sl_order": sl_order
        })

    except Exception as e:
        print("[❌ UNHANDLED Exception]:", str(e))
        return jsonify({"error": str(e)}), 500

def set_leverage(symbol, leverage=10):
    url = "https://fapi.binance.com/fapi/v1/leverage"
    params = {
        "symbol": symbol,
        "leverage": leverage,
        "timestamp": int(time.time() * 1000)
    }
    sign_and_send(params, url)

def place_market_order(symbol, action, amount):
    url = "https://fapi.binance.com/fapi/v1/order"
    params = {
        "symbol": symbol,
        "side": action.upper(),
        "type": "MARKET",
        "quantity": round(amount, 3),
        "timestamp": int(time.time() * 1000)
    }
    return sign_and_send(params, url)

def place_limit_order(symbol, action, amount, price):
    url = "https://fapi.binance.com/fapi/v1/order"
    params = {
        "symbol": symbol,
        "side": action.upper(),
        "type": "LIMIT",
        "quantity": round(amount, 3),
        "price": price,
        "timeInForce": "GTC",
        "timestamp": int(time.time() * 1000)
    }
    return sign_and_send(params, url)

def place_stop_market_order(symbol, action, amount, stop_price):
    url = "https://fapi.binance.com/fapi/v1/order"
    params = {
        "symbol": symbol,
        "side": action.upper(),
        "type": "STOP_MARKET",
        "stopPrice": stop_price,
        "closePosition": False,
        "quantity": round(amount, 3),
        "timestamp": int(time.time() * 1000)
    }
    return sign_and_send(params, url)

def sign_and_send(params, url):
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    headers = {"X-MBX-APIKEY": API_KEY}
    res = requests.post(url, params=params, headers=headers)
    print(f"[🧾 Binance API Response from {url}]:", res.text)
    return res.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
