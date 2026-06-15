import time
import logging
import random
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================= CONFIGURATION =================
PAPER_MODE        = True   # Set to False for live trading
INITIAL_BALANCE   = 10000  # Starting balance in USDT
MAX_POSITION_SIZE = 50     # Max $ per trade
MAX_POSITIONS     = 3      # Max open positions at once
LOOP_INTERVAL     = 60     # Seconds between auto-scans

RSI_OVERSOLD      = 30
RSI_OVERBOUGHT    = 70
RSI_PERIOD        = 14

BASE_URL = "https://fapi.bitunix.com/openApi/v2"

# ================= PAPER TRADING STATE =================
paper_balance    = float(INITIAL_BALANCE)
paper_positions  = {}   # { symbol: {side, qty, entry_price} }
paper_orders     = []
simulated_prices = {}


# ================= MARKET DATA =================
def get_futures_coins():
    if PAPER_MODE:
        return [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT",
            "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "TRXUSDT",
            "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT",
        ]
    try:
        r = requests.get(f"{BASE_URL}/market/instruments", timeout=10)
        result = r.json()
        if result.get("code") == "0":
            coins = [i["symbol"] for i in result.get("data", [])
                     if i.get("status") == "TRADING" and i.get("symbol")]
            logger.info(f"✅ Found {len(coins)} futures coins")
            return coins
        logger.error(f"❌ Instruments error: {result.get('msg')}")
        return []
    except Exception as e:
        logger.error(f"❌ get_futures_coins: {e}")
        return []


def get_current_price(symbol):
    _DEFAULTS = {
        "BTCUSDT": 65000, "ETHUSDT": 3500, "SOLUSDT": 150,
        "XRPUSDT": 0.55,  "ADAUSDT": 0.45, "DOGEUSDT": 0.13,
        "AVAXUSDT": 35,   "TRXUSDT": 0.12, "DOTUSDT": 7.5,
        "MATICUSDT": 0.9, "LINKUSDT": 15,  "UNIUSDT": 8,
    }
    if PAPER_MODE:
        if symbol not in simulated_prices:
            simulated_prices[symbol] = _DEFAULTS.get(symbol, random.uniform(1, 100))
        simulated_prices[symbol] *= random.uniform(0.998, 1.002)
        return simulated_prices[symbol]
    try:
        r = requests.get(f"{BASE_URL}/market/ticker", params={"symbol": symbol}, timeout=10)
        result = r.json()
        if result.get("code") == "0":
            price = float(result["data"]["lastPrice"])
            simulated_prices[symbol] = price
            return price
    except Exception as e:
        logger.error(f"❌ get_current_price({symbol}): {e}")
    return simulated_prices.get(symbol, _DEFAULTS.get(symbol, 100.0))


def get_historical_data(symbol, interval="1m", limit=100):
    if PAPER_MODE:
        base = get_current_price(symbol)
        closes = []
        for _ in range(limit):
            base *= random.uniform(0.995, 1.005)
            closes.append({"close": base, "high": base * 1.01,
                            "low": base * 0.99, "volume": random.uniform(100, 10000)})
        return closes
    try:
        r = requests.get(
            f"{BASE_URL}/market/kline",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10,
        )
        result = r.json()
        if result.get("code") == "0":
            return result.get("data", [])
    except Exception as e:
        logger.error(f"❌ get_historical_data({symbol}): {e}")
    return []


