"""
Pure-function technical indicators.
No I/O — easy to unit-test and swap out.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from config.settings import (
    RSI_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    SMA_FAST,
    SMA_SLOW,
    VOLUME_AVG_PERIOD,
)


def compute_rsi(closes: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Wilder-smoothed RSI."""
    delta = closes.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_sma(closes: pd.Series, period: int) -> pd.Series:
    return closes.rolling(window=period).mean()


def compute_volume_ratio(volumes: pd.Series, period: int = VOLUME_AVG_PERIOD) -> float:
    """Latest volume divided by its rolling average — >1 means above-average activity."""
    avg = volumes.rolling(window=period).mean().iloc[-1]
    if avg == 0 or np.isnan(avg):
        return 1.0
    return float(volumes.iloc[-1] / avg)


def analyze_trend(df: pd.DataFrame) -> dict:
    """
    Derive a simple directional bias from price + volume data.

    Returns
    -------
    dict with keys:
        rsi          : float   — latest RSI value
        above_sma20  : bool
        above_sma50  : bool
        volume_ratio : float
        bias         : 'bullish' | 'bearish' | 'neutral'
    """
    closes  = df["close"]
    volumes = df["volume"]

    rsi    = compute_rsi(closes)
    sma20  = compute_sma(closes, SMA_FAST)
    sma50  = compute_sma(closes, SMA_SLOW)

    latest_close  = closes.iloc[-1]
    latest_rsi    = float(rsi.iloc[-1])
    above_sma20   = bool(latest_close > sma20.iloc[-1])
    above_sma50   = bool(latest_close > sma50.iloc[-1])
    volume_ratio  = compute_volume_ratio(volumes)

    # ── Bias logic ────────────────────────────────────────────────────────────
    # Bullish: oversold RSI + price still holding above short-term average
    # Bearish: overbought RSI + price slipping below short-term average
    # NOTE: extend here — add MACD crossover, Bollinger squeeze, VIX level, etc.
    if latest_rsi < RSI_OVERSOLD and above_sma20:
        bias = "bullish"
    elif latest_rsi > RSI_OVERBOUGHT and not above_sma20:
        bias = "bearish"
    else:
        bias = "neutral"

    return {
        "rsi":          latest_rsi,
        "above_sma20":  above_sma20,
        "above_sma50":  above_sma50,
        "volume_ratio": volume_ratio,
        "bias":         bias,
    }
