"""Trip request schema — the structured intent extracted from conversation."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class TripRequest(BaseModel):
    """What the user wants, once Intake has resolved the ambiguous bits.

    Any field may be None until Intake has gathered it; the Intake node is
    responsible for asking clarifying questions to fill the required ones.
    """

    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_inr: int | None = Field(default=None, gt=0)
    party_size: int | None = Field(default=None, gt=0)
    preferences: list[str] = Field(default_factory=list)
