import requests
import hashlib
import secrets
import base64
import json
import time
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
BASE_URL   = "https://fapi.bitunix.com/openApi/v2"


# ================= AUTHENTICATION =================
def generate_signature(nonce, timestamp, query_string="", body=""):
    """
    Bitunix double-SHA256 signature:
      digest = SHA256(nonce + timestamp + api_key + query_string + body)
      sign   = SHA256(digest + secret_key)
    POST: query_string="", body=JSON string
    GET:  query_string=sorted URL params, body=""
    """
    digest = hashlib.sha256(
        (nonce + timestamp + API_KEY + query_string + body).encode("utf-8")
    ).hexdigest()
    return hashlib.sha256((digest + SECRET_KEY).encode("utf-8")).hexdigest()


def build_headers(nonce, timestamp, sign):
    return {
        "api-key":      API_KEY,
        "timestamp":    timestamp,
        "nonce":        nonce,
        "sign":         sign,
        "Content-Type": "application/json",
    }


def _nonce():
    # Cryptographically random — avoids collisions from timestamp-based nonces
    return base64.b64encode(secrets.token_bytes(32)).decode()


# ================= HELPER FUNCTIONS =================
def _post(path, payload):
    """Signed POST. Body is sent as the exact JSON string that was signed."""
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    # ✅ Sign and send the SAME bytes — never let requests re-serialize
    body      = json.dumps(payload, separators=(",", ":"))
    sign      = generate_signature(nonce, timestamp, query_string="", body=body)
    try:
        response = requests.post(
            BASE_URL + path,
            headers=build_headers(nonce, timestamp, sign),
            data=body,          # raw string, not json=payload
            timeout=10,
        )
        result = response.json()
        if result.get("code") not in (0, "0"):
            logger.error(f"❌ POST {path} failed: {result.get('msg', result.get('errorMessage', result))}")
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"error": str(e)}


def _get(path, params=None):
    """Signed GET. Query params are sorted then signed as query_string."""
    params    = params or {}
    timestamp = str(int(time.time() * 1000))
    nonce     = _nonce()
    qs        = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sign      = generate_signature(nonce, timestamp, query_string=qs, body="")
    try:
        response = requests.get(
            BASE_URL + "/" + path.lstrip("/"),
            headers=build_headers(nonce, timestamp, sign),
            params=params,
            timeout=10,
        )
        result = response.json()
        if result.get("code") not in (0, "0"):
            logger.error(f"❌ GET {path} failed: {result.get('msg', result.get('errorMessage', result))}")
        else:
            logger.info(f"✅ GET {path} successful")
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
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
    logger.info(f"🟢 LONG  {symbol}  qty={qty}")
    return _place_order(symbol, qty, "BUY", "OPEN", order_type, price)


def short(symbol, qty, order_type="MARKET", price=None):
    logger.info(f"🔴 SHORT {symbol}  qty={qty}")
    return _place_order(symbol, qty, "SELL", "OPEN", order_type, price)


def close_long(symbol, qty):
    logger.info(f"🔚 Close LONG  {symbol}  qty={qty}")
    return _place_order(symbol, qty, "SELL", "CLOSE", "MARKET")


def close_short(symbol, qty):
    logger.info(f"🔚 Close SHORT {symbol}  qty={qty}")
    return _place_order(symbol, qty, "BUY", "CLOSE", "MARKET")


def close(symbol, qty):
    """Alias for close_short()."""
    return close_short(symbol, qty)


def close_all(symbol):
    logger.info(f"⚡ Close ALL {symbol}")
    result = _post("/trade/closeAll", {"symbol": symbol})
    if result.get("code") in (0, "0"):
        logger.info(f"✅ All positions closed on {symbol}")
    return result


# ================= ACCOUNT INFO =================
def get_balance():
    logger.info("💰 Checking balance...")
    return _get("account/balance")


def get_positions():
    logger.info("📊 Checking positions...")
    return _get("account/positions")


# ================= MAIN =================
if __name__ == "__main__":
    print("=" * 50)
    print("BITUNIX TRADING BOT")
    print("=" * 50)

    print("\n1. Balance:")
    print(get_balance())

    print("\n2. Positions:")
    print(get_positions())

    # === LIVE TRADING (uncomment, start small!) ===
    # print("\n3. LONG BTCUSDT qty=0.001:")
    # print(long("BTCUSDT", "0.001"))

    # print("\n4. SHORT ETHUSDT qty=0.01:")
    # print(short("ETHUSDT", "0.01"))

    # time.sleep(30)

    # print("\n5. Close LONG BTCUSDT:")
    # print(close_long("BTCUSDT", "0.001"))

    # print("\n6. Close SHORT ETHUSDT:")
    # print(close_short("ETHUSDT", "0.01"))

    print("\n" + "=" * 50)
    print("Done.")
    print("=" * 50)
