"""Synthesizer — assembles the Itinerary (§9).

GPT-4o combines TripRequest + DaySkeleton[] + ResearchBundle into the canonical
Itinerary via strict structured output. It prefers grounded research data and
avoids inventing facts when research is absent. The LLM call is isolated in
`_synthesize` for testing.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.prompts.synthesizer import SYNTHESIZER_SYSTEM_PROMPT
from app.agents.state import ConversationState
from app.config import get_settings
from app.core.llm import parse_structured
from app.schemas.itinerary import HotelOption, Itinerary, TravelLeg, Weather
from app.schemas.planning import DaySkeleton, ResearchBundle
from app.schemas.trip import TripRequest


def _attach_grounding(
    itinerary: Itinerary, trip: TripRequest, research: ResearchBundle | None
) -> None:
    """Overwrite the itinerary's factual fields (travel leg, hotels, origin) from
    researched data, never the LLM — same principle as weather."""
    itinerary.origin = trip.origin

    leg = research.travel_leg if research else None
    itinerary.travel = TravelLeg.model_validate(leg) if leg else None

    hotels = research.hotels if research else []
    itinerary.hotels = [
        HotelOption(
            name=h.get("name", ""),
            area=h.get("area", "") or "",
            rating=h.get("rating"),
        )
        for h in hotels
        if h.get("name")
    ]


def _attach_weather(itinerary: Itinerary, research: ResearchBundle | None) -> None:
    """Overwrite each day's weather from the researched forecast (a fact), never
    the LLM. The forecast dict is insertion-ordered by forecast day, so we zip
    it against the itinerary days; days beyond the forecast window stay None."""
    forecasts = list((research.weather_by_day if research else {}).values())
    for i, day in enumerate(itinerary.days):
        f = forecasts[i] if i < len(forecasts) else None
        day.weather = (
            Weather(
                min_temp_c=f.get("min_temp_c"),
                max_temp_c=f.get("max_temp_c"),
                condition=f.get("condition", ""),
            )
            if f
            else None
        )


async def _synthesize(
    trip: TripRequest,
    skeletons: list[DaySkeleton],
    research: ResearchBundle | None,
) -> Itinerary:
    payload = {
        "trip_request": trip.model_dump(mode="json"),
        "day_skeletons": [s.model_dump() for s in skeletons],
        "research": (research or ResearchBundle()).model_dump(mode="json"),
    }
    messages = [
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload)},
    ]
    result = await parse_structured(get_settings().model_planner, messages, Itinerary)
    return result or Itinerary(destination=trip.destination or "TBD")


async def synthesizer(state: ConversationState) -> dict[str, Any]:
    trip = state.get("trip_request")
    if trip is None:
        return {}
    research = state.get("research")
    itinerary = await _synthesize(trip, state.get("day_skeletons") or [], research)
    _attach_weather(itinerary, research)
    _attach_grounding(itinerary, trip, research)
    return {"itinerary": itinerary}
