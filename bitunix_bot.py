import requests
import hashlib
import secrets
import base64
import time
import json
import logging

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
def generate_signature(nonce, timestamp, query_string="", body=""):
    """
    Bitunix double-SHA256 signature.
      digest = SHA256(nonce + timestamp + api_key + query_string + body)
      sign   = SHA256(digest + secret_key)
    For POST requests: query_string="" and body=JSON string.
    For GET  requests: query_string=URL-encoded params and body="".
    """
    digest = hashlib.sha256(
        (nonce + timestamp + API_KEY + query_string + body).encode()
    ).hexdigest()
    return hashlib.sha256((digest + SECRET_KEY).encode()).hexdigest()


def _nonce():
    return base64.b64encode(secrets.token_bytes(32)).decode()


def _base_headers(nonce, timestamp, sign):
    return {
        "api-key":      API_KEY,
        "timestamp":    timestamp,
        "nonce":        nonce,
        "sign":         sign,
        "Content-Type": "application/json",
    }


# ================= HELPER FUNCTIONS =================
def _post(path, payload):
    """Signed POST request. Body is JSON; query_string is empty."""
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    body      = json.dumps(payload, separators=(",", ":"))
    sign      = generate_signature(nonce, timestamp, query_string="", body=body)
    try:
        response = requests.post(
            BASE_URL + path,
            headers=_base_headers(nonce, timestamp, sign),
            data=body,
            timeout=10,
        )
        result = response.json()
        if result.get("code") not in (0, "0"):
            logger.error(f"❌ POST {path} failed: {result.get('msg', result)}")
        return result
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out")
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return {"error": str(e)}


def _get(path, params=None):
    """Signed GET request. Params go in URL; query_string is used for signing."""
    params    = params or {}
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    qs        = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sign      = generate_signature(nonce, timestamp, query_string=qs, body="")
    try:
        response = requests.get(
            BASE_URL + path,
            headers=_base_headers(nonce, timestamp, sign),
            params=params,
            timeout=10,
        )
        result = response.json()
        if result.get("code") not in (0, "0"):
            logger.error(f"❌ GET {path} failed: {result.get('msg', result)}")
        else:
            logger.info(f"✅ GET {path} successful")
        return result
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out")
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return {"error": str(e)}


def _place_order(symbol, qty, side, trade_side, order_type="MARKET", price=None):
    payload = {
        "symbol":    symbol,
        "side":      side,
        "orderType": order_type,
        "qty":       str(qty),
        "tradeSide": trade_side,
    }
    if order_type == "LIMIT" and price is not None:
        payload["price"]       = str(price)
        payload["timeInForce"] = "GTC"

    result = _post("/trade/order", payload)
    if result.get("code") in (0, "0"):
        logger.info(f"✅ {side} {trade_side} {symbol} qty={qty} {order_type}")
    return result


# ================= TRADING FUNCTIONS =================
def long(symbol, qty, order_type="MARKET", price=None):
    """Open a LONG position (BUY to open)."""
    logger.info(f"🟢 Opening LONG  {symbol}  qty={qty}")
    return _place_order(symbol, qty, "BUY", "OPEN", order_type, price)


def short(symbol, qty, order_type="MARKET", price=None):
    """Open a SHORT position (SELL to open)."""
    logger.info(f"🔴 Opening SHORT {symbol}  qty={qty}")
    return _place_order(symbol, qty, "SELL", "OPEN", order_type, price)


def close_long(symbol, qty):
    """Close a LONG position (SELL to close)."""
    logger.info(f"🔚 Closing LONG  {symbol}  qty={qty}")
    return _place_order(symbol, qty, "SELL", "CLOSE", "MARKET")


def close_short(symbol, qty):
    """Close a SHORT position (BUY to close)."""
    logger.info(f"🔚 Closing SHORT {symbol}  qty={qty}")
    return _place_order(symbol, qty, "BUY", "CLOSE", "MARKET")


def close(symbol, qty):
    """Alias for close_short() — BUY to close a short."""
    return close_short(symbol, qty)


def close_all(symbol):
    """Flash-close every open position for a symbol."""
    logger.info(f"⚡ Closing ALL positions on {symbol}")
    result = _post("/trade/closeAll", {"symbol": symbol})
    if result.get("code") in (0, "0"):
        logger.info(f"✅ All positions closed on {symbol}")
    return result


# ================= ACCOUNT INFO =================
def get_balance():
    """Get account balance."""
    logger.info("💰 Checking balance...")
    return _get("/account/balance")


def get_positions():
    """Get open positions."""
    logger.info("📊 Checking positions...")
    result = _get("/account/positions")
    if result.get("code") in (0, "0"):
        count = len(result.get("data", []))
        logger.info(f"   {count} open position(s)")
    return result


# ================= USAGE EXAMPLE =================
if __name__ == "__main__":
    print("=" * 50)
    print("BITUNIX TRADING BOT - TEST MODE")
    print("=" * 50)

    # Check balance first
    print("\n1. Checking balance...")
    balance = get_balance()
    print(f"   {balance}")

    # Check positions
    print("\n2. Checking positions...")
    positions = get_positions()
    print(f"   {positions}")

    # === LIVE ORDERS — uncomment when ready (start small!) ===
    # print("\n3. Testing LONG on BTCUSDT (qty=0.001)...")
    # print(long("BTCUSDT", "0.001"))

    # print("\n4. Testing SHORT on ETHUSDT (qty=0.01)...")
    # print(short("ETHUSDT", "0.01"))

    # time.sleep(30)

    # print("\n5. Closing LONG on BTCUSDT...")
    # print(close_long("BTCUSDT", "0.001"))

    # print("\n6. Closing SHORT on ETHUSDT...")
    # print(close_short("ETHUSDT", "0.01"))

    print("\n" + "=" * 50)
    print("DONE! Uncomment live orders to trade.")
    print("=" * 50)
