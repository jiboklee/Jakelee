from flask import Flask, request, jsonify
import os
import json
import requests
import hmac
import hashlib
import time

app = Flask(__name__)

# 🔐 환경변수에서 API 키 가져오기
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("❌ API_KEY or API_SECRET is not set in environment variables")

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

        print(f"[🔍 Parsed] symbol={symbol}, action={action}, amount={amount}")

        # 필수 필드 누락 체크
        if not symbol or not action or not amount:
            print("[❌ ERROR] Missing symbol/action/amount")
            return jsonify({"error": "Missing symbol/action/amount"}), 400

        # amount를 float으로 변환 시도
        try:
            amount = float(amount)
        except Exception as e:
            print(f"[❌ ERROR] amount 변환 실패: amount={amount}, error={e}")
            return jsonify({"error": f"Invalid amount format: {amount}"}), 400

        # 🔧 레버리지 설정
        set_leverage(symbol, leverage=10)

        # 📈 주문 실행
        response = place_order(symbol, action, amount)
        print("[✅ Order Response]:", response)
        return jsonify(response)

    except Exception as e:
        print("[❌ UNHANDLED Exception]:", str(e))
        return jsonify({"error": str(e)}), 500

# 🔧 레버리지 설정 함수
def set_leverage(symbol, leverage=10):
    url = "https://fapi.binance.com/fapi/v1/leverage"
    params = {
        "symbol": symbol,
        "leverage": leverage,
        "timestamp": int(time.time() * 1000)
    }

    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    res = requests.post(url, params=params, headers=headers)
    print("[⚙️ Set Leverage Response]:", res.text)

# 📤 주문 실행 함수
def place_order(symbol, action, amount):
    url = "https://fapi.binance.com/fapi/v1/order"

    try:
        params = {
            "symbol": symbol,
            "side": "BUY" if action.lower() == "buy" else "SELL",
            "type": "MARKET",
            "quantity": round(float(amount), 3),
            "timestamp": int(time.time() * 1000)
        }

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature

        headers = {
            "X-MBX-APIKEY": API_KEY
        }

        print("[📤 Request Params]:", params)
        res = requests.post(url, params=params, headers=headers)
        print("[🧾 Binance API Response]:", res.text)

        return res.json()

    except Exception as e:
        print("[❌ Binance Order Exception]:", str(e))
        return {"error": str(e)}

# ✅ Render용 포트 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
