from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
import os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
client = Client(API_KEY, API_SECRET)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    signal = data.get("signal")
    symbol = "BTCUSDT"
    usdt_amount = 30
    leverage = 5

    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    mark_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    qty = round((usdt_amount * leverage) / mark_price, 3)

    if signal == "buy":
        client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=qty)
        tp = round(mark_price * 1.006, 2)
        sl = round(mark_price * 0.996, 2)
        close_side = SIDE_SELL
    elif signal == "sell":
        client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=qty)
        tp = round(mark_price * 0.994, 2)
        sl = round(mark_price * 1.004, 2)
        close_side = SIDE_BUY
    else:
        return jsonify({"error": "unknown signal"}), 400

    # TP
    client.futures_create_order(
        symbol=symbol,
        side=close_side,
        type=ORDER_TYPE_LIMIT,
        price=str(tp),
        quantity=qty,
        timeInForce=TIME_IN_FORCE_GTC,
        reduceOnly=True
    )

    # SL
    try:
        client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type=ORDER_TYPE_STOP_MARKET,
            stopPrice=str(sl),
            quantity=qty,
            reduceOnly=True
        )
    except Exception as e:
        print("❌ SL 주문 실패:", str(e))

    print(f"✅ {signal.upper()} 주문 완료 | TP: {tp}, SL: {sl}")
    return jsonify({"status": "ok"}), 200

@app.route("/")
def index():
    return "✅ Binance Webhook 서버 작동 중"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
