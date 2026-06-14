#!/usr/bin/env python3
"""
QQQ Daily OTM Options Trading System
PAPER TRADING ONLY — no live orders are placed.

Usage
-----
    python main.py                  # run once (manual / cron)
    python main.py --schedule       # loop with built-in scheduler (8:30 AM ET daily)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import pytz
from dotenv import load_dotenv

load_dotenv()   # must happen before importing settings

from config.settings import LOG_FILE, LOG_LEVEL, RSI_PERIOD, SYMBOL
from src.logger import setup_logger
from src.data_fetcher import DataFetcher
from src.indicators import analyze_trend
from src.option_selector import OptionSelector
from src.risk_manager import RiskManager
from src.order_manager import OrderManager

ET = pytz.timezone("America/New_York")
logger = setup_logger("main", LOG_FILE, LOG_LEVEL)


# ── Core pipeline ─────────────────────────────────────────────────────────────

def run_premarket_analysis() -> None:
    """
    Full premarket analysis and optional order placement.
    Designed to run once around 8:30–9:25 AM ET before open.
    """
    logger.info("=" * 60)
    logger.info("QQQ Options Bot — premarket analysis starting (PAPER)")
    logger.info("=" * 60)

    # ── Load credentials ──────────────────────────────────────────────────────
    api_key    = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")
    base_url   = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

    if not api_key or not secret_key:
        logger.error("ALPACA_API_KEY / ALPACA_SECRET_KEY not set — check your .env file")
        sys.exit(1)

    # Refuse to continue unless the URL clearly identifies paper trading
    if "paper" not in base_url.lower():
        logger.error("ALPACA_BASE_URL does not look like a paper trading URL: %s", base_url)
        sys.exit(1)

    # ── Initialise clients ────────────────────────────────────────────────────
    fetcher   = DataFetcher(api_key, secret_key, base_url)
    selector  = OptionSelector(fetcher)
    order_mgr = OrderManager(api_key, secret_key, base_url)

    # ── 1. Cutoff check ───────────────────────────────────────────────────────
    if selector.is_past_cutoff():
        logger.warning("Past 3:30 PM ET cutoff — no new positions today")
        return

    # ── 2. Fetch daily bars for indicator computation ─────────────────────────
    df = fetcher.get_bars(SYMBOL, "1Day", limit=60)
    if df is None or len(df) < RSI_PERIOD + 5:
        logger.error("Insufficient bar data (got %s rows) — aborting", len(df) if df is not None else 0)
        return

    # ── 3. Compute indicators and derive directional bias ─────────────────────
    analysis = analyze_trend(df)
    logger.info(
        "Indicators | RSI=%.1f  above_SMA20=%s  above_SMA50=%s  vol_ratio=%.2f  bias=%s",
        analysis["rsi"],
        analysis["above_sma20"],
        analysis["above_sma50"],
        analysis["volume_ratio"],
        analysis["bias"].upper(),
    )

    bias = analysis["bias"]
    if bias == "neutral":
        logger.info("Bias is NEUTRAL — no trade today")
        return

    # ── 4. Get current spot price ─────────────────────────────────────────────
    quote = fetcher.get_latest_quote(SYMBOL)
    if quote is None:
        logger.error("Could not fetch %s quote — aborting", SYMBOL)
        return
    spot = quote["mid"]
    logger.info("%s spot price: $%.2f", SYMBOL, spot)

    # ── 5. Find valid expiry dates ────────────────────────────────────────────
    expiries = selector.get_expiry_dates()
    if not expiries:
        logger.error("No valid expiry dates in range — aborting")
        return
    logger.info("Candidate expiries: %s", [str(e) for e in expiries])

    # ── 6. Select nearest OTM contract that passes filters ────────────────────
    option = None
    for expiry in expiries:
        option = selector.find_otm_option(bias, spot, expiry)
        if option:
            logger.info(
                "Selected | %s  strike=$%.2f  expiry=%s  mid=$%.2f  bid=$%.2f  ask=$%.2f",
                option["symbol"],
                option["strike"],
                option["expiry"],
                option["mid_price"],
                option["bid"],
                option["ask"],
            )
            break

    if option is None:
        logger.warning("No suitable OTM option found across all candidate expiries — aborting")
        return

    # ── 7. Fetch portfolio value for sizing ───────────────────────────────────
    try:
        account = fetcher.get_account()
        account_value = float(account.portfolio_value)
    except Exception as exc:
        logger.error("Could not fetch account: %s", exc)
        return
    logger.info("Portfolio value: $%,.2f", account_value)

    # ── 8. Size position ──────────────────────────────────────────────────────
    risk_mgr  = RiskManager(account_value)
    contracts = risk_mgr.calculate_position_size(option["mid_price"])
    logger.info("Calculated position size: %d contract(s)", contracts)

    # ── 9. Pre-trade validation ───────────────────────────────────────────────
    valid, reason = risk_mgr.validate_trade(option, contracts)
    if not valid:
        logger.warning("Trade validation failed: %s — aborting", reason)
        return

    # ── 10. Place paper order ─────────────────────────────────────────────────
    logger.info(
        "Placing PAPER limit order | %d x %s @ $%.2f",
        contracts,
        option["symbol"],
        option["mid_price"],
    )
    order = order_mgr.place_option_order(option["symbol"], contracts, option["mid_price"])
    logger.info("Order result: id=%s  status=%s", order.id, order.status)

    # NOTE: Add a monitoring loop here to track fill status and P&L intraday.
    # NOTE: Add profit-target and stop-loss exit logic here (e.g., 50% gain / 50% loss).
    # NOTE: Add end-of-day close logic — cancel unfilled orders, close positions before 3:30 PM ET.


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QQQ OTM Options Bot (paper trading)")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a daily schedule at 08:30 ET instead of executing once",
    )
    args = parser.parse_args()

    if args.schedule:
        import schedule  # optional dependency for automated mode

        logger.info("Scheduler mode active — will run at 08:30 ET every weekday")
        schedule.every().monday.at("08:30").do(run_premarket_analysis)
        schedule.every().tuesday.at("08:30").do(run_premarket_analysis)
        schedule.every().wednesday.at("08:30").do(run_premarket_analysis)
        schedule.every().thursday.at("08:30").do(run_premarket_analysis)
        schedule.every().friday.at("08:30").do(run_premarket_analysis)

        while True:
            schedule.run_pending()
            time.sleep(30)
    else:
        run_premarket_analysis()
        logger.info("Run complete.")


if __name__ == "__main__":
    main()
