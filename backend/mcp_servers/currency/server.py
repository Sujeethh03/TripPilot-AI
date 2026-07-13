"""Currency MCP server (FastMCP).

Exposes FX conversion as an MCP tool. Run standalone with:
    python -m mcp_servers.currency
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_servers.currency.frankfurter import FrankfurterClient
from mcp_servers.currency.schemas import ConversionResult

mcp: FastMCP = FastMCP("currency")
_client = FrankfurterClient()


@mcp.tool
async def convert_currency(
    amount: float, from_currency: str, to_currency: str = "INR"
) -> ConversionResult:
    """Convert an amount between currencies at the latest reference rate.

    Args:
        amount: Amount in the source currency.
        from_currency: ISO 4217 code to convert from, e.g. "USD".
        to_currency: ISO 4217 code to convert to (default "INR").
    """
    return await _client.convert(amount, from_currency, to_currency)
