"""
Market data and account access via alpaca-py.
All network calls are isolated here so the rest of the codebase stays testable.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import pytz

from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest,
    OptionChainRequest,
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient

logger = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")


class DataFetcher:
    def __init__(self, api_key: str, secret_key: str, base_url: str) -> None:
        self._stock_client = StockHistoricalDataClient(api_key, secret_key)
        self._option_client = OptionHistoricalDataClient(api_key, secret_key)
        self._trading_client = TradingClient(api_key, secret_key, paper=True)

    # ── Equity bars ──────────────────────────────────────────────────────────

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 60,
    ) -> Optional[pd.DataFrame]:
        """Return OHLCV DataFrame for *symbol*, most-recent row last."""
        tf_map = {
            "1Min":  TimeFrame(1,  TimeFrameUnit.Minute),
            "5Min":  TimeFrame(5,  TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1,  TimeFrameUnit.Hour),
            "1Day":  TimeFrame(1,  TimeFrameUnit.Day),
        }
        tf = tf_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Day))

        end   = datetime.now(tz=ET)
        start = end - timedelta(days=limit * 2)   # extra buffer for weekends/holidays

        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=end,
            limit=limit,
        )
        try:
            bars = self._stock_client.get_stock_bars(req)
            df = bars.df
            if df.empty:
                logger.warning("get_bars returned empty DataFrame for %s", symbol)
                return None
            # Multi-index [symbol, timestamp] → single index on timestamp
            if isinstance(df.index, pd.MultiIndex):
                df = df.xs(symbol, level="symbol")
            df = df.sort_index()
            return df
        except Exception as exc:
            logger.error("get_bars failed: %s", exc)
            return None

    # ── Latest quote ─────────────────────────────────────────────────────────

    def get_latest_quote(self, symbol: str) -> Optional[dict]:
        """Return {'bid': float, 'ask': float, 'mid': float} for *symbol*."""
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        try:
            quotes = self._stock_client.get_stock_latest_quote(req)
            q = quotes[symbol]
            bid = float(q.bid_price)
            ask = float(q.ask_price)
            mid = (bid + ask) / 2
            return {"bid": bid, "ask": ask, "mid": mid}
        except Exception as exc:
            logger.error("get_latest_quote failed: %s", exc)
            return None

    # ── Option chain ─────────────────────────────────────────────────────────

    def get_option_chain(
        self,
        symbol: str,
        expiry_date: date,
    ) -> Optional[pd.DataFrame]:
        """
        Return option chain snapshot for *symbol* expiring on *expiry_date*.
        Columns include: symbol, strike_price, type, bid_price, ask_price, etc.
        Returns None on failure or empty chain.
        """
        req = OptionChainRequest(
            underlying_symbol=symbol,
            expiration_date=expiry_date,
        )
        try:
            chain = self._option_client.get_option_chain(req)
            if not chain:
                logger.warning("Empty option chain for %s on %s", symbol, expiry_date)
                return None
            rows = []
            for occ_symbol, snapshot in chain.items():
                q = snapshot.latest_quote
                rows.append({
                    "symbol":       occ_symbol,
                    "strike_price": float(snapshot.greeks.delta if snapshot.greeks else 0),
                    # NOTE: greeks are indicative; replace with real-time feed for production
                    "bid_price":    float(q.bid_price) if q else 0.0,
                    "ask_price":    float(q.ask_price) if q else 0.0,
                })
            df = pd.DataFrame(rows)
            return df if not df.empty else None
        except Exception as exc:
            logger.error("get_option_chain failed: %s", exc)
            return None

    # ── Account ───────────────────────────────────────────────────────────────

    def get_account(self):
        """Return Alpaca Account object with portfolio_value, buying_power, etc."""
        try:
            return self._trading_client.get_account()
        except Exception as exc:
            logger.error("get_account failed: %s", exc)
            raise
