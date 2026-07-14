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
    origin: str | None = None  # starting point, if travelling by own transport
    transport_mode: str | None = None  # driving | transit
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = Field(default=None, gt=0)
    budget_inr: int | None = Field(default=None, gt=0)
    party_size: int | None = Field(default=None, gt=0)
    preferences: list[str] = Field(default_factory=list)


class IntakeExtraction(BaseModel):
    """LLM output contract for the Intake node (kept separate from the domain
    TripRequest so the model schema stays strict-outputs friendly).

    Every field is optional: the model fills only what the traveller stated.
    """

    destination: str | None = None
    origin: str | None = None
    transport_mode: str | None = None
    duration_days: int | None = None
    budget_inr: int | None = None
    party_size: int | None = None
    preferences: list[str] = Field(default_factory=list)
