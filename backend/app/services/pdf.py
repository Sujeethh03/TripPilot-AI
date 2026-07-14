"""Render an Itinerary to a PDF document.

A pure function over the SSOT `Itinerary` schema (§5.1) so it stays decoupled
from the HTTP/DB layers and is unit-testable in isolation. Uses fpdf2, which is
pure-Python (no native deps) — keeps local + CI setup trivial.
"""

from __future__ import annotations

from fpdf import FPDF

from app.schemas.itinerary import Itinerary, Weather

# fpdf2's core fonts are latin-1 only; rupee/other glyphs would raise. Render
# amounts as "Rs." and strip anything outside latin-1 defensively.
_RUPEE = "Rs."


def _latin1(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def _hours(minutes: float) -> str:
    h, m = divmod(round(minutes), 60)
    return f"{h}h {m}m" if h else f"{m}m"


def _weather_line(weather: Weather) -> str:
    parts = []
    if weather.max_temp_c is not None and weather.min_temp_c is not None:
        parts.append(f"{round(weather.max_temp_c)}/{round(weather.min_temp_c)}C")
    if weather.condition:
        parts.append(weather.condition)
    return " ".join(parts)


def render_itinerary_pdf(itinerary: Itinerary, *, title: str | None = None) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    heading = title or f"Trip to {itinerary.destination}"
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 10, _latin1(heading), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _latin1(f"Destination: {itinerary.destination}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        8,
        _latin1(f"Estimated total: {_RUPEE} {itinerary.total_cost_inr:,}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )

    if itinerary.travel is not None:
        t = itinerary.travel
        leg = f"Getting there: {t.origin} to {t.destination} by {t.mode}"
        if t.distance_km is not None and t.duration_min is not None:
            leg += f" ({round(t.distance_km)} km, {_hours(t.duration_min)})"
        pdf.cell(0, 8, _latin1(leg), new_x="LMARGIN", new_y="NEXT")

    if itinerary.hotels:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _latin1("Where to stay"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for hotel in itinerary.hotels:
            line = f"  - {hotel.name}"
            if hotel.rating is not None:
                line += f" ({hotel.rating})"
            if hotel.area:
                line += f" - {hotel.area}"
            pdf.multi_cell(0, 6, _latin1(line), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    for day in itinerary.days:
        pdf.set_font("Helvetica", "B", 14)
        heading = f"Day {day.day}"
        if day.weather is not None:
            heading += f"   {_weather_line(day.weather)}"
        pdf.multi_cell(0, 9, _latin1(heading), new_x="LMARGIN", new_y="NEXT")

        for block in day.blocks:
            pdf.set_font("Helvetica", "", 11)
            line = f"{block.time}  {block.activity} - {block.location}"
            if block.cost_inr:
                line += f" ({_RUPEE} {block.cost_inr:,})"
            pdf.multi_cell(0, 7, _latin1(line), new_x="LMARGIN", new_y="NEXT")
            if block.notes:
                pdf.set_font("Helvetica", "I", 9)
                pdf.multi_cell(0, 6, _latin1(f"    {block.notes}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    return bytes(pdf.output())
