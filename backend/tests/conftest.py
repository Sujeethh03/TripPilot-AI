"""Shared test fixtures."""

import importlib
import os
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401  (register tables on Base.metadata)
from app.agents.nodes.conversation_manager import RouteDecision
from app.agents.state import Route
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.planning import DaySkeleton
from app.schemas.trip import IntakeExtraction, TripRequest

# Node functions are re-exported on the package, shadowing their submodules —
# fetch the real modules to monkeypatch the LLM/tool boundaries.
_cm = importlib.import_module("app.agents.nodes.conversation_manager")
_intake = importlib.import_module("app.agents.nodes.intake")
_planner = importlib.import_module("app.agents.nodes.planner")
_researcher = importlib.import_module("app.agents.nodes.researcher")
_synth = importlib.import_module("app.agents.nodes.synthesizer")
_refiner = importlib.import_module("app.agents.nodes.refiner")


def valid_itinerary() -> Itinerary:
    return Itinerary(
        destination="Kerala",
        days=[
            Day(
                day=1,
                blocks=[
                    Block(time="09:00", activity="Fort Kochi walk", location="Fort Kochi"),
                    Block(time="13:00", activity="Lunch", location="cafe", cost_inr=400),
                ],
            )
        ],
        total_cost_inr=400,
    )


@pytest.fixture
def mock_agent_llms(monkeypatch: pytest.MonkeyPatch) -> Callable[[], Itinerary]:
    """Stub every LLM/tool boundary so the graph runs with no key/network."""

    async def _route(messages: list, *, has_itinerary: bool) -> RouteDecision:
        return RouteDecision(route=Route.REFINE if has_itinerary else Route.PLAN)

    async def _extract(messages: list) -> IntakeExtraction:
        return IntakeExtraction(destination="Kerala", duration_days=1, budget_inr=20000)

    async def _plan(trip: TripRequest) -> list[DaySkeleton]:
        return [DaySkeleton(day=1, theme="Fort Kochi", meal_slots=["lunch"])]

    async def _fetch(city: str, days: int = 5) -> None:
        return None

    async def _search(query: str, max_results: int = 5) -> None:
        return None

    async def _hotels(destination: str) -> list:
        return []

    async def _leg(trip: object) -> None:
        return None

    async def _synthesize(trip: object, skeletons: object, research: object) -> Itinerary:
        return valid_itinerary()

    async def _refine(itinerary: object, validation: object, messages: object) -> Itinerary:
        return valid_itinerary()

    monkeypatch.setattr(_cm, "_route", _route)
    monkeypatch.setattr(_intake, "_extract", _extract)
    monkeypatch.setattr(_planner, "_plan", _plan)
    monkeypatch.setattr(_researcher, "fetch_forecast", _fetch)
    monkeypatch.setattr(_researcher, "search_places", _search)
    monkeypatch.setattr(_researcher, "_gather_hotels", _hotels)
    monkeypatch.setattr(_researcher, "_travel_leg", _leg)
    monkeypatch.setattr(_synth, "_synthesize", _synthesize)
    monkeypatch.setattr(_refiner, "_refine", _refine)

    return valid_itinerary


# --- Database-backed API test fixtures ---------------------------------------

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://trippilot:trippilot@localhost:5432/trippilot_test",
)


@pytest_asyncio.fixture
async def db_sessionmaker() -> AsyncIterator[async_sessionmaker]:
    """Fresh schema per test against the test database."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_sessionmaker: async_sessionmaker) -> AsyncIterator[AsyncClient]:
    """HTTP client with the DB session dependency pointed at the test database."""

    async def _get_session() -> AsyncIterator[object]:
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_auth(client: AsyncClient, email: str) -> dict[str, str]:
    """Register a user and return an Authorization header for them."""
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return await register_and_auth(client, "owner@trippilot.ai")
