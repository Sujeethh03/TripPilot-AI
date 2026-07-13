"""Tests for itinerary PDF rendering and the export endpoint."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Trip
from app.services.pdf import render_itinerary_pdf
from tests.conftest import valid_itinerary


def test_render_itinerary_pdf_produces_pdf_bytes() -> None:
    pdf = render_itinerary_pdf(valid_itinerary(), title="Kerala getaway")
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_render_handles_non_latin1_text() -> None:
    itinerary = valid_itinerary()
    itinerary.days[0].blocks[0].notes = "Try the ₹ special — café ☕"
    pdf = render_itinerary_pdf(itinerary)  # must not raise on non-latin1 glyphs
    assert pdf.startswith(b"%PDF")


async def test_export_pdf_requires_itinerary(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    trip_id = (
        await client.post("/api/v1/trips", json={"destination": "Kerala"}, headers=auth_headers)
    ).json()["id"]
    r = await client.get(f"/api/v1/trips/{trip_id}/pdf", headers=auth_headers)
    assert r.status_code == 409


async def test_export_pdf_happy_path(
    client: AsyncClient, auth_headers: dict[str, str], db_sessionmaker: async_sessionmaker
) -> None:
    trip_id = (
        await client.post("/api/v1/trips", json={"destination": "Kerala"}, headers=auth_headers)
    ).json()["id"]

    async with db_sessionmaker() as session:
        trip = (await session.execute(select(Trip).where(Trip.id == trip_id))).scalar_one()
        trip.itinerary = valid_itinerary().model_dump(mode="json")
        await session.commit()

    r = await client.get(f"/api/v1/trips/{trip_id}/pdf", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
