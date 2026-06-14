"""
Position sizing and pre-trade validation.
Keep all risk math here so it's easy to audit and tune.
"""
from __future__ import annotations

import logging
import math

from config.settings import (
    MAX_RISK_PER_TRADE,
    MAX_CONTRACTS,
    MIN_CONTRACTS,
    MIN_OPTION_PRICE,
    MAX_SPREAD_PCT,
)

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, account_value: float) -> None:
        self._account_value = account_value

    def calculate_position_size(self, mid_price: float) -> int:
        """
        How many contracts can we buy while risking at most MAX_RISK_PER_TRADE
        of portfolio?  Each contract covers 100 shares.

        NOTE: For defined-risk spreads, replace full-premium risk with max-loss.
        """
        if mid_price <= 0:
            return MIN_CONTRACTS
        max_risk_dollars = self._account_value * MAX_RISK_PER_TRADE
        contracts = math.floor(max_risk_dollars / (mid_price * 100))
        return max(MIN_CONTRACTS, min(contracts, MAX_CONTRACTS))

    def validate_trade(self, option: dict, contracts: int) -> tuple[bool, str]:
        """
        Gate the order on basic sanity checks.
        Returns (True, 'ok') or (False, reason_string).
        """
        mid    = option.get("mid_price", 0)
        bid    = option.get("bid", 0)
        ask    = option.get("ask", 0)

        if mid < MIN_OPTION_PRICE:
            return False, f"mid ${mid:.2f} below minimum ${MIN_OPTION_PRICE}"

        spread_pct = (ask - bid) / mid if mid > 0 else 1.0
        if spread_pct > MAX_SPREAD_PCT:
            return False, f"spread {spread_pct:.1%} exceeds max {MAX_SPREAD_PCT:.1%}"

        if contracts < MIN_CONTRACTS:
            return False, f"calculated contracts ({contracts}) below minimum"

        cost = contracts * mid * 100
        max_allowed = self._account_value * MAX_RISK_PER_TRADE
        if cost > max_allowed * 1.05:   # 5 % tolerance for rounding
            return False, f"total cost ${cost:.0f} exceeds risk limit ${max_allowed:.0f}"

        # NOTE: add open-position count check here to limit concurrent trades
        return True, "ok"
