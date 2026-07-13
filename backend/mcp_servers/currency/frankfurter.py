"""Frankfurter.app adapter for the currency MCP server.

Frankfurter is a free, no-key FX API over ECB reference rates. Parsing is
defensive (PROJECT_PLAN §5.1 #11): upstream JSON is assumed to be possibly
malformed.
"""

from __future__ import annotations

from typing import Any

import httpx

from mcp_servers.currency.schemas import ConversionResult

_LATEST_URL = "https://api.frankfurter.dev/v1/latest"


class CurrencyError(RuntimeError):
    """Raised when the upstream FX provider fails or returns an unusable rate."""


class FrankfurterClient:
    """Thin async client over the Frankfurter FX API.

    An httpx client may be injected for testing; otherwise one is created per
    call.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client

    async def convert(
        self, amount: float, from_currency: str, to_currency: str
    ) -> ConversionResult:
        base = from_currency.upper()
        target = to_currency.upper()
        if base == target:
            # No round-trip needed; the identity conversion.
            return ConversionResult(
                from_currency=base,
                to_currency=target,
                amount=amount,
                converted=amount,
                rate=1.0,
                date="",
            )

        params: dict[str, str | float] = {"amount": amount, "from": base, "to": target}
        try:
            if self._http is not None:
                resp = await self._http.get(_LATEST_URL, params=params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(_LATEST_URL, params=params)
            resp.raise_for_status()
            payload: Any = resp.json()
        except httpx.HTTPError as exc:
            raise CurrencyError(f"currency request failed: {exc}") from exc

        converted = _rate_for(payload, target)
        if converted is None:
            raise CurrencyError(f"no rate for {base}->{target}")
        rate = converted / amount if amount else 0.0
        return ConversionResult(
            from_currency=base,
            to_currency=target,
            amount=amount,
            converted=round(converted, 2),
            rate=round(rate, 6),
            date=_safe_date(payload),
        )


def _rate_for(payload: Any, target: str) -> float | None:
    if isinstance(payload, dict):
        rates = payload.get("rates")
        if isinstance(rates, dict) and isinstance(rates.get(target), (int, float)):
            return float(rates[target])
    return None


def _safe_date(payload: Any) -> str:
    if isinstance(payload, dict):
        date = payload.get("date")
        if isinstance(date, str):
            return date
    return ""
