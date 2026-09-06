import json

from syllabot.digest import build_digest
from syllabot.fixtures import load_readings
from syllabot.graph import episode_uuid, export_episodes
from syllabot.pipeline import fake_apply, plan_run


def two_nights(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    run = plan_run(store, load_readings("day1", fixtures))
    fake_apply(store, run["run_id"])
    return boot["run_id"], run["run_id"]


def test_digest_lists_upcoming_moves_and_volatility(store, fixtures):
    two_nights(store, fixtures)
    text = build_digest(store, weeks=2)
    assert "Due in the next 14 days" in text
    assert "Homework 1 — CS 201 Data Structures 11:59 PM" in text
    assert "MOVED — CS 201 Data Structures: Midterm 1" in text
    assert "ADDED — MATH 240 Linear Algebra: Problem Set 5" in text
    assert "most volatile: CS 201 Data Structures (1 move(s))" in text
    assert "Pending removals (1)" in text and "Lab Report 2" in text
    assert "Needs your decision" in text and "Museum visit" in text


def test_digest_on_empty_state(store):
    text = build_digest(store)
    assert "nothing on the calendar" in text
    assert "no changes detected" in text
    assert "no deadline has moved yet" in text


def test_graph_episodes_cover_changes_and_snapshots(store, fixtures):
    _, run2 = two_nights(store, fixtures)
    eps = export_episodes(store, run2, group_id="student-42")
    kinds = [e["name"].split(":")[0] for e in eps]
    assert kinds.count("moved") == 1 and kinds.count("added") == 1 and kinds.count("reworded") == 1
    assert kinds.count("snapshot") == 6
    moved = next(e for e in eps if e["name"].startswith("moved"))
    assert "2026-10-14T11:00:00-04:00" in moved["episode_body"] and "2026-10-16T11:00:00-04:00" in moved["episode_body"]
    assert moved["group_id"] == "student-42" and moved["source"] == "text"
    assert moved["reference_time"].startswith("2026-09-06")
    snap = next(e for e in eps if e["name"].startswith("snapshot: CS 201"))
    body = json.loads(snap["episode_body"])
    assert body["course"]["id"] == "data-structures" and len(body["items"]) >= 5
    # deterministic ids: re-exporting a run cannot duplicate episodes
    assert [e["uuid"] for e in eps] == [e["uuid"] for e in export_episodes(store, run2, group_id="student-42")]
    assert episode_uuid("r", "k", "moved") != episode_uuid("r", "k", "added")
