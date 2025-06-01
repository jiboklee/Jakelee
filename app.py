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

# 주문 함수
def place_order(symbol, amount):
    print(f"📦 바이낸스에 주문 전송 준비: {symbol}, {amount}")

    base_url = "https://api.binance.com"
    endpoint = "/api/v3/order"
    url = base_url + endpoint

    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": amount,  # 금액 기준 주문
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
        print(f"❌ 바이낸스 주문 실패: {e}")
        return {"error": str(e)}

# 웹훅 엔드포인트
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print(f"📩 받은 메시지: {data}")

        symbol = data.get("symbol")
        amount = data.get("amount")

        if not symbol or not amount:
            return jsonify({"error": "symbol or amount missing"}), 400

        result = place_order(symbol, amount)
        return jsonify(result)
    except Exception as e:
        print(f"❌ 처리 중 예외 발생: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
