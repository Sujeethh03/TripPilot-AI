"""Unit tests for the Frankfurter FX adapter — parsing/conversion logic."""

import httpx
import pytest

from mcp_servers.currency.frankfurter import CurrencyError, FrankfurterClient


def _client_with(
    json_body: dict, status: int = 200
) -> tuple[FrankfurterClient, httpx.AsyncClient]:
    transport = httpx.MockTransport(lambda req: httpx.Response(status, json=json_body))
    http = httpx.AsyncClient(transport=transport)
    return FrankfurterClient(http_client=http), http


async def test_convert_computes_rate_and_amount() -> None:
    client, http = _client_with({"date": "2026-07-13", "rates": {"INR": 8305.0}})
    async with http:
        result = await client.convert(100.0, "usd", "inr")

    assert result.from_currency == "USD"
    assert result.to_currency == "INR"
    assert result.converted == 8305.0
    assert result.rate == 83.05  # per 1 USD
    assert result.date == "2026-07-13"


async def test_same_currency_is_identity_without_network() -> None:
    # No transport needed — same-currency short-circuits before any request.
    client = FrankfurterClient()
    result = await client.convert(500.0, "INR", "INR")
    assert result.rate == 1.0
    assert result.converted == 500.0


async def test_missing_rate_raises() -> None:
    client, http = _client_with({"date": "2026-07-13", "rates": {}})
    async with http:
        with pytest.raises(CurrencyError):
            await client.convert(100.0, "USD", "INR")


async def test_http_error_raises() -> None:
    client, http = _client_with({}, status=500)
    async with http:
        with pytest.raises(CurrencyError):
            await client.convert(100.0, "USD", "INR")
