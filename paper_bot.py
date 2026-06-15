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
PAPER_MODE           = True   # Set to False for live trading
INITIAL_BALANCE      = 10000  # Starting balance in USDT
MAX_POSITION_SIZE    = 1000   # Max $ per trade
MAX_POSITIONS        = 3      # Max open positions at once
LOOP_INTERVAL        = 60     # Seconds between scans

RSI_OVERSOLD         = 30
RSI_OVERBOUGHT       = 70
RSI_PERIOD           = 14

BASE_URL = "https://fapi.bitunix.com/openApi/v2"


# ================= PAPER TRADING STATE =================
paper_balance    = INITIAL_BALANCE
paper_positions  = {}   # { symbol: {"side": "LONG"|"SHORT", "qty": float, "entry": float} }
paper_orders     = []   # history
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
        logger.error(f"❌ Instruments: {result.get('msg')}")
        return []
    except Exception as e:
        logger.error(f"❌ get_futures_coins: {e}")
        return []


def get_current_price(symbol):
    if PAPER_MODE:
        if symbol not in simulated_prices:
            defaults = {
                "BTCUSDT": 65000, "ETHUSDT": 3500, "SOLUSDT": 150,
                "XRPUSDT": 0.55,  "ADAUSDT": 0.45, "DOGEUSDT": 0.13,
                "AVAXUSDT": 35,   "TRXUSDT": 0.12, "DOTUSDT": 7.5,
                "MATICUSDT": 0.9, "LINKUSDT": 15,  "UNIUSDT": 8,
            }
            simulated_prices[symbol] = defaults.get(symbol, random.uniform(1, 100))
        # Simulate small random walk each call
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
    return simulated_prices.get(symbol, 100.0)


def get_historical_closes(symbol, interval="1m", limit=100):
    if PAPER_MODE:
        base = get_current_price(symbol)
        closes = []
        for _ in range(limit):
            base *= random.uniform(0.995, 1.005)
            closes.append(base)
        return closes
    try:
        r = requests.get(
            f"{BASE_URL}/market/kline",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10,
        )
        result = r.json()
        if result.get("code") == "0":
            return [float(c["close"]) for c in result.get("data", [])]
    except Exception as e:
        logger.error(f"❌ get_historical_closes({symbol}): {e}")
    return []


