"""`vidya why`: every date has a receipt. `vidya track`: nothing in the world
happens twice."""

import pytest

from vidya.fixtures import load_readings
from vidya.pipeline import fake_apply, plan_run
from vidya.track import Track
from vidya.why import explain, find_events


def _two_nights(store, fixtures):
    for day in ("day0", "day1"):
        run = plan_run(store, load_readings(day, fixtures))
        fake_apply(store, run["run_id"])


def test_why_explains_a_move_with_both_dates_and_the_source(store, fixtures):
    _two_nights(store, fixtures)
    text = explain(store, "Midterm 1")
    assert "# Midterm 1" in text
    assert "moved from" in text and "Oct 14" in text and "Oct 16" in text
    assert "source: https://" in text
    assert "As written on the page" in text
    assert "Calendar event:" in text and "none" not in text.split("Calendar event:")[1].split("\n")[0]


def test_why_matches_key_title_and_substring(store, fixtures):
    _two_nights(store, fixtures)
    assert find_events(store, "data-structures::midterm 1")[0].title == "Midterm 1"
    assert find_events(store, "midterm 1")
    assert any(e.title == "Midterm 1" for e in find_events(store, "midte"))
    # an exact title beats a substring: "midterm" is another course's item, not "Midterm 1"
    assert {e.title for e in find_events(store, "midterm")} == {"Midterm"}


def test_why_unknown_item(store, fixtures):
    _two_nights(store, fixtures)
    assert "Nothing in the belief matches" in explain(store, "underwater basket weaving")


def test_why_ambiguous_query_lists_keys(store, fixtures):
    _two_nights(store, fixtures)
    text = explain(store, "final exam")
    assert "match" in text.lower() and "::final exam" in text


def test_track_dedupes(store):
    tr = Track(store)
    assert tr.add("applications", "stripe/swe-intern-2027", note="via simplify") is True
    assert tr.add("applications", "stripe/swe-intern-2027") is False
    assert tr.has("applications", "stripe/swe-intern-2027")
    assert not tr.has("applications", "figma/swe-intern-2027")
    assert not tr.has("outreach", "stripe/swe-intern-2027")  # kinds are separate
    assert tr.kinds() == ["applications"]
    assert tr.remove("applications", "stripe/swe-intern-2027")
    assert not tr.has("applications", "stripe/swe-intern-2027")


def test_track_rejects_bad_kind(store):
    with pytest.raises(ValueError):
        Track(store).add("Bad Kind!", "x")
