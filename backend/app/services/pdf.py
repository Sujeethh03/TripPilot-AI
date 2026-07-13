"""Render an Itinerary to a PDF document.

A pure function over the SSOT `Itinerary` schema (§5.1) so it stays decoupled
from the HTTP/DB layers and is unit-testable in isolation. Uses fpdf2, which is
pure-Python (no native deps) — keeps local + CI setup trivial.
"""

from __future__ import annotations

from fpdf import FPDF

from app.schemas.itinerary import Itinerary

# fpdf2's core fonts are latin-1 only; rupee/other glyphs would raise. Render
# amounts as "Rs." and strip anything outside latin-1 defensively.
_RUPEE = "Rs."


def _latin1(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


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
    pdf.ln(4)

    for day in itinerary.days:
        pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 9, _latin1(f"Day {day.day}"), new_x="LMARGIN", new_y="NEXT")

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
