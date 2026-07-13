"""Exhaustive tests for the deterministic Validator rules."""

from app.agents.validation import parse_hhmm, validate
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.trip import TripRequest


def _itin(*days: Day, destination: str = "Kochi") -> Itinerary:
    return Itinerary(destination=destination, days=list(days))


def _good_day(day: int = 1) -> Day:
    return Day(
        day=day,
        blocks=[
            Block(time="09:00", activity="Fort Kochi walk", location="Fort Kochi", cost_inr=0),
            Block(time="13:00", activity="Lunch at cafe", location="Fort Kochi", cost_inr=400),
            Block(time="17:00", activity="Chinese fishing nets", location="Fort Kochi", cost_inr=0),
        ],
    )


# --- parse_hhmm ---------------------------------------------------------------

def test_parse_hhmm_valid() -> None:
    assert parse_hhmm("00:00") == 0
    assert parse_hhmm("09:30") == 570
    assert parse_hhmm("23:59") == 1439


def test_parse_hhmm_invalid() -> None:
    for bad in ["24:00", "12:60", "9:00am", "abc", "12", "12:00:00", ""]:
        assert parse_hhmm(bad) is None


# --- happy path ---------------------------------------------------------------

def test_valid_itinerary_passes() -> None:
    report = validate(_itin(_good_day()), TripRequest(budget_inr=20000))
    assert report.is_valid
    assert all(i.severity != "error" for i in report.issues)


# --- budget -------------------------------------------------------------------

def test_over_budget_is_error() -> None:
    day = Day(day=1, blocks=[Block(time="10:00", activity="Lunch", location="x", cost_inr=30000)])
    report = validate(_itin(day), TripRequest(budget_inr=20000))
    assert not report.is_valid
    assert any(i.code == "over_budget" for i in report.issues)


def test_within_buffer_passes() -> None:
    # 21,000 is within 20,000 + 10% (22,000).
    day = Day(day=1, blocks=[Block(time="10:00", activity="Lunch", location="x", cost_inr=21000)])
    report = validate(_itin(day), TripRequest(budget_inr=20000))
    assert not any(i.code == "over_budget" for i in report.issues)


def test_no_budget_skips_budget_rule() -> None:
    day = Day(day=1, blocks=[Block(time="10:00", activity="Lunch", location="x", cost_inr=999999)])
    report = validate(_itin(day), TripRequest())
    assert not any(i.code == "over_budget" for i in report.issues)


# --- day count ----------------------------------------------------------------

def test_day_count_mismatch_is_error() -> None:
    report = validate(_itin(_good_day(1), _good_day(2)), TripRequest(duration_days=3))
    assert not report.is_valid
    assert any(i.code == "day_count_mismatch" for i in report.issues)


def test_day_count_match_passes() -> None:
    report = validate(_itin(_good_day(1)), TripRequest(duration_days=1))
    assert not any(i.code == "day_count_mismatch" for i in report.issues)


def test_day_count_skipped_without_duration() -> None:
    report = validate(_itin(_good_day(1), _good_day(2)), TripRequest())
    assert not any(i.code == "day_count_mismatch" for i in report.issues)


# --- pacing -------------------------------------------------------------------

def test_dense_day_warns_but_stays_valid() -> None:
    blocks = [
        Block(time=f"{8 + i:02d}:00", activity=f"Lunch stop {i}", location="x")
        for i in range(6)
    ]
    report = validate(_itin(Day(day=1, blocks=blocks)))
    assert report.is_valid  # warning only
    assert any(i.code == "dense_pacing" for i in report.issues)


# --- time ordering ------------------------------------------------------------

def test_out_of_order_is_error() -> None:
    day = Day(
        day=1,
        blocks=[
            Block(time="15:00", activity="Lunch", location="x"),
            Block(time="09:00", activity="Museum", location="y"),
        ],
    )
    report = validate(_itin(day))
    assert not report.is_valid
    assert any(i.code == "out_of_order" for i in report.issues)


def test_bad_time_is_error() -> None:
    day = Day(day=1, blocks=[Block(time="25:00", activity="Lunch", location="x")])
    report = validate(_itin(day))
    assert not report.is_valid
    assert any(i.code == "bad_time" for i in report.issues)


# --- meals --------------------------------------------------------------------

def test_missing_meal_warns() -> None:
    day = Day(day=1, blocks=[Block(time="10:00", activity="Museum", location="x")])
    report = validate(_itin(day))
    assert report.is_valid  # warning only
    assert any(i.code == "no_meal_slot" for i in report.issues)


# --- empty --------------------------------------------------------------------

def test_empty_itinerary_warns() -> None:
    report = validate(_itin())
    assert report.is_valid
    assert any(i.code == "empty_itinerary" for i in report.issues)
