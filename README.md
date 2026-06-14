# QQQ Daily OTM Options Bot

Automated premarket analysis and OTM options order placement for QQQ, using **Alpaca paper trading only**. No live orders are placed.

> **Disclaimer:** This is educational software. It is not financial advice. Options trading carries substantial risk. Never risk money you cannot afford to lose.

---

## How it works

1. **Premarket (~8:30 AM ET):** fetches the last 60 daily bars for QQQ.
2. **Indicator analysis:** computes RSI, 20/50-day SMAs, and volume ratio.
3. **Bias decision:**
   - RSI < 35 and price above SMA-20 → **bullish** → look for an OTM call
   - RSI > 65 and price below SMA-20 → **bearish** → look for an OTM put
   - Otherwise → **neutral** → no trade today
4. **Contract selection:** scans the QQQ option chain for the nearest expiry (1–5 days out) and picks the strike closest to ~3 % OTM.
5. **Risk check:** sizes to risk at most 2 % of portfolio; validates bid/ask spread and minimum price.
6. **Order:** places a DAY limit order at the mid price via Alpaca paper trading.

### Safety features
- Hard check that `ALPACA_BASE_URL` contains `"paper"` — exits immediately if not.
- `OrderManager` constructor raises if a live URL is passed.
- 3:30 PM ET cutoff respected — no new orders placed after that time.
- All credentials come from environment variables; nothing is hard-coded.

---

## Project structure

```
paperqqq/
├── main.py                 # entry point — orchestrates the full pipeline
├── requirements.txt
├── .env.example            # copy to .env and fill in your paper keys
├── config/
│   └── settings.py         # all tunable constants (risk %, RSI thresholds, etc.)
└── src/
    ├── data_fetcher.py     # Alpaca market data + account API calls
    ├── indicators.py       # pure-function RSI / SMA / volume calculations
    ├── option_selector.py  # expiry date logic + OTM contract selection
    ├── risk_manager.py     # position sizing + pre-trade validation
    ├── order_manager.py    # paper order placement via alpaca-py
    └── logger.py           # file + console logging setup
```

---

## Setup

### 1. Get Alpaca paper trading API keys

1. Sign up at [alpaca.markets](https://alpaca.markets)
2. In the dashboard, switch to **Paper Trading** (toggle in the top-left)
3. Go to **API Keys** → **Generate New Key**
4. Copy the key and secret

### 2. Configure the project

```bash
git clone <this-repo>
cd paperqqq

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste your paper API key and secret
```

### 3. Run

```bash
# Run once (manual / cron job)
python main.py

# Run on a daily 8:30 AM ET schedule (blocks forever)
python main.py --schedule
```

Logs are written to `logs/trading.log` and also printed to the console.

---

## Configuration

All parameters are in `config/settings.py`:

| Constant | Default | Description |
|---|---|---|
| `MAX_RISK_PER_TRADE` | `0.02` | Max portfolio % risked per trade |
| `MAX_CONTRACTS` | `10` | Hard cap on contracts per order |
| `OTM_PCT_CALL` | `0.03` | Call strike % above spot |
| `OTM_PCT_PUT` | `0.03` | Put strike % below spot |
| `MIN_DAYS_TO_EXPIRY` | `1` | Nearest expiry to consider |
| `MAX_DAYS_TO_EXPIRY` | `5` | Farthest expiry to consider |
| `RSI_OVERBOUGHT` | `65` | RSI level triggering bearish bias |
| `RSI_OVERSOLD` | `35` | RSI level triggering bullish bias |
| `CUTOFF_HOUR/MINUTE` | `15:30` | No new entries after 3:30 PM ET |

---

## Extending the system

The codebase has `# NOTE:` comments marking the main extension points:

- **More indicators** (`src/indicators.py`) — add MACD, Bollinger Bands, VIX overlay, etc.
- **Delta-based strike selection** (`src/option_selector.py`) — replace the % OTM proxy with real-time greeks when available.
- **Exit logic** (`main.py`) — add a monitoring loop with profit-target / stop-loss closes.
- **EOD cleanup** (`main.py`) — cancel unfilled orders and close positions before 3:30 PM ET.
- **Spread orders** (`src/order_manager.py`) — replace naked options with defined-risk vertical spreads.
- **Scheduling** — use `--schedule` flag or deploy with a cron job / cloud scheduler.