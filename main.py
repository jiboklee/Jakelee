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

        if not symbol or not action or not amount:
            print("[❌ ERROR] Missing required field in payload")
            return jsonify({"error": "Missing symbol/action/amount"}), 400

        # 🔧 수량을 float으로 강제 변환 및 유효성 검사
        try:
            amount = float(amount)
        except:
            print(f"[❌ ERROR] amount '{amount}' is not a valid number")
            return jsonify({"error": "Invalid amount format"}), 400

        # 🔧 레버리지 자동 설정
        set_leverage(symbol, leverage=10)

        # 📩 주문 실행
        response = place_order(symbol, action, amount)
        print("[✅ Order Response]:", response)
        return jsonify(response)

    except Exception as e:
        print("[❌ Exception]:", str(e))
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

# 📈 주문 실행 함수
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

        # 🔍 Binance 주문 요청 및 응답 출력
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
