"""Contract test: the currency MCP tool is callable and returns structured data.

Uses FastMCP's in-memory client (no subprocess) and stubs the upstream client
so the test needs no network.
"""

import pytest
from fastmcp import Client

from mcp_servers.currency import server
from mcp_servers.currency.schemas import ConversionResult


async def test_convert_currency_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_convert(amount: float, from_currency: str, to_currency: str) -> ConversionResult:
        return ConversionResult(
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            amount=amount,
            converted=amount * 83.0,
            rate=83.0,
            date="2026-07-13",
        )

    monkeypatch.setattr(server._client, "convert", fake_convert)

    async with Client(server.mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert "convert_currency" in tools

        result = await client.call_tool(
            "convert_currency", {"amount": 10.0, "from_currency": "USD", "to_currency": "INR"}
        )

    data = result.structured_content
    assert data["to_currency"] == "INR"
    assert data["converted"] == 830.0
