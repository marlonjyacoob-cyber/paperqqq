import hashlib
import secrets
import base64
import time
import json
import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================= CONFIGURATION =================
API_KEY    = "cf0e6b74506af9e06dc052b331be6bab"
SECRET_KEY = "9ea21cf309c6f48262f0ddeb26fe6759"

BASE_URL = "https://fapi.bitunix.com/openApi/v2"


# ================= AUTHENTICATION =================
def _nonce() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()

def _sign(nonce: str, timestamp: str, query_string: str, body: str) -> str:
    # Bitunix double-SHA256: SHA256(SHA256(nonce+ts+key+qs+body) + secret)
    msg    = f"{nonce}{timestamp}{API_KEY}{query_string}{body}"
    digest = hashlib.sha256(msg.encode()).hexdigest()
    return hashlib.sha256((digest + SECRET_KEY).encode()).hexdigest()

def _build_headers(nonce: str, timestamp: str, sign: str) -> dict:
    return {
        "api-key":      API_KEY,
        "timestamp":    timestamp,
        "nonce":        nonce,
        "sign":         sign,
        "Content-Type": "application/json",
    }


# ================= HTTP HELPERS =================
def _post(path: str, payload: dict) -> dict:
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    body      = json.dumps(payload, separators=(",", ":"))
    sign      = _sign(nonce, timestamp, "", body)
    try:
        resp = requests.post(
            BASE_URL + path,
            headers=_build_headers(nonce, timestamp, sign),
            data=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out")
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return {"error": str(e)}

def _get(path: str, params: dict) -> dict:
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    qs        = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sign      = _sign(nonce, timestamp, qs, "")
    try:
        resp = requests.get(
            BASE_URL + path,
            headers=_build_headers(nonce, timestamp, sign),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out")
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return {"error": str(e)}


# ================= INTERNAL ORDER FUNCTION =================
def _order(symbol: str, qty, side: str, trade_side: str,
           order_type: str = "MARKET", price=None) -> dict:
    payload = {
        "symbol":    symbol,
        "qty":       str(qty),
        "side":      side,
        "tradeSide": trade_side,
        "orderType": order_type,
    }
    if order_type == "LIMIT" and price is not None:
        payload["price"]       = str(price)
        payload["timeInForce"] = "GTC"

    result = _post("/trade/order", payload)

    if result.get("code") not in (0, "0", None):
        logger.error(f"❌ Order failed: {result.get('msg', result)}")
    else:
        logger.info(f"✅ {side} {trade_side} {symbol} qty={qty} {order_type}")
    return result


# ================= TRADING FUNCTIONS =================
def long(symbol: str, qty, order_type: str = "MARKET", price=None) -> dict:
    """Open a LONG position (BUY to open)."""
    logger.info(f"🟢 Opening LONG  {symbol}  qty={qty}")
    return _order(symbol, qty, "BUY", "OPEN", order_type, price)

def short(symbol: str, qty, order_type: str = "MARKET", price=None) -> dict:
    """Open a SHORT position (SELL to open)."""
    logger.info(f"🔴 Opening SHORT {symbol}  qty={qty}")
    return _order(symbol, qty, "SELL", "OPEN", order_type, price)

def close_long(symbol: str, qty) -> dict:
    """Close a LONG position (SELL to close)."""
    logger.info(f"🔚 Closing LONG  {symbol}  qty={qty}")
    return _order(symbol, qty, "SELL", "CLOSE", "MARKET")

def close_short(symbol: str, qty) -> dict:
    """Close a SHORT position (BUY to close)."""
    logger.info(f"🔚 Closing SHORT {symbol}  qty={qty}")
    return _order(symbol, qty, "BUY", "CLOSE", "MARKET")

def close(symbol: str, qty) -> dict:
    """Alias: close a short (BUY to close). Use close_long() to close a long."""
    return close_short(symbol, qty)

def close_all(symbol: str) -> dict:
    """Flash-close every open position for a symbol."""
    logger.info(f"⚡ Closing ALL positions on {symbol}")
    result = _post("/trade/closeAll", {"symbol": symbol})
    if result.get("code") not in (0, "0", None):
        logger.error(f"❌ Close all failed: {result.get('msg', result)}")
    else:
        logger.info(f"✅ All positions closed on {symbol}")
    return result


# ================= ACCOUNT INFO =================
def get_balance() -> dict:
    """Get account balance."""
    logger.info("💰 Fetching balance...")
    result = _get("/account/balance", {})
    if result.get("code") not in (0, "0", None):
        logger.error(f"❌ Balance check failed: {result.get('msg', result)}")
    else:
        logger.info("✅ Balance retrieved")
    return result

def get_positions() -> dict:
    """Get all open positions."""
    logger.info("📊 Fetching positions...")
    result = _get("/account/positions", {})
    if result.get("code") not in (0, "0", None):
        logger.error(f"❌ Positions check failed: {result.get('msg', result)}")
    else:
        count = len(result.get("data", []))
        logger.info(f"✅ Found {count} open position(s)")
    return result


# ================= USAGE EXAMPLE =================
if __name__ == "__main__":
    print("=" * 50)
    print("BITUNIX TRADING BOT")
    print("=" * 50)

    print("\n1. Checking balance...")
    balance = get_balance()
    print(f"   {balance}")

    print("\n2. Checking open positions...")
    positions = get_positions()
    print(f"   {positions}")

    # Uncomment to place real orders:
    # print("\n3. Open LONG BTCUSDT qty=0.001")
    # print(long("BTCUSDT", "0.001"))

    # print("\n4. Open SHORT ETHUSDT qty=0.01")
    # print(short("ETHUSDT", "0.01"))

    # time.sleep(5)

    # print("\n5. Close LONG BTCUSDT")
    # print(close_long("BTCUSDT", "0.001"))

    # print("\n6. Close SHORT ETHUSDT")
    # print(close_short("ETHUSDT", "0.01"))
