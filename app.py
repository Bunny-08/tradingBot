import os
import logging
from flask import Flask, render_template, request, flash
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "trading_bot_secret"

if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger()

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi/v1'

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        try:
            symbol = symbol.strip().upper()
            side = side.strip().upper()
            
            params = {
                "symbol": symbol,
                "side": side,
                "quantity": float(quantity)
            }

            if order_type == "MARKET":
                params["type"] = "MARKET"
            
            elif order_type == "LIMIT":
                params.update({
                    "type": "LIMIT",
                    "price": str(price),
                    "timeInForce": "GTC"
                })
            
            elif order_type == "STOP-LIMIT":
                params.update({
                    "type": "STOP",
                    "stopPrice": str(stop_price),
                    "price": str(price),
                    "timeInForce": "GTC"
                })

            logger.info(f"Request: {params}")
            res = self.client.futures_create_order(**params)
            logger.info(f"Response: {res}")
            return {"status": "success", "data": res}

        except (BinanceAPIException, BinanceOrderException) as e:
            logger.error(f"API Error: {e.message}")
            return {"status": "error", "message": e.message}
        except Exception as e:
            logger.error(f"System Error: {str(e)}")
            return {"status": "error", "message": str(e)}

bot = BasicBot(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        side = request.form.get("side")
        order_type = request.form.get("order_type")
        quantity = request.form.get("quantity")
        price = request.form.get("price")
        stop_price = request.form.get("stop_price")

        result = bot.place_order(symbol, side, order_type, quantity, price, stop_price)
        
        if result["status"] == "success":
            flash(f"Order Success: {result['data']['orderId']}", "success")
        else:
            flash(f"Order Failed: {result['message']}", "danger")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)