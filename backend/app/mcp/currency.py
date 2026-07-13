"""Helper for calling the currency MCP tool from agent code.

Agents reach FX rates only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import get_tools
from app.mcp.weather import _extract_text  # shared MCP result unwrapping
from mcp_servers.currency.schemas import ConversionResult

_TOOL = "convert_currency"


async def convert_currency(
    amount: float, from_currency: str, to_currency: str = "INR"
) -> ConversionResult | None:
    """Convert an amount via the currency MCP tool, or None on failure."""
    tools = {tool.name: tool for tool in await get_tools()}
    tool = tools.get(_TOOL)
    if tool is None:
        return None
    try:
        raw = await tool.ainvoke(
            {"amount": amount, "from_currency": from_currency, "to_currency": to_currency}
        )
    except Exception:
        return None

    text = _extract_text(raw)
    if text is None:
        return None
    try:
        return ConversionResult.model_validate_json(text)
    except ValueError:
        return None
