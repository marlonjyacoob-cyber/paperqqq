import hashlib
import secrets
import base64
import time
import json
import requests

# ── API Credentials ───────────────────────────────────────────────────────────
API_KEY    = "cf0e6b74506af9e06dc052b331be6bab"
SECRET_KEY = "9ea21cf309c6f48262f0ddeb26fe6759"

BASE_URL = "https://fapi.bitunix.com"

# ── Auth helpers ──────────────────────────────────────────────────────────────

def _nonce() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()

def _sign(nonce: str, timestamp: str, query_string: str, body: str) -> str:
    # Step 1: SHA256( nonce + timestamp + api_key + query_string + body )
    msg     = f"{nonce}{timestamp}{API_KEY}{query_string}{body}"
    digest  = hashlib.sha256(msg.encode()).hexdigest()
    # Step 2: SHA256( digest + secret_key )
    return hashlib.sha256((digest + SECRET_KEY).encode()).hexdigest()

def _headers(nonce: str, timestamp: str, sign: str) -> dict:
    return {
        "api-key":      API_KEY,
        "timestamp":    timestamp,
        "nonce":        nonce,
        "sign":         sign,
        "Content-Type": "application/json",
    }

def _post(path: str, payload: dict) -> dict:
    timestamp    = str(int(time.time() * 1000))
    nonce        = _nonce()
    body         = json.dumps(payload, separators=(",", ":"))
    sign         = _sign(nonce, timestamp, "", body)
    url          = BASE_URL + path
    resp         = requests.post(url, headers=_headers(nonce, timestamp, sign), data=body, timeout=10)
    resp.raise_for_status()
    return resp.json()

# ── Core trading functions ────────────────────────────────────────────────────

def long(symbol: str, quantity: str):
    """Open a long position (market buy)."""
    print(f"[LONG]  {symbol}  qty={quantity}")
    payload = {
        "symbol":    symbol,
        "qty":       str(quantity),
        "side":      "BUY",
        "tradeSide": "OPEN",
        "orderType": "MARKET",
    }
    result = _post("/openApi/v2/mix/order/place", payload)
    print(f"[LONG]  response: {result}")
    return result

def short(symbol: str, quantity: str):
    """Open a short position (market sell)."""
    print(f"[SHORT] {symbol}  qty={quantity}")
    payload = {
        "symbol":    symbol,
        "qty":       str(quantity),
        "side":      "SELL",
        "tradeSide": "OPEN",
        "orderType": "MARKET",
    }
    result = _post("/openApi/v2/mix/order/place", payload)
    print(f"[SHORT] response: {result}")
    return result

def close(symbol: str, quantity: str):
    """Close an open position (market order, opposite side)."""
    print(f"[CLOSE] {symbol}  qty={quantity}")
    # Bitunix uses tradeSide=CLOSE to reduce/close a position.
    # The side must match the current holding direction; passing CLOSE
    # with a BUY closes a short, but to close either side without knowing
    # the current direction use the close-all endpoint if qty covers full size.
    payload = {
        "symbol":    symbol,
        "qty":       str(quantity),
        "side":      "BUY",       # BUY to close short; change to SELL to close long
        "tradeSide": "CLOSE",
        "orderType": "MARKET",
    }
    result = _post("/openApi/v2/mix/order/place", payload)
    print(f"[CLOSE] response: {result}")
    return result

# ── Optional: close all positions for a symbol ────────────────────────────────

def close_all(symbol: str):
    """Flash-close every open position on a symbol."""
    print(f"[CLOSE_ALL] {symbol}")
    payload = {"symbol": symbol}
    result  = _post("/openApi/v2/mix/order/closeAll", payload)
    print(f"[CLOSE_ALL] response: {result}")
    return result

# ── Quick test (comment out before live use) ──────────────────────────────────

if __name__ == "__main__":
    # Example usage – replace symbol and quantity with real values before running
    # long("BTCUSDT",  "0.001")
    # short("BTCUSDT", "0.001")
    # close("BTCUSDT", "0.001")
    # close_all("BTCUSDT")
    print("Bitunix bot loaded. Call long(), short(), close(), or close_all().")
