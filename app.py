from flask import Flask, request
import os
import time
import hmac
import hashlib
import requests

app = Flask(__name__)

# Render 환경 변수에서 API 키 불러오기
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📩 받은 메시지:", data)

    symbol = data.get("symbol")
    action = data.get("action")
    amount = data.get("amount")

    if action == "buy":
        result = place_order(symbol, amount)
        return {"status": "buy executed", "result": result}
    else:
        return {"error": "unknown action"}, 400

def place_order(symbol, usdt_amount):
    url = "https://api.binance.com/api/v3/order"
    timestamp = int(time.time() * 1000)

    # 시장가 매수 주문 구성
    params = f"symbol={symbol}&side=BUY&type=MARKET&quoteOrderQty={usdt_amount}&timestamp={timestamp}"
    signature = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    full_url = f"{url}?{params}&signature={signature}"

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    res = requests.post(full_url, headers=headers)
    print("📤 바이낸스 응답:", res.json())
    return res.json()

# ✅ Render 외부에서 접근 가능하도록 설정 (핵심!)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
