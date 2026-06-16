import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
raise ValueError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")

client = TradingClient(API_KEY, SECRET_KEY, paper=True)

def main():
account = client.get_account()
print(f"Connected. Buying power: {account.buying_power}")

order = MarketOrderRequest(
symbol="AAPL",
qty=1,
side=OrderSide.BUY,
time_in_force=TimeInForce.DAY,
)

submitted = client.submit_order(order_data=order)
print("Paper order submitted:")
print(submitted)

if __name__ == "__main__":
main()
