"""
Trading configuration constants.
All tunable parameters live here — no magic numbers in business logic.
"""
import os

# ── Instrument ──────────────────────────────────────────────────────────────
SYMBOL = "QQQ"

# ── Alpaca endpoints (loaded from .env) ──────────────────────────────────────
PAPER_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# ── Risk management ──────────────────────────────────────────────────────────
MAX_RISK_PER_TRADE = 0.02      # 2 % of portfolio per trade
MAX_CONTRACTS      = 10         # hard cap regardless of account size
MIN_CONTRACTS      = 1

# ── Option selection ─────────────────────────────────────────────────────────
OTM_PCT_CALL  = 0.03           # calls: strike ~3 % above spot
OTM_PCT_PUT   = 0.03           # puts : strike ~3 % below spot
MIN_DAYS_TO_EXPIRY = 1
MAX_DAYS_TO_EXPIRY = 5
MIN_OPTION_PRICE   = 0.05      # skip sub-nickel contracts
MAX_SPREAD_PCT     = 0.20      # max bid/ask spread as % of mid

# ── Market timing (all Eastern Time) ─────────────────────────────────────────
PREMARKET_ANALYSIS_HOUR   = 8
PREMARKET_ANALYSIS_MINUTE = 30
CUTOFF_HOUR   = 15             # 3:30 PM ET — no new entries after this
CUTOFF_MINUTE = 30

# ── Technical indicators ──────────────────────────────────────────────────────
RSI_PERIOD    = 14
RSI_OVERBOUGHT = 65            # bearish signal threshold
RSI_OVERSOLD   = 35            # bullish signal threshold
SMA_FAST       = 20
SMA_SLOW       = 50
VOLUME_AVG_PERIOD = 20         # bars used for volume ratio baseline

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE  = "logs/trading.log"
