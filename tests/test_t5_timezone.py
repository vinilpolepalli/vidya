"""T5. The calendar is America/New_York. An 11:59 PM deadline lands at 11:59 PM
Eastern. Not 11:59 AM, not UTC, not the following day."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from syllabot.calendar_plan import build_plan
from syllabot.dates import parse_date_text
from syllabot.fixtures import load_readings
from syllabot.pipeline import plan_run
from syllabot.selftest import t5_timezone


def test_selftest_t5(fixtures, tmp_path):
    chk = t5_timezone(fixtures, tmp_path)
    assert chk.passed, chk.failures


def test_1159pm_is_1159pm_eastern():
    r = parse_date_text("Due Oct 16 by 11:59 PM", "2026-09-05")
    dt = datetime.fromisoformat(r.start)
    assert dt.tzinfo is not None
    assert (dt.hour, dt.minute) == (23, 59)
    assert dt.utcoffset() == ZoneInfo("America/New_York").utcoffset(dt)
    assert dt.astimezone(timezone.utc).isoformat() == "2026-10-17T03:59:00+00:00"
    assert dt.date().isoformat() == "2026-10-16"


def test_dst_boundary_offsets():
    assert parse_date_text("Oct 31 11:59 PM", "2026-09-05").start.endswith("-04:00")
    assert parse_date_text("Nov 1 11:59 PM", "2026-09-05").start.endswith("-05:00")


def test_course_timezone_is_configurable():
    r = parse_date_text("Oct 16 11:59 PM", "2026-09-05", tz="America/Los_Angeles")
    assert r.start == "2026-10-16T23:59:00-07:00"
    assert any("America/Los_Angeles" in a for a in r.assumptions)


def test_calendar_ops_carry_timezone_and_exclusive_allday_end(store, fixtures):
    run = plan_run(store, load_readings("day0", fixtures))
    ops = {o.key: o for o in run["ops"]}
    timed = ops["data-structures::homework 1"]
    assert timed.timezone == "America/New_York"
    assert timed.start == "2026-09-19T23:59:00-04:00" and timed.all_day is False
    multi = ops["modern-history::midterm essay"]
    assert multi.all_day and multi.start == "2026-10-22" and multi.end == "2026-10-25"  # inclusive 22..24
    single = ops["physics-1::exam 1"]
    assert single.all_day and single.start == "2026-10-07" and single.end == "2026-10-08"
