"""T3. Feed the empty-file fixture. Correct: report the page as unreadable,
change nothing. A deletion requires the item to be absent on two consecutive
successful reads on different days; an error read is not a successful read."""

from syllabot.diff import diff_course
from syllabot.fake_calendar import FakeCalendar
from syllabot.fixtures import load_readings
from syllabot.model import OP_DELETE, REMOVED, STATUS_ERROR, Reading
from syllabot.pipeline import fake_apply, plan_run
from syllabot.resolve import resolve_reading
from syllabot.selftest import t3_destructive_write_guard


def test_selftest_t3(fixtures, tmp_path):
    chk = t3_destructive_write_guard(fixtures, tmp_path)
    assert chk.passed, chk.failures


def test_empty_page_changes_nothing(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    before = store.belief("microeconomics")
    run = plan_run(store, load_readings("day1", fixtures))
    assert [o for o in run["ops"] if o.op == OP_DELETE] == []
    assert any(u.course_id == "microeconomics" for u in run["diff"].unreadable)
    fake_apply(store, run["run_id"])
    assert [e.key for e in store.belief("microeconomics")] == [e.key for e in before]


def test_error_read_does_not_count_toward_removal(fixtures):
    day0 = next(r for r in load_readings("day0", fixtures) if r.course_id == "physics-1")
    events, _ = resolve_reading(day0)
    day1 = next(r for r in load_readings("day1", fixtures) if r.course_id == "physics-1")

    # night 1: successful read, Lab Report 2 gone -> pending (1/2)
    res1, belief1, missing1 = diff_course("physics-1", events, day1, {})
    assert [c.title for c in res1.pending_removals] == ["Lab Report 2"]
    assert res1.changes == []
    assert len(belief1) == len(events)

    # night 2: the read FAILS -> nothing advances
    err = Reading("physics-1", day1.source_url, "2026-09-07T23:00:00-04:00", status=STATUS_ERROR, error="login wall")
    res2, belief2, missing2 = diff_course("physics-1", belief1, err, missing1)
    assert res2.changes == [] and res2.pending_removals == []
    assert len(res2.unreadable) == 1
    assert missing2 == missing1
    assert len(belief2) == len(events)

    # night 3: successful read, still gone -> confirmed removal
    day3 = Reading.from_dict({**day1.to_dict(), "read_at": "2026-09-08T23:00:00-04:00"})
    res3, belief3, missing3 = diff_course("physics-1", belief2, day3, missing2)
    assert [c.type for c in res3.changes] == [REMOVED]
    assert "physics-1::lab report 2" not in {e.key for e in belief3}
    assert missing3 == {}


def test_item_reappearing_clears_pending_removal(fixtures):
    day0 = next(r for r in load_readings("day0", fixtures) if r.course_id == "physics-1")
    events, _ = resolve_reading(day0)
    day1 = next(r for r in load_readings("day1", fixtures) if r.course_id == "physics-1")
    _, belief1, missing1 = diff_course("physics-1", events, day1, {})
    assert missing1
    back = Reading.from_dict({**day0.to_dict(), "read_at": "2026-09-07T23:00:00-04:00"})
    res, belief2, missing2 = diff_course("physics-1", belief1, back, missing1)
    assert missing2 == {}
    assert res.changes == [] and res.pending_removals == []


def test_date_becoming_tbd_is_not_a_removal(fixtures):
    day0 = next(r for r in load_readings("day0", fixtures) if r.course_id == "physics-1")
    events, _ = resolve_reading(day0)
    d = day0.to_dict()
    d["read_at"] = "2026-09-06T23:00:00-04:00"
    for it in d["items"]:
        if it["title"] == "Exam 1":
            it["date_text"] = "TBD"
    res, belief, missing = diff_course("physics-1", events, Reading.from_dict(d), {})
    assert res.pending_removals == [] and res.changes == []
    assert any(e.key == "physics-1::exam 1" for e in belief)
    assert any("calendar keeps" in e.review_reason for e in res.needs_review)
