"""Intermediate artifacts passed between planning nodes.

These are internal to the agent pipeline (Planner -> Researcher -> Synthesizer
-> Validator); they are not part of the public API surface.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DaySkeleton(BaseModel):
    """Planner output: the shape of a day before real places are filled in."""

    day: int = Field(ge=1)
    theme: str
    target_areas: list[str] = Field(default_factory=list)
    meal_slots: list[str] = Field(default_factory=list)


class DaySkeletonPlan(BaseModel):
    """LLM output wrapper for the Planner (structured outputs need an object,
    not a bare list)."""

    days: list[DaySkeleton] = Field(default_factory=list)


class ResearchBundle(BaseModel):
    """Researcher output: real data gathered via MCP tools (no LLM).

    Shapes are intentionally loose for now; they firm up as each MCP server
    lands and we know the exact response contracts.
    """

    candidate_places: list[dict[str, Any]] = Field(default_factory=list)
    weather_by_day: dict[str, Any] = Field(default_factory=dict)
    transport_options: list[dict[str, Any]] = Field(default_factory=list)
    bus_routes: list[dict[str, Any]] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """A single deterministic feasibility problem found by the Validator."""

    code: str
    message: str
    severity: Literal["warning", "error"] = "error"


class ValidationReport(BaseModel):
    """Validator output: deterministic feasibility verdict (no LLM)."""

    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
