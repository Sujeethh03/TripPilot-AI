"""Deterministic feasibility rules for the Validator node (PROJECT_PLAN §9).

No LLM. This module is the source of truth for whether an itinerary is
feasible (§5.12 rule 2). Rules are plain, individually testable functions run
as an ordered chain (§5.4 Chain of Responsibility); each returns the issues it
found. A report is invalid only if at least one *error*-severity issue exists;
warnings are surfaced but do not block shipping (§9: "then ship with a warning").

Rules that need grounded research data (opening hours, drive times) are
deliberately deferred until the places/directions MCP servers land — see TODOs.
"""

from __future__ import annotations

from collections.abc import Callable

from app.schemas.itinerary import Itinerary
from app.schemas.planning import ValidationIssue, ValidationReport
from app.schemas.trip import TripRequest

# Tunables.
MAX_ACTIVITIES_PER_DAY = 5  # §9 pacing guidance
BUDGET_BUFFER = 0.10  # allow 10% over the stated budget

_MEAL_KEYWORDS = ("breakfast", "lunch", "dinner", "brunch", "meal", "eat", "food")

Rule = Callable[[Itinerary, TripRequest | None], list[ValidationIssue]]


def parse_hhmm(value: str) -> int | None:
    """Return minutes-since-midnight for a 'HH:MM' string, or None if invalid."""
    parts = value.split(":")
    if len(parts) != 2:
        return None
    try:
        hours, minutes = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def check_not_empty(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    if not itinerary.days:
        return [
            ValidationIssue(
                code="empty_itinerary",
                message="Itinerary has no days",
                severity="warning",
            )
        ]
    return []


def check_budget(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    if trip is None or trip.budget_inr is None:
        return []
    total = sum(block.cost_inr for day in itinerary.days for block in day.blocks)
    ceiling = int(trip.budget_inr * (1 + BUDGET_BUFFER))
    if total > ceiling:
        pct = int(BUDGET_BUFFER * 100)
        return [
            ValidationIssue(
                code="over_budget",
                message=(
                    f"Estimated cost ₹{total} exceeds budget "
                    f"₹{trip.budget_inr} (+{pct}% buffer)"
                ),
                severity="error",
            )
        ]
    return []


def check_day_count(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    if trip is None or trip.duration_days is None or not itinerary.days:
        return []
    if len(itinerary.days) != trip.duration_days:
        return [
            ValidationIssue(
                code="day_count_mismatch",
                message=(
                    f"Itinerary has {len(itinerary.days)} day(s) "
                    f"but the trip is {trip.duration_days} day(s)"
                ),
                severity="error",
            )
        ]
    return []


def check_pacing(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for day in itinerary.days:
        if len(day.blocks) > MAX_ACTIVITIES_PER_DAY:
            issues.append(
                ValidationIssue(
                    code="dense_pacing",
                    message=(
                        f"Day {day.day} has {len(day.blocks)} activities "
                        f"(max {MAX_ACTIVITIES_PER_DAY})"
                    ),
                    severity="warning",
                )
            )
    return issues


def check_time_ordering(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for day in itinerary.days:
        previous: int | None = None
        for block in day.blocks:
            minutes = parse_hhmm(block.time)
            if minutes is None:
                issues.append(
                    ValidationIssue(
                        code="bad_time",
                        message=(
                            f"Day {day.day}: invalid time '{block.time}' "
                            f"for '{block.activity}'"
                        ),
                        severity="error",
                    )
                )
                continue
            if previous is not None and minutes < previous:
                issues.append(
                    ValidationIssue(
                        code="out_of_order",
                        message=(
                            f"Day {day.day}: '{block.activity}' at {block.time} "
                            f"is earlier than the previous block"
                        ),
                        severity="error",
                    )
                )
            previous = minutes
    return issues


def check_meals(itinerary: Itinerary, trip: TripRequest | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for day in itinerary.days:
        text = " ".join(f"{b.activity} {b.notes}".lower() for b in day.blocks)
        if not any(keyword in text for keyword in _MEAL_KEYWORDS):
            issues.append(
                ValidationIssue(
                    code="no_meal_slot",
                    message=f"Day {day.day} has no obvious meal slot",
                    severity="warning",
                )
            )
    return issues


# TODO: check_opening_hours — needs place hours from the `places` MCP server.
# TODO: check_drive_times — needs leg durations from the `directions` MCP server.
RULES: list[Rule] = [
    check_not_empty,
    check_day_count,
    check_budget,
    check_pacing,
    check_time_ordering,
    check_meals,
]


def validate(itinerary: Itinerary, trip: TripRequest | None = None) -> ValidationReport:
    """Run every rule and aggregate the result."""
    issues = [issue for rule in RULES for issue in rule(itinerary, trip)]
    is_valid = not any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=is_valid, issues=issues)
