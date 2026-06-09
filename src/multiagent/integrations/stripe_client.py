"""Stripe adapter — revenue snapshots and income/expense pulls."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .base import Integration


class Stripe(Integration):
    name = "stripe"
    env_vars = ("STRIPE_API_KEY",)

    def _client(self):
        try:
            import stripe
        except ImportError:
            self.log.info("stripe not installed — `pip install stripe`")
            return None
        stripe.api_key = self.env("STRIPE_API_KEY")
        return stripe

    def weekly_revenue(self) -> dict[str, Any]:
        """Last 7 days vs the prior 7 days."""
        if not self.configured:
            self.demo("weekly_revenue")
            return _SAMPLE_REVENUE
        stripe = self._client()
        if stripe is None:
            self.demo("weekly_revenue")
            return _SAMPLE_REVENUE
        now = datetime.now(timezone.utc)
        this_week = _sum_charges(stripe, now - timedelta(days=7), now)
        prior = _sum_charges(stripe, now - timedelta(days=14), now - timedelta(days=7))
        delta = this_week - prior
        pct = (delta / prior * 100) if prior else 0.0
        return {
            "this_week": round(this_week, 2),
            "prior_week": round(prior, 2),
            "delta": round(delta, 2),
            "pct_change": round(pct, 1),
            "currency": "usd",
        }

    def quarterly_breakdown(self) -> dict[str, Any]:
        """Income and (Stripe-fee) expenses for the current quarter."""
        if not self.configured:
            self.demo("quarterly_breakdown")
            return _SAMPLE_QUARTER
        stripe = self._client()
        if stripe is None:
            self.demo("quarterly_breakdown")
            return _SAMPLE_QUARTER
        # Live: aggregate BalanceTransaction over the quarter, splitting
        # gross income, Stripe fees, and refunds.
        raise NotImplementedError("Wire Stripe BalanceTransaction aggregation here.")


def _sum_charges(stripe, start: datetime, end: datetime) -> float:
    total = 0.0
    charges = stripe.Charge.list(
        created={"gte": int(start.timestamp()), "lt": int(end.timestamp())},
        limit=100,
    )
    for ch in charges.auto_paging_iter():
        if ch.get("paid") and not ch.get("refunded"):
            total += ch["amount"] / 100.0
    return total


_SAMPLE_REVENUE = {
    "this_week": 8450.00,
    "prior_week": 6200.00,
    "delta": 2250.00,
    "pct_change": 36.3,
    "currency": "usd",
}

_SAMPLE_QUARTER = {
    "income": 64200.00,
    "stripe_fees": 1863.80,
    "refunds": 500.00,
    "net": 61836.20,
    "top_clients": [
        {"name": "BrightPath SaaS", "total": 18000.00},
        {"name": "Northwind DTC", "total": 12500.00},
        {"name": "Cedar Health", "total": 9000.00},
    ],
    "currency": "usd",
}
