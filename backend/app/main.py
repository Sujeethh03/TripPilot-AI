"""FastAPI application entrypoint.

Wires together configuration, middleware, and the versioned API router.
Run locally with: uvicorn app.main:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import build_graph
from app.api.v1 import auth, chat, health, trips
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the graph once per process, with the configured checkpointer."""
    settings = get_settings()
    async with AsyncExitStack() as stack:
        if settings.checkpointer == "postgres" and settings.database_url:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            saver = await stack.enter_async_context(
                AsyncPostgresSaver.from_conn_string(settings.postgres_dsn)
            )
            await saver.setup()
            app.state.graph = build_graph(saver)
        else:
            app.state.graph = build_graph()
        yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(trips.router, prefix=settings.api_v1_prefix)
    app.include_router(chat.router)  # WebSocket lives at /ws/... (no v1 prefix)

    return app


app = create_app()
