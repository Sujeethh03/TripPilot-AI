"""OpenAI client factory.

A single shared AsyncOpenAI client (§5.4 Singleton). Constructed lazily so
importing this module never requires a key; the key is read from settings when
the client is first requested.
"""

from __future__ import annotations

from functools import lru_cache

from openai import AsyncOpenAI

from app.config import get_settings


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)
