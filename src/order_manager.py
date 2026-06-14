"""
Order placement — PAPER TRADING ONLY.
Any attempt to use a live URL will raise immediately.
"""
from __future__ import annotations

import logging

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, api_key: str, secret_key: str, base_url: str) -> None:
        # Hard safety check — refuse to run against live endpoints
        if "paper" not in base_url.lower():
            raise RuntimeError(
                "OrderManager requires a paper trading URL. "
                f"Got: {base_url!r}"
            )
        self._client = TradingClient(api_key, secret_key, paper=True)
        logger.info("OrderManager initialised (PAPER TRADING)")

    # ── Order placement ───────────────────────────────────────────────────────

    def place_option_order(
        self,
        option_symbol: str,
        qty: int,
        limit_price: float,
    ) -> dict:
        """
        Place a limit buy order for *qty* contracts of *option_symbol*.
        Uses Day TIF — order expires at market close if unfilled.

        NOTE: Add stop-loss / bracket order logic here for automated exits.
        NOTE: Consider switching to IOC/FOK for tighter fills on wide spreads.
        """
        req = LimitOrderRequest(
            symbol=option_symbol,
            qty=qty,
            side=OrderSide.BUY,
            type="limit",
            time_in_force=TimeInForce.DAY,
            limit_price=round(limit_price, 2),
        )
        logger.info(
            "Submitting PAPER order | symbol=%s qty=%d limit=$%.2f",
            option_symbol,
            qty,
            limit_price,
        )
        order = self._client.submit_order(req)
        logger.info("Order accepted | id=%s status=%s", order.id, order.status)
        return order

    # ── Position / order utilities ────────────────────────────────────────────

    def get_open_positions(self) -> list:
        """Return all open positions (equity + options)."""
        try:
            return self._client.get_all_positions()
        except Exception as exc:
            logger.error("get_open_positions failed: %s", exc)
            return []

    def cancel_all_orders(self) -> None:
        """Cancel every open order — call as part of end-of-day cleanup."""
        try:
            self._client.cancel_orders()
            logger.info("All open orders cancelled")
        except Exception as exc:
            logger.error("cancel_all_orders failed: %s", exc)
