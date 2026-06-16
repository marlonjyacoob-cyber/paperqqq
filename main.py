import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    MarketOrderRequest,
    OptionLegRequest,
)
from alpaca.trading.enums import (
    OrderSide,
    TimeInForce,
    OrderType,
    ContractType,
    AssetStatus,
    PositionIntent,
)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import date, timedelta, datetime, timezone
import time

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise ValueError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# ── CONFIG ────────────────────────────────────────────────────────────────────
MAX_SPEND   = 200.00
WATCHLIST   = ["SPY", "QQQ", "AAPL"]
EOD_HOUR    = 15
EOD_MINUTE  = 0
CHECK_EVERY = 60
# ─────────────────────────────────────────────────────────────────────────────


def get_account():
    account = trading_client.get_account()
    print(f"Connected. Buying power: ${float(account.buying_power):,.2f}")
    return account


def detect_momentum(symbol: str):
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=40)

    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    bars = data_client.get_stock_bars(req).df

    if bars.empty or len(bars) < 20:
        print(f"  [{symbol}] Not enough data for momentum check.")
        return None

    closes = bars["close"].values

    def ema(prices, period):
        k = 2 / (period + 1)
        result = [prices[0]]
        for p in prices[1:]:
            result.append(p * k + result[-1] * (1 - k))
        return result

    ema9  = ema(closes, 9)[-1]
    ema20 = ema(closes, 20)[-1]

    print(f"  [{symbol}] EMA9={ema9:.2f}  EMA20={ema20:.2f}", end="  →  ")

    if ema9 > ema20:
        print("UPTREND → BUY CALL")
        return "call"
    elif ema9 < ema20:
        print("DOWNTREND → BUY PUT")
        return "put"
    else:
        print("NO SIGNAL")
        return None


def find_affordable_contract(symbol: str, direction: str):
    today        = date.today()
    expiry_limit = today + timedelta(days=30)

    req = GetOptionContractsRequest(
        underlying_symbols=[symbol],
        expiration_date_gte=str(today),
        expiration_date_lte=str(expiry_limit),
        status=AssetStatus.ACTIVE,
        type=ContractType.CALL if direction == "call" else ContractType.PUT,
    )

    response  = trading_client.get_option_contracts(req)
    contracts = response.option_contracts

    if not contracts:
        print(f"  [{symbol}] No contracts found.")
        return None

    affordable = []
    for c in contracts:
        if c.ask_price is None:
            continue
        total_cost = float(c.ask_price) * 100
        if total_cost <= MAX_SPEND:
            affordable.append((c, total_cost))

    if not affordable:
        print(f"  [{symbol}] No contracts under ${MAX_SPEND}.")
        return None

    affordable.sort(key=lambda x: x[1])
    best, cost = affordable[0]

    print(f"  [{symbol}] Contract: {best.symbol} | "
          f"Strike: ${best.strike_price} | "
          f"Expiry: {best.expiration_date} | "
          f"Cost: ${cost:.2f}")
    return best


def place_option_order(contract_symbol: str):
    order_req = MarketOrderRequest(
        symbol=contract_symbol,
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        order_class="simple",
        legs=[
            OptionLegRequest(
                symbol=contract_symbol,
                side=OrderSide.BUY,
                position_intent=PositionIntent.BUY_TO_OPEN,
            )
        ],
    )
    submitted = trading_client.submit_order(order_req)
    print(f"  ✅ Order submitted → ID: {submitted.id} | Status: {submitted.status}")
    return submitted


def close_all_positions():
    positions = trading_client.get_all_positions()
    options   = [p for p in positions if len(p.symbol) > 6]

    if not options:
        print("  No open option positions to close.")
        return

    for p in options:
        try:
            trading_client.close_position(p.symbol)
            print(f"  🔴 Closed: {p.symbol} | P&L: ${float(p.unrealized_pl):+.2f}")
        except Exception as e:
            print(f"  ⚠️  Could not close {p.symbol}: {e}")


def is_eod() -> bool:
    now = datetime.now()
    return now.hour >= EOD_HOUR and now.minute >= EOD_MINUTE


def is_market_open() -> bool:
    clock = trading_client.get_clock()
    return clock.is_open


def main():
    print("=" * 55)
    print("   Alpaca Paper Options Bot — Momentum Strategy")
    print("=" * 55)

    get_account()

    traded_today = set()

    while True:
        now = datetime.now()
        print(f"\n[{now.strftime('%H:%M:%S')}] Checking market...")

        if is_eod():
            print("\n🔔 EOD reached — closing all positions.")
            close_all_positions()
            print("✅ Done for today. Bot shutting down.")
            break

        if not is_market_open():
            print("  Market is closed. Waiting...")
            time.sleep(CHECK_EVERY)
            continue

        for symbol in WATCHLIST:
            if symbol in traded_today:
                continue

            print(f"\nScanning {symbol}...")
            direction = detect_momentum(symbol)

            if direction is None:
                continue

            contract = find_affordable_contract(symbol, direction)
            if contract is None:
                continue

            place_option_order(contract.symbol)
            traded_today.add(symbol)

        print(f"\n  Sleeping {CHECK_EVERY}s before next check...")
        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    main()