# ================= TECHNICAL ANALYSIS =================
def calculate_rsi(closes, period=RSI_PERIOD):
    if len(closes) < period + 1:
        return 50.0  # neutral default
    changes  = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains    = [c if c > 0 else 0.0 for c in changes]
    losses   = [abs(c) if c < 0 else 0.0 for c in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_macd(closes, fast=12, slow=26, signal_period=9):
    if len(closes) < slow + signal_period:
        return 0.0, 0.0, 0.0

    def ema(prices, span):
        k, val = 2 / (span + 1), prices[0]
        for p in prices[1:]:
            val = p * k + val * (1 - k)
        return val

    macd_line   = ema(closes, fast) - ema(closes, slow)
    # Build MACD series for signal EMA (simplified: use last slow+signal candles)
    macd_series = []
    for i in range(slow, len(closes)):
        macd_series.append(ema(closes[:i + 1], fast) - ema(closes[:i + 1], slow))
    signal_line = ema(macd_series, signal_period) if len(macd_series) >= signal_period else macd_line
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze_symbol(symbol):
    try:
        data = get_historical_data(symbol, interval="1m", limit=100)
        if not data:
            return {"symbol": symbol, "signal": "HOLD", "reason": "No data"}

        closes = [float(d.get("close", 100)) for d in data]
        rsi    = calculate_rsi(closes, RSI_PERIOD)
        macd_line, sig_line, histogram = calculate_macd(closes)
        price  = get_current_price(symbol)

        trade_signal = "HOLD"
        reason       = ""

        if rsi < RSI_OVERSOLD:
            trade_signal = "LONG"
            reason       = f"RSI oversold ({rsi:.1f})"
            if histogram > 0:
                reason += " + MACD bullish"
        elif rsi > RSI_OVERBOUGHT:
            trade_signal = "SHORT"
            reason       = f"RSI overbought ({rsi:.1f})"
            if histogram < 0:
                reason += " + MACD bearish"

        return {
            "symbol": symbol, "price": price,
            "rsi": rsi, "macd": macd_line,
            "histogram": histogram,
            "signal": trade_signal, "reason": reason,
        }
    except Exception as e:
        logger.error(f"❌ analyze_symbol({symbol}): {e}")
        return {"symbol": symbol, "signal": "HOLD", "reason": str(e)}


# ================= PAPER TRADING ENGINE =================
def _paper_order(symbol, qty, side, trade_side):
    global paper_balance
    price = get_current_price(symbol)
    pnl   = 0.0

    if trade_side == "OPEN":
        cost = qty  # qty is in USDT for simplicity
        if paper_balance < cost:
            logger.warning(f"⚠️  Insufficient balance (${paper_balance:.2f}) for ${cost:.2f} trade")
            return {"code": "ERR", "error": "Insufficient balance"}

        if symbol in paper_positions:
            pos = paper_positions[symbol]
            if pos["side"] == side:
                # Add to existing position
                total_cost  = pos["qty"] * pos["entry_price"] + cost
                pos["qty"]  += cost / price
                pos["entry_price"] = total_cost / pos["qty"]
                paper_balance -= cost
                logger.info(f"📈 Added to {side} {symbol}  new avg=${pos['entry_price']:.4f}")
            else:
                # Reverse position
                paper_close_internal(symbol)
                paper_balance -= cost
                paper_positions[symbol] = {"side": side, "qty": cost / price, "entry_price": price}
                logger.info(f"🔄 Reversed {symbol} to {side}  qty={cost/price:.6f}")
        else:
            paper_balance -= cost
            paper_positions[symbol] = {"side": side, "qty": cost / price, "entry_price": price}
            logger.info(f"🟢 OPEN {side} {symbol}  qty={cost/price:.6f}  entry=${price:.4f}  cost=${cost:.2f}")

    elif trade_side == "CLOSE":
        if symbol not in paper_positions:
            logger.warning(f"⚠️  No position to close for {symbol}")
            return {"code": "ERR", "error": "No position"}
        pnl = paper_close_internal(symbol, close_qty=qty / price if qty else None)

    order = {
        "id": len(paper_orders) + 1,
        "symbol": symbol, "side": side, "tradeSide": trade_side,
        "qty": qty, "price": price, "pnl": pnl,
        "timestamp": time.strftime("%H:%M:%S"), "status": "FILLED",
    }
    paper_orders.append(order)
    return {"code": "0", "data": order, "simulated": True, "pnl": pnl}


def paper_close_internal(symbol, close_qty=None):
    """Close (part of) a position and credit balance. Returns realized PnL."""
    global paper_balance
    if symbol not in paper_positions:
        return 0.0
    pos   = paper_positions[symbol]
    price = get_current_price(symbol)
    qty   = close_qty if close_qty and close_qty < pos["qty"] else pos["qty"]

    if pos["side"] == "BUY":
        pnl = (price - pos["entry_price"]) * qty
    else:
        pnl = (pos["entry_price"] - price) * qty

    returned = qty * pos["entry_price"] + pnl   # original cost + profit
    paper_balance += returned
    emoji = "✅" if pnl >= 0 else "🔻"
    logger.info(f"{emoji} CLOSE {pos['side']} {symbol}  qty={qty:.6f}  exit=${price:.4f}  PnL=${pnl:+.2f}")

    pos["qty"] -= qty
    if pos["qty"] <= 1e-9:
        del paper_positions[symbol]
    return pnl


# ================= PUBLIC TRADING FUNCTIONS =================
def long(symbol, qty):
    if PAPER_MODE:
        logger.info(f"🟢 [PAPER] LONG {symbol} ${qty}")
        return _paper_order(symbol, qty, "BUY", "OPEN")
    # Live mode — delegates to bitunix_bot
    from bitunix_bot import long as _live_long
    return _live_long(symbol, str(qty))


def short(symbol, qty):
    if PAPER_MODE:
        logger.info(f"🔴 [PAPER] SHORT {symbol} ${qty}")
        return _paper_order(symbol, qty, "SELL", "OPEN")
    from bitunix_bot import short as _live_short
    return _live_short(symbol, str(qty))


def close_long(symbol, qty=None):
    if PAPER_MODE:
        logger.info(f"🔚 [PAPER] Close LONG {symbol}")
        return _paper_order(symbol, qty or 0, "SELL", "CLOSE")
    from bitunix_bot import close_long as _live_cl
    return _live_cl(symbol, str(qty or 0))


def close_short(symbol, qty=None):
    if PAPER_MODE:
        logger.info(f"🔚 [PAPER] Close SHORT {symbol}")
        return _paper_order(symbol, qty or 0, "BUY", "CLOSE")
    from bitunix_bot import close_short as _live_cs
    return _live_cs(symbol, str(qty or 0))


def close_position(symbol, qty=None):
    if symbol in paper_positions:
        side = paper_positions[symbol]["side"]
        return close_long(symbol, qty) if side == "BUY" else close_short(symbol, qty)
    logger.warning(f"⚠️  No open position for {symbol}")
    return {"code": "ERR", "error": "No position"}


# ================= ACCOUNT INFO =================
def get_balance():
    if PAPER_MODE:
        upnl = 0.0
        for sym, pos in paper_positions.items():
            price = get_current_price(sym)
            if pos["side"] == "BUY":
                upnl += (price - pos["entry_price"]) * pos["qty"]
            else:
                upnl += (pos["entry_price"] - price) * pos["qty"]
        return {
            "code": "0",
            "data": {"balance": paper_balance, "unrealized_pnl": upnl,
                     "total": paper_balance + upnl},
            "simulated": True,
        }
    from bitunix_bot import get_balance as _live_bal
    return _live_bal()


def get_positions():
    if PAPER_MODE:
        return {
            "code": "0",
            "data": [{"symbol": s, "side": pos["side"],
                       "qty": pos["qty"], "entryPrice": pos["entry_price"]}
                     for s, pos in paper_positions.items()],
            "simulated": True,
        }
    from bitunix_bot import get_positions as _live_pos
    return _live_pos()


# ================= AUTO STRATEGY =================
def run_auto_strategy():
    print("=" * 60)
    print("AUTO TRADING STRATEGY — SCANNING FUTURES COINS")
    print("=" * 60)

    coins   = get_futures_coins()
    signals = []

    print(f"\n📊 Scanning {len(coins)} coins...")
    for coin in coins:
        analysis = analyze_symbol(coin)
        signals.append(analysis)
        if analysis["signal"] != "HOLD":
            print(f"  {analysis['symbol']:12s} {analysis['signal']:5s}  RSI={analysis['rsi']:.1f}  {analysis['reason']}")

    long_signals  = sorted([s for s in signals if s["signal"] == "LONG"],  key=lambda x: x["rsi"])
    short_signals = sorted([s for s in signals if s["signal"] == "SHORT"], key=lambda x: x["rsi"], reverse=True)
    print(f"\n💡 {len(long_signals)} LONG  |  {len(short_signals)} SHORT opportunities")

    trades = 0
    for sig in long_signals:
        if trades >= MAX_POSITIONS or len(paper_positions) >= MAX_POSITIONS:
            break
        if sig["symbol"] not in paper_positions:
            qty = min(MAX_POSITION_SIZE, paper_balance * 0.05)
            print(f"\n🟢 LONG  {sig['symbol']}  ${qty:.2f}  —  {sig['reason']}")
            long(sig["symbol"], qty)
            trades += 1

    for sig in short_signals:
        if trades >= MAX_POSITIONS or len(paper_positions) >= MAX_POSITIONS:
            break
        if sig["symbol"] not in paper_positions:
            qty = min(MAX_POSITION_SIZE, paper_balance * 0.05)
            print(f"\n🔴 SHORT {sig['symbol']}  ${qty:.2f}  —  {sig['reason']}")
            short(sig["symbol"], qty)
            trades += 1

    _print_status()


def _print_status():
    bal = get_balance()
    d   = bal["data"]
    pnl = d["total"] - INITIAL_BALANCE
    print("\n" + "=" * 60)
    print(f"  Balance    : ${d['balance']:>10.2f} USDT")
    print(f"  Unrealized : ${d['unrealized_pnl']:>+10.2f} USDT")
    print(f"  Equity     : ${d['total']:>10.2f} USDT")
    print(f"  Total PnL  : ${pnl:>+10.2f} USDT  ({pnl/INITIAL_BALANCE*100:+.2f}%)")
    print(f"  Positions  : {len(paper_positions)}/{MAX_POSITIONS}")
    for sym, pos in paper_positions.items():
        price = get_current_price(sym)
        upnl  = (price - pos["entry_price"]) * pos["qty"] * (1 if pos["side"] == "BUY" else -1)
        print(f"    {pos['side']:4s} {sym:12s}  entry=${pos['entry_price']:.4f}  now=${price:.4f}  uPnL=${upnl:+.2f}")
    print("=" * 60 + "\n")


def simulate_market_movement():
    for sym in list(simulated_prices):
        simulated_prices[sym] *= random.uniform(0.99, 1.01)


# ================= MAIN =================
if __name__ == "__main__":
    mode = "PAPER" if PAPER_MODE else "LIVE"
    print("=" * 60)
    print(f"  BITUNIX AUTO TRADING BOT — {mode} MODE")
    print(f"  Balance: ${INITIAL_BALANCE:,.2f}  |  Max positions: {MAX_POSITIONS}")
    print(f"  Max per trade: ${MAX_POSITION_SIZE}  |  RSI {RSI_OVERSOLD}/{RSI_OVERBOUGHT}")
    print("=" * 60 + "\n")

    # Initial scan
    run_auto_strategy()

    # Simulate 5 minutes of price movement then re-scan
    print("⏳ Simulating 5 minutes of market movement...")
    for _ in range(5):
        simulate_market_movement()
        time.sleep(1)

    print("\n🔄 Re-scanning markets after price movement...")
    run_auto_strategy()

    print("Auto trading complete!")
    print("Set LOOP_INTERVAL and wrap run_auto_strategy() in a while loop for continuous scanning.")
