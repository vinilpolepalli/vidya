"""T1. Run the diff from day0 to day1. Expected output is exactly the planted
changes. Anything extra is noise, anything missing is a bug."""

from vidya.fixtures import load_expected, load_readings
from vidya.model import ADDED, MOVED, REWORDED
from vidya.pipeline import fake_apply, plan_run
from vidya.selftest import expected_summary, summarize_diff, t1_known_answer_diff


def test_selftest_t1(fixtures, tmp_path):
    chk = t1_known_answer_diff(fixtures, tmp_path)
    assert chk.passed, chk.failures


def test_day1_diff_is_exactly_the_planted_changes(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    assert {c.type for c in boot["diff"].changes} == {ADDED}
    fake_apply(store, boot["run_id"])

    run = plan_run(store, load_readings("day1", fixtures))
    assert summarize_diff(run["diff"]) == expected_summary(load_expected(fixtures))

    by_type = {c.type: c for c in run["diff"].changes}
    moved = by_type[MOVED]
    assert moved.before.start == "2026-10-14T11:00:00-04:00"
    assert moved.after.start == "2026-10-16T11:00:00-04:00"
    reworded = by_type[REWORDED]
    assert reworded.before.title == "Essay 1 draft"
    assert reworded.after.title == "Essay 1: first draft"
    assert reworded.before.same_schedule(reworded.after)


def test_page_noise_never_appears_as_a_change(store, fixtures):
    """modern-history is byte-different between nights (timestamps, session ids)
    but semantically identical: zero changes for it."""
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    run = plan_run(store, load_readings("day1", fixtures))
    touched = {c.course_id for c in run["diff"].changes + run["diff"].pending_removals + run["diff"].unreadable}
    assert "modern-history" not in touched
