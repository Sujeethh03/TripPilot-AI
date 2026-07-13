"""Shared structured-output helper over the OpenAI client.

One place for the parse boilerplate so nodes only supply a model, messages, and
a Pydantic schema. Future cross-cutting concerns (cost/latency logging,
retries, caching — PROJECT_PLAN §5.9) hang off this single seam.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

from pydantic import BaseModel

from app.core.openai_client import get_openai_client

T = TypeVar("T", bound=BaseModel)


async def parse_structured(
    model: str,
    messages: list[dict[str, str]],
    schema: type[T],
) -> T | None:
    """Call the model and parse its reply into `schema` (None on refusal)."""
    client = get_openai_client()
    completion = await client.beta.chat.completions.parse(
        model=model,
        messages=cast(Any, messages),
        response_format=schema,
    )
    return completion.choices[0].message.parsed
