"""Course tutor: the code decides when, the model teaches. Classes land on
session days, review sits right before each exam, weak concepts come back."""

from datetime import date

import pytest

from vidya.fixtures import load_readings
from vidya.pipeline import fake_apply, plan_run
from vidya.teach import Mastery, build_map, render_map

TOPICS = [{"title": t, "source": f"syllabus week {i + 1}"} for i, t in enumerate(
    ["Arrays and complexity", "Linked lists", "Stacks and queues", "Recursion", "Trees", "Binary search trees",
     "Heaps", "Hashing", "Graphs", "Shortest paths", "Sorting", "Dynamic programming"])]


@pytest.fixture
def taught(store, fixtures):
    run = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, run["run_id"])
    return store


def test_map_uses_believed_exams_and_reviews_before_each(taught):
    plan = build_map(taught, "data-structures", TOPICS, date(2026, 9, 7), per_week=2)
    exams = [e["title"] for e in plan["exams"]]
    assert exams == ["Midterm 1", "Final Exam"]
    kinds = [(c["kind"], c["date"]) for c in plan["classes"]]
    # every taught class is on a Monday or Wednesday
    for c in plan["classes"]:
        if c["kind"] != "exam":
            assert date.fromisoformat(c["date"]).weekday() in (0, 2)
    # a review sits immediately before each exam entry, and nothing is scheduled after the final
    for i, (kind, d) in enumerate(kinds):
        if kind == "exam":
            assert kinds[i - 1][0] == "review"
            assert kinds[i - 1][1] < d
    assert kinds[-1][0] == "exam" and plan["classes"][-1]["for_exam"] == "Final Exam"
    # all topics placed, in order, none after their exam
    placed = [t for c in plan["classes"] if c["kind"] == "class" for t in c["topics"]]
    assert placed == [t["title"] for t in TOPICS]
    midterm_date = plan["exams"][0]["date"]
    before = [t for c in plan["classes"] if c["kind"] == "class" and c["date"] < midterm_date for t in c["topics"]]
    assert before and before[0] == "Arrays and complexity"
    text = render_map(taught, plan)
    assert "semester map" in text and "EXAM — Midterm 1" in text and "review for Final Exam" in text


def test_tagged_topics_go_to_their_exam(taught):
    topics = [{"title": "A", "exam": "Midterm 1"}, {"title": "B", "exam": "Midterm 1"}, {"title": "C", "exam": "Final Exam"}]
    plan = build_map(taught, "data-structures", topics, date(2026, 9, 7))
    mid = plan["exams"][0]["date"]
    for c in plan["classes"]:
        if c["kind"] == "class":
            for t in c["topics"]:
                assert (c["date"] < mid) == (t in ("A", "B"))


def test_map_without_exams_spans_default_weeks(store):
    plan = build_map(store, "modern-history", TOPICS[:4], date(2026, 9, 7), per_week=1, weeks_if_no_exam=6)
    assert any("no exam dates" in n for n in plan["notes"])
    assert plan["classes"][-1]["kind"] == "exam" and plan["classes"][-1]["for_exam"] == "end of term"
    assert all(date.fromisoformat(c["date"]).weekday() == 1 for c in plan["classes"] if c["kind"] != "exam")  # Tuesdays


def test_mastery_ledger_tracks_weak_concepts(store):
    m = Mastery(store, "data-structures")
    m.record("Recursion", 0, note="confused about base cases")
    m.record("Trees", 2)
    m.record("Recursion", 1)
    assert [c for c, _, _ in m.weak()] == ["Recursion"]
    m.record("Recursion", 3, note="taught it back")
    assert m.weak() == []
    assert m.summary() == {"concepts": 2, "weak": 0, "solid": 2}
    with pytest.raises(ValueError):
        m.record("Heaps", 5)
