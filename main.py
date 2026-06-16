import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    OptionOrderRequest,
    ClosePositionRequest,
)
from alpaca.trading.enums import (
    OrderSide,
    TimeInForce,
    OrderType,
    ContractType,
    AssetStatus,
)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import date, timedelta, datetime, timezone
import time

load_dotenv()

API_KEY = os.getenv("PK4MDBGUZXZ7CA62KEP3ZLYIQ3")
SECRET_KEY = os.getenv("ESphvpJABpMxkvib4qp9aqtS1BSPmDzoCURmAU4gRbiN")

if not API_KEY or not SECRET_KEY:
    raise ValueError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in
