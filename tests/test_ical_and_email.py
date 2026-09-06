"""iCal feed (the MFA mitigation) and the read-only email adapter, including how
an email merges with a page read in the nightly diff."""

from pathlib import Path

from vidya.extract.email import extract_email
from vidya.extract.ical import clean_summary, extract_ical
from vidya.fixtures import fixture_dir, load_readings
from vidya.model import MOVED, SOURCE_FAILED, STATUS_ERROR, UNREADABLE, Reading
from vidya.pipeline import fake_apply, plan_run
from vidya.resolve import resolve_reading

FX = fixture_dir()
READ_AT = "2026-09-06T23:00:00-04:00"


def test_ical_feed_parses_tzid_utc_and_date_ranges():
    r = extract_ical((FX / "ical" / "brightspace.ics").read_text(), "data-structures", "https://lms.example.edu/feed.ics", read_at=READ_AT)
    assert r.ok
    events, review = resolve_reading(r)
    by = {e.title: e for e in events}
    assert by["Homework 1"].start == "2026-09-19T23:59:00-04:00"          # TZID=America/New_York
    assert by["Midterm 1"].start == "2026-10-14T11:00:00-04:00"           # 15:00Z
    assert by["Midterm 1"].end == "2026-10-14T13:00:00-04:00"
    assert (by["Reading days"].start, by["Reading days"].end, by["Reading days"].all_day) == ("2026-10-20", "2026-10-22", True)
    assert [e.title for e in review] == ["Lecture"] and "recurring" in review[0].review_reason
    assert by["Homework 1"].sources[0].startswith("https://lms.example.edu/d2l/lms/dropbox")  # folded URL line


def test_ical_titles_match_page_titles():
    assert clean_summary("Homework 1 - Due") == "Homework 1"
    assert clean_summary("Midterm 1 [CS 201]") == "Midterm 1"
    assert clean_summary("Quiz 2 - Availability Ends") == "Quiz 2"


def test_ical_feed_and_page_agree_on_keys(store, fixtures):
    """A feed can replace a page read for the same course without re-creating events."""
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    feed = extract_ical((FX / "ical" / "brightspace.ics").read_text(), "data-structures", "https://lms.example.edu/feed.ics", read_at=READ_AT)
    events, _ = resolve_reading(feed)
    believed = {e.key for e in store.belief("data-structures")}
    assert {"data-structures::homework 1", "data-structures::midterm 1"} <= believed
    assert {e.key for e in events} & believed == {"data-structures::homework 1", "data-structures::midterm 1"}


def test_email_is_read_only_partial_and_matches_known_titles():
    raw = (FX / "email" / "professor_move.eml").read_bytes()
    r = extract_email(raw, "data-structures", read_at=READ_AT, known_titles=["Midterm 1", "Homework 2", "Project 1"])
    assert r.partial and r.ok
    assert [i.title for i in r.items] == ["Midterm 1"]
    assert r.items[0].posted_at == "2026-09-06"
    events, review = resolve_reading(r)
    assert review == []
    assert events[0].start == "2026-10-16T11:00:00-04:00"
    assert events[0].superseded == "2026-10-14"


def test_email_ambiguous_or_unknown_mentions_go_to_review():
    raw = (FX / "email" / "professor_move.eml").read_bytes()
    r = extract_email(raw, "data-structures", read_at=READ_AT, known_titles=["Midterm 1", "Midterm 2"])
    _, review = resolve_reading(r)
    assert len(review) == 1 and "several items" in review[0].review_reason
    r = extract_email(raw, "data-structures", read_at=READ_AT, known_titles=[])
    _, review = resolve_reading(r)
    assert len(review) == 1 and "not in the course belief" in review[0].review_reason


def test_email_change_supersedes_stale_page(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    known = [e.title for e in store.belief("data-structures")]
    email = extract_email((FX / "email" / "professor_move.eml").read_bytes(), "data-structures", read_at=READ_AT, known_titles=known)
    stale_page = [r for r in load_readings("day0", fixtures, read_at=READ_AT) if r.course_id == "data-structures"]
    run = plan_run(store, stale_page + [email])
    assert [(c.type, c.title) for c in run["diff"].changes] == [(MOVED, "Midterm 1")]
    after = run["diff"].changes[0].after
    assert after.start == "2026-10-16T11:00:00-04:00"
    assert any(a.startswith("supersedes") for a in after.assumptions)
    assert len(after.sources) == 2
    assert [o.op for o in run["review"].approved] == ["update"]


def test_email_alone_moves_but_never_removes_when_page_fails(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    known = [e.title for e in store.belief("data-structures")]
    n_before = len(store.belief("data-structures"))
    email = extract_email((FX / "email" / "professor_move.eml").read_bytes(), "data-structures", read_at=READ_AT, known_titles=known)
    failed = Reading("data-structures", "https://lms.example.edu/d2l/home/41001", READ_AT, status=STATUS_ERROR, error="login wall")
    others = [r for r in load_readings("day0", fixtures, read_at=READ_AT) if r.course_id != "data-structures"]
    run = plan_run(store, others + [failed, email])
    assert [(c.type, c.title) for c in run["diff"].changes] == [(MOVED, "Midterm 1")]
    assert run["diff"].pending_removals == []
    notes = {c.course_id: c.type for c in run["diff"].unreadable}
    assert notes == {"data-structures": SOURCE_FAILED}
    assert [o.op for o in run["review"].approved] == ["update"]
    fake_apply(store, run["run_id"])
    assert len(store.belief("data-structures")) == n_before


def test_fully_unreadable_course_blocks_everything(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    failed = Reading("data-structures", "https://lms.example.edu/d2l/home/41001", READ_AT, status=STATUS_ERROR, error="login wall")
    run = plan_run(store, [failed])
    assert run["diff"].changes == [] and run["review"].approved == []
    assert any(c.type == UNREADABLE and c.course_id == "data-structures" for c in run["diff"].unreadable)
