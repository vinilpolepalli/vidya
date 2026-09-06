"""T6. Seed a Canvas sandbox course with three known items. Point the same loop
at it with no code changes: it finds all three. The loop is generic over
Readings; only the extractor knows what Canvas is."""

from pathlib import Path

from vidya.extract.canvas import extract_canvas_files, items_from_canvas
from vidya.fixtures import fixture_dir, load_readings
from vidya.model import OP_CREATE
from vidya.pipeline import fake_apply, plan_run
from vidya.store import Store

CANVAS = fixture_dir() / "canvas"
READ_AT = "2026-09-06T23:00:00-04:00"


def canvas_reading(course_id="sandbox"):
    return extract_canvas_files(course_id, "https://canvas.example.edu/courses/777", READ_AT,
                                str(CANVAS / "sandbox_assignments.json"),
                                str(CANVAS / "sandbox_announcements.json"), None)


def test_three_known_items_found():
    r = canvas_reading()
    assert r.ok
    titles = sorted(i.title for i in r.items)
    assert titles == ["Guest lecture", "Lab 1: Setup", "Midterm Exam"]


def test_exact_timestamps_land_in_course_timezone(tmp_path):
    store = Store(tmp_path / "s")
    store.init(courses=[{"id": "sandbox", "name": "Canvas Sandbox", "platform": "canvas",
                         "url": "https://canvas.example.edu/courses/777"}])
    run = plan_run(store, [canvas_reading()])
    ops = {o.key: o for o in run["review"].approved}
    assert len(ops) == 3 and all(o.op == OP_CREATE for o in ops.values())
    # 2026-09-20T03:59:00Z is 11:59 PM Eastern on Sep 19
    assert ops["sandbox::lab 1 setup"].start == "2026-09-19T23:59:00-04:00"
    assert ops["sandbox::midterm exam"].start == "2026-10-16T11:00:00-04:00"
    assert ops["sandbox::guest lecture"].all_day and ops["sandbox::guest lecture"].start == "2026-10-22"


def test_unpublished_and_dateless_are_ignored():
    r = canvas_reading()
    assert not any("Unpublished" in i.title for i in r.items)
    assert not any(i.title == "Welcome" for i in r.items)


def test_same_loop_mixes_brightspace_and_canvas_in_one_run(tmp_path, fixtures):
    """One store, two platforms, one nightly diff. No platform-specific branch anywhere."""
    from vidya.fixtures import load_courses
    store = Store(tmp_path / "s")
    courses = load_courses(fixtures) + [{"id": "sandbox", "name": "Canvas Sandbox", "platform": "canvas",
                                         "url": "https://canvas.example.edu/courses/777"}]
    store.init(courses=courses)
    boot = plan_run(store, load_readings("day0", fixtures) + [canvas_reading()])
    fake_apply(store, boot["run_id"])
    assert len(store.belief("sandbox")) == 3
    # a Canvas due date moves by a day
    moved = [dict(a) for a in __import__("json").loads((CANVAS / "sandbox_assignments.json").read_text())]
    for a in moved:
        if a["name"] == "Midterm Exam":
            a["due_at"] = "2026-10-17T15:00:00Z"
    p = tmp_path / "moved.json"
    p.write_text(__import__("json").dumps(moved))
    r = extract_canvas_files("sandbox", "https://canvas.example.edu/courses/777", "2026-09-07T23:00:00-04:00",
                             str(p), str(CANVAS / "sandbox_announcements.json"), None)
    run = plan_run(store, load_readings("day1", fixtures, read_at="2026-09-07T23:00:00-04:00") + [r])
    canvas_changes = [c for c in run["diff"].changes if c.course_id == "sandbox"]
    assert [(c.type, c.title) for c in canvas_changes] == [("moved", "Midterm Exam")]
    assert canvas_changes[0].after.start == "2026-10-17T11:00:00-04:00"


def test_calendar_events_endpoint_shape():
    events = [{"title": "Field trip", "start_at": "2026-11-03T14:00:00Z", "end_at": "2026-11-03T18:00:00Z",
               "all_day": False, "html_url": "https://canvas.example.edu/calendar?event_id=1"},
              {"title": "Reading day", "start_at": "2026-10-20T04:00:00Z", "all_day": True, "all_day_date": "2026-10-20"}]
    items = items_from_canvas([], [], events)
    assert [(i.title, i.start, i.all_day) for i in items] == [
        ("Field trip", "2026-11-03T14:00:00Z", False), ("Reading day", "2026-10-20", True)]
