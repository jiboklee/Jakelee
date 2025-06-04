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

# 현재 포지션 상태 저장
current_position = None  # "long", "short", None

@app.route('/')
def home():
    return "Binance Auto Trading Server is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    global current_position
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
        action = json_data.get("action").lower()
        amount = json_data.get("amount")
        price = float(json_data.get("price"))
        tp_mul = float(json_data.get("tp_multiplier", 1.004))
        sl_mul = float(json_data.get("sl_multiplier", 0.996))

        if not symbol or not action or not amount or not price:
            print("[❌ ERROR] 필수 데이터 누락")
            return jsonify({"error": "Missing required fields"}), 400

        # 롱 or 숏 중복 진입 방지 로직
        if current_position == "long" and action == "sell":
            print("⚠️ 현재 롱 포지션 보유중 → 숏 시그널 무시")
            return jsonify({"status": "ignored - holding long"})
        elif current_position == "short" and action == "buy":
            print("⚠️ 현재 숏 포지션 보유중 → 롱 시그널 무시")
            return jsonify({"status": "ignored - holding short"})

        tp = round(price * tp_mul, 2)
        sl = round(price * sl_mul, 2)

        print(f"[📈 TP/SL 계산] 진입가={price}, TP={tp}, SL={sl}")

        set_leverage(symbol, leverage=10)
        response = place_order(symbol, action, amount, tp, sl)

        # 현재 포지션 업데이트
        current_position = "long" if action == "buy" else "short"
        print(f"[📌 현재 포지션] → {current_position}")

        return jsonify(response)

    except Exception as e:
        print("[❌ UNHANDLED ERROR]:", str(e))
        return jsonify({"error": str(e)}), 500

def set_leverage(symbol, leverage=10):
    url = "https://fapi.binance.com/fapi/v1/leverage"
    params = {
        "symbol": symbol,
        "leverage": leverage,
        "timestamp": int(time.time() * 1000)
    }
    sign(params)
    headers = {"X-MBX-APIKEY": API_KEY}
    res = requests.post(url, params=params, headers=headers)
    print("[⚙️ 레버리지 설정 결과]:", res.text)

def place_order(symbol, action, amount, tp, sl):
    url = "https://fapi.binance.com/fapi/v1/order"
    side = "BUY" if action == "buy" else "SELL"

    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": round(float(amount), 3),
        "timestamp": int(time.time() * 1000)
    }
    sign(params)
    headers = {"X-MBX-APIKEY": API_KEY}
    res = requests.post(url, params=params, headers=headers)
    print("[📤 시장 주문 응답]:", res.text)

    # TP/SL 주문 설정
    opp_side = "SELL" if side == "BUY" else "BUY"

    for label, price_level, stop_type in [("TP", tp, "TAKE_PROFIT_MARKET"), ("SL", sl, "STOP_MARKET")]:
        stop_params = {
            "symbol": symbol,
            "side": opp_side,
            "type": stop_type,
            "stopPrice": price_level,
            "closePosition": "true",
            "timeInForce": "GTC",
            "timestamp": int(time.time() * 1000)
        }
        sign(stop_params)
        stop_res = requests.post(url, params=stop_params, headers=headers)
        print(f"[📌 {label} 주문]:", stop_res.text)

    return res.json()

def sign(params):
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

# ✅ Render에서 동작하도록 포트 지정
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
