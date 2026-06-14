"""
Finds an appropriate QQQ OTM option contract for the current session.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

from config.settings import (
    MIN_DAYS_TO_EXPIRY,
    MAX_DAYS_TO_EXPIRY,
    OTM_PCT_CALL,
    OTM_PCT_PUT,
    CUTOFF_HOUR,
    CUTOFF_MINUTE,
    MIN_OPTION_PRICE,
    MAX_SPREAD_PCT,
)
from src.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)
ET = pytz.timezone("America/New_York")


class OptionSelector:
    def __init__(self, data_fetcher: DataFetcher) -> None:
        self._fetcher = data_fetcher

    # ── Timing ────────────────────────────────────────────────────────────────

    def is_past_cutoff(self) -> bool:
        """True if current ET time is at or after 3:30 PM — respect expiry-day rule."""
        now = datetime.now(tz=ET)
        return (now.hour, now.minute) >= (CUTOFF_HOUR, CUTOFF_MINUTE)

    # ── Expiry dates ──────────────────────────────────────────────────────────

    def get_expiry_dates(self) -> list[date]:
        """
        Return candidate expiry dates in MIN..MAX_DAYS_TO_EXPIRY window.
        QQQ has Monday/Wednesday/Friday weekly expirations plus monthly.
        We return all weekdays and let the chain lookup confirm tradable strikes.
        """
        today = date.today()
        candidates = []
        for delta in range(MIN_DAYS_TO_EXPIRY, MAX_DAYS_TO_EXPIRY + 1):
            d = today + timedelta(days=delta)
            if d.weekday() < 5:          # Mon–Fri only
                candidates.append(d)
        return candidates

    # ── Contract selection ────────────────────────────────────────────────────

    def find_otm_option(
        self,
        bias: str,
        spot_price: float,
        expiry: date,
    ) -> Optional[dict]:
        """
        Locate the nearest-strike OTM contract matching *bias* on *expiry*.

        Strategy
        --------
        • bullish → OTM call, target strike ≈ spot * (1 + OTM_PCT_CALL)
        • bearish → OTM put,  target strike ≈ spot * (1 - OTM_PCT_PUT)

        Returns a dict ready for the order manager, or None if nothing passes filters.
        NOTE: swap the chain lookup for a live Greeks feed to target by delta instead.
        """
        if bias not in ("bullish", "bearish"):
            return None

        option_type  = "call" if bias == "bullish" else "put"
        target_strike = (
            spot_price * (1 + OTM_PCT_CALL)
            if bias == "bullish"
            else spot_price * (1 - OTM_PCT_PUT)
        )

        chain_df = self._fetcher.get_option_chain("QQQ", expiry)
        if chain_df is None or chain_df.empty:
            logger.warning("No chain data for expiry %s", expiry)
            return None

        # Filter to the correct option type encoded in the OCC symbol
        # OCC format: QQQ{YYMMDD}{C|P}{8-digit strike*1000}
        type_char = "C" if option_type == "call" else "P"
        mask = chain_df["symbol"].str.contains(f"QQQ\\d{{6}}{type_char}", regex=True)
        typed_df = chain_df[mask].copy()

        if typed_df.empty:
            logger.warning("No %s options in chain for %s", option_type, expiry)
            return None

        # Parse strike from OCC symbol (chars 12-20 are 8-digit strike*1000)
        typed_df["strike"] = typed_df["symbol"].apply(
            lambda s: int(s[12:20]) / 1000.0
        )

        # Pick the strike closest to our target
        typed_df["dist"] = (typed_df["strike"] - target_strike).abs()
        best = typed_df.nsmallest(1, "dist").iloc[0]

        bid = float(best["bid_price"])
        ask = float(best["ask_price"])
        mid = (bid + ask) / 2.0

        # Basic liquidity / price sanity filters
        if mid < MIN_OPTION_PRICE:
            logger.warning("Option mid $%.2f below minimum — skipping %s", mid, best["symbol"])
            return None
        spread_pct = (ask - bid) / mid if mid > 0 else 1.0
        if spread_pct > MAX_SPREAD_PCT:
            logger.warning(
                "Spread %.1f%% exceeds max for %s — skipping", spread_pct * 100, best["symbol"]
            )
            return None

        return {
            "symbol":      best["symbol"],
            "strike":      best["strike"],
            "expiry":      expiry,
            "option_type": option_type,
            "bid":         bid,
            "ask":         ask,
            "mid_price":   round(mid, 2),
        }
