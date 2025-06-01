from flask import Flask, request, jsonify
import hmac
import hashlib
import time
import requests
import os

app = Flask(__name__)

# 환경변수에서 API 키 불러오기
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# 바이낸스 주문 함수
def place_order(symbol, amount):
    print(f"📦 주문 실행: symbol={symbol}, amount={amount}")

    base_url = "https://api.binance.com"
    endpoint = "/api/v3/order"
    url = base_url + endpoint

    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": amount,
        "timestamp": timestamp
    }

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    params["signature"] = signature
    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    try:
        response = requests.post(url, headers=headers, params=params)
        print(f"📤 바이낸스 응답: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ 주문 중 오류 발생: {e}")
        return {"error": str(e)}

# Webhook 엔드포인트
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print(f"📩 받은 메시지: {data}")

        symbol = data.get("symbol")
        amount = data.get("amount")

        if not symbol or not amount:
            print("❗ symbol 또는 amount가 누락됨.")
            return jsonify({"error": "symbol or amount missing"}), 400

        result = place_order(symbol, amount)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Webhook 처리 오류: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