# ================= TECHNICAL ANALYSIS =================
def calculate_rsi(closes, period=RSI_PERIOD):
    """Wilder RSI from a list of close prices."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period + 1, len(closes)):
        diff = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(diff, 0))  / period
        avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


# ================= PAPER TRADING EXECUTION =================
def paper_open_long(symbol, usdt_size):
    global paper_balance
    if symbol in paper_positions:
        logger.info(f"⏭  Already in position: {symbol}")
        return
    if len(paper_positions) >= MAX_POSITIONS:
        logger.info(f"⏭  Max positions ({MAX_POSITIONS}) reached")
        return
    size  = min(usdt_size, MAX_POSITION_SIZE, paper_balance * 0.95)
    price = get_current_price(symbol)
    qty   = size / price
    paper_balance -= size
    paper_positions[symbol] = {"side": "LONG", "qty": qty, "entry": price, "size": size}
    paper_orders.append({"action": "OPEN LONG", "symbol": symbol, "qty": qty,
                          "price": price, "time": time.strftime("%H:%M:%S")})
    logger.info(f"🟢 [PAPER] LONG  {symbol}  qty={qty:.6f}  entry=${price:.4f}  cost=${size:.2f}")


def paper_open_short(symbol, usdt_size):
    global paper_balance
    if symbol in paper_positions:
        logger.info(f"⏭  Already in position: {symbol}")
        return
    if len(paper_positions) >= MAX_POSITIONS:
        logger.info(f"⏭  Max positions ({MAX_POSITIONS}) reached")
        return
    size  = min(usdt_size, MAX_POSITION_SIZE, paper_balance * 0.95)
    price = get_current_price(symbol)
    qty   = size / price
    paper_balance -= size
    paper_positions[symbol] = {"side": "SHORT", "qty": qty, "entry": price, "size": size}
    paper_orders.append({"action": "OPEN SHORT", "symbol": symbol, "qty": qty,
                          "price": price, "time": time.strftime("%H:%M:%S")})
    logger.info(f"🔴 [PAPER] SHORT {symbol}  qty={qty:.6f}  entry=${price:.4f}  cost=${size:.2f}")


def paper_close(symbol):
    global paper_balance
    if symbol not in paper_positions:
        return
    pos   = paper_positions.pop(symbol)
    price = get_current_price(symbol)
    qty   = pos["qty"]
    side  = pos["side"]
    entry = pos["entry"]
    if side == "LONG":
        pnl = (price - entry) * qty
    else:
        pnl = (entry - price) * qty
    returned = pos["size"] + pnl
    paper_balance += returned
    paper_orders.append({"action": f"CLOSE {side}", "symbol": symbol, "qty": qty,
                          "price": price, "pnl": pnl, "time": time.strftime("%H:%M:%S")})
    emoji = "✅" if pnl >= 0 else "🔻"
    logger.info(f"{emoji} [PAPER] CLOSE {side} {symbol}  exit=${price:.4f}  PnL=${pnl:+.2f}")


# ================= STRATEGY =================
def run_strategy(symbol):
    """RSI mean-reversion strategy with SMA trend filter."""
    closes = get_historical_closes(symbol, limit=RSI_PERIOD + 20)
    if not closes:
        return

    rsi  = calculate_rsi(closes)
    sma  = calculate_sma(closes, 20)
    price = closes[-1]

    if rsi is None or sma is None:
        return

    in_position = symbol in paper_positions

    # ── Exit logic ──────────────────────────────────────────────────────────
    if in_position:
        pos  = paper_positions[symbol]
        side = pos["side"]
        entry = pos["entry"]
        pnl_pct = ((price - entry) / entry) * (1 if side == "LONG" else -1) * 100

        # Stop-loss at -2%, take-profit at +3%
        if pnl_pct <= -2.0:
            logger.info(f"🛑 Stop-loss hit for {symbol}  PnL={pnl_pct:.2f}%")
            paper_close(symbol)
            return
        if pnl_pct >= 3.0:
            logger.info(f"🎯 Take-profit hit for {symbol}  PnL={pnl_pct:.2f}%")
            paper_close(symbol)
            return
        # RSI reversal exit
        if side == "LONG"  and rsi >= RSI_OVERBOUGHT:
            logger.info(f"📤 RSI exit LONG  {symbol}  RSI={rsi}")
            paper_close(symbol)
        if side == "SHORT" and rsi <= RSI_OVERSOLD:
            logger.info(f"📤 RSI exit SHORT {symbol}  RSI={rsi}")
            paper_close(symbol)
        return

    # ── Entry logic ─────────────────────────────────────────────────────────
    if rsi <= RSI_OVERSOLD and price > sma:
        logger.info(f"📈 BUY signal  {symbol}  RSI={rsi}  price={price:.4f} > SMA={sma:.4f}")
        paper_open_long(symbol, MAX_POSITION_SIZE)
    elif rsi >= RSI_OVERBOUGHT and price < sma:
        logger.info(f"📉 SELL signal {symbol}  RSI={rsi}  price={price:.4f} < SMA={sma:.4f}")
        paper_open_short(symbol, MAX_POSITION_SIZE)


# ================= STATUS REPORT =================
def print_status(coins):
    total_unrealized = 0.0
    for sym, pos in paper_positions.items():
        price = get_current_price(sym)
        if pos["side"] == "LONG":
            upnl = (price - pos["entry"]) * pos["qty"]
        else:
            upnl = (pos["entry"] - price) * pos["qty"]
        total_unrealized += upnl

    equity = paper_balance + sum(p["size"] for p in paper_positions.values()) + total_unrealized
    pnl    = equity - INITIAL_BALANCE

    print("\n" + "=" * 55)
    print(f"  Balance   : ${paper_balance:>10.2f} USDT")
    print(f"  Unrealized: ${total_unrealized:>+10.2f} USDT")
    print(f"  Equity    : ${equity:>10.2f} USDT")
    print(f"  Total PnL : ${pnl:>+10.2f} USDT  ({pnl/INITIAL_BALANCE*100:+.2f}%)")
    print(f"  Positions : {len(paper_positions)}/{MAX_POSITIONS}")
    for sym, pos in paper_positions.items():
        price = get_current_price(sym)
        upnl  = (price - pos["entry"]) * pos["qty"] * (1 if pos["side"] == "LONG" else -1)
        print(f"    {pos['side']:5s} {sym:12s}  entry=${pos['entry']:.4f}  now=${price:.4f}  uPnL=${upnl:+.2f}")
    print(f"  Coins scanned: {len(coins)}")
    print("=" * 55 + "\n")


# ================= MAIN LOOP =================
if __name__ == "__main__":
    mode = "PAPER" if PAPER_MODE else "LIVE"
    print("=" * 55)
    print(f"  BITUNIX RSI BOT — {mode} MODE")
    print(f"  Balance: ${INITIAL_BALANCE:,.2f}  |  Max positions: {MAX_POSITIONS}")
    print(f"  RSI period: {RSI_PERIOD}  oversold: {RSI_OVERSOLD}  overbought: {RSI_OVERBOUGHT}")
    print("=" * 55)

    coins = get_futures_coins()
    logger.info(f"Scanning {len(coins)} coins every {LOOP_INTERVAL}s ...")

    iteration = 0
    while True:
        iteration += 1
        logger.info(f"── Scan #{iteration} ──────────────────────────────────")
        for symbol in coins:
            try:
                run_strategy(symbol)
            except Exception as e:
                logger.error(f"❌ Strategy error for {symbol}: {e}")

        if iteration % 5 == 0:
            print_status(coins)

        time.sleep(LOOP_INTERVAL)
