"""Public tool contract for the currency MCP server.

These types ARE the interface (PROJECT_PLAN §5.1 #12): the FX provider is
swappable as long as it returns these shapes.
"""

from __future__ import annotations

from pydantic import BaseModel


class ConversionResult(BaseModel):
    """A currency conversion at the latest available reference rate."""

    from_currency: str  # ISO 4217, e.g. "USD"
    to_currency: str  # ISO 4217, e.g. "INR"
    amount: float  # amount in the source currency
    converted: float  # amount in the target currency
    rate: float  # to_currency per 1 from_currency
    date: str  # ISO date the rate is quoted for
