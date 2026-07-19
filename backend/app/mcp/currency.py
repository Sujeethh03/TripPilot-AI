"""Helper for calling the currency MCP tool from agent code.

Agents reach FX rates only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import call_tool
from mcp_servers.currency.schemas import ConversionResult

_SERVER = "currency"
_TOOL = "convert_currency"


async def convert_currency(
    amount: float, from_currency: str, to_currency: str = "INR"
) -> ConversionResult | None:
    """Convert an amount via the currency MCP tool, or None on failure."""
    text = await call_tool(
        _SERVER,
        _TOOL,
        {"amount": amount, "from_currency": from_currency, "to_currency": to_currency},
    )
    if text is None:
        return None
    try:
        return ConversionResult.model_validate_json(text)
    except ValueError:
        return None
