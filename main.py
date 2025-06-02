//@version=5
indicator("Scalp_TrendMomentum_5min_Aggressive", overlay=true)

ema20 = ta.ema(close, 20)
ema50 = ta.ema(close, 50)
rsi = ta.rsi(close, 14)
vol = volume
volAvg = ta.sma(volume, 20)

longTrend = ema20 > ema50
longRSI = rsi < 60
longCandle = (close > open) and (close - open > (high - low) * 0.6)
longVolume = vol > volAvg

longSignal = longTrend and longRSI and longCandle and longVolume

shortTrend = ema20 < ema50
shortRSI = rsi > 40
shortCandle = (close < open) and (open - close > (high - low) * 0.6)
shortVolume = vol > volAvg

shortSignal = shortTrend and shortRSI and shortCandle and shortVolume

alertcondition(longSignal, title="Aggressive Long", message='{"signal":"buy", "strategy":"Aggressive5min", "ticker":"{{ticker}}", "price":{{close}}}')
alertcondition(shortSignal, title="Aggressive Short", message='{"signal":"sell", "strategy":"Aggressive5min", "ticker":"{{ticker}}", "price":{{close}}}')

plotshape(longSignal, title="Buy", location=location.belowbar, color=color.lime, style=shape.triangleup, size=size.small)
plotshape(shortSignal, title="Sell", location=location.abovebar, color=color.red, style=shape.triangledown, size=size.small)

plot(ema20, color=color.green)
plot(ema50, color=color.orange)

---

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
    try:
        data = request.get_json(force=True)
        if not data:
            print("❌ [ERROR] Webhook에 JSON 데이터 없음")
            return jsonify({"error": "Invalid JSON"}), 400

        signal = data.get("signal")
        strategy = data.get("strategy")
        if signal not in ["buy", "sell"] or strategy != "Aggressive5min":
            print(f"❌ [ERROR] 잘못된 요청: signal={signal}, strategy={strategy}")
            return jsonify({"error": "Invalid signal or strategy"}), 400

        symbol = "BTCUSDT"
        usdt_amount = 30
        leverage = 5

        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        mark_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
        qty = round((usdt_amount * leverage) / mark_price, 3)

        print(f"📥 Webhook 수신됨: {signal.upper()} | 전략: {strategy} | 수량: {qty} | 가격: {mark_price}")

        if signal == "buy":
            client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=qty)
            tp = round(mark_price * 1.004, 2)
            sl = round(mark_price * 0.996, 2)
            close_side = SIDE_SELL
        else:
            client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=qty)
            tp = round(mark_price * 0.996, 2)
            sl = round(mark_price * 1.004, 2)
            close_side = SIDE_BUY

        client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type=ORDER_TYPE_LIMIT,
            price=str(tp),
            quantity=qty,
            timeInForce=TIME_IN_FORCE_GTC,
            reduceOnly=True
        )

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

    except Exception as e:
        print("❌ [Webhook 처리 오류]", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route("/")
def index():
    return "✅ Binance Webhook 서버 작동 중"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
