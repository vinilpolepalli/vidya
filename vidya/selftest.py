"""Built-in fixture suite. `vidya selftest` runs it without pytest.

Checks mirror tests/ so an installer can prove the loop on a clean machine:

  T1  known-answer diff      day0 -> day1 yields exactly the planted changes
  T2  idempotency            replaying a night creates nothing twice
  T3  destructive-write guard an empty page deletes nothing; a removal needs
                             two successful reads on different days
  T4  date parsing           the adversarial set
  T5  timezone               11:59 PM lands at 11:59 PM Eastern, not UTC
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .dates import parse_date_text
from .fake_calendar import FakeCalendar
from .fixtures import fixture_dir, load_courses, load_expected, load_readings
from .model import OP_CREATE, OP_DELETE, REMOVED
from .normalize import slug
from .pipeline import fake_apply, plan_run
from .store import Store


class Check:
    def __init__(self, name: str):
        self.name = name
        self.failures: list[str] = []
        self.notes: list[str] = []

    def ok(self, cond: bool, msg: str) -> None:
        if not cond:
            self.failures.append(msg)

    @property
    def passed(self) -> bool:
        return not self.failures


def fresh_store(root: Path, fixtures: Path) -> Store:
    store = Store(root)
    store.init(courses=load_courses(fixtures))
    return store


def bootstrap_day0(store: Store, fixtures: Path) -> dict[str, Any]:
    run = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, run["run_id"])
    return run


def summarize_diff(diff) -> dict[str, list[tuple]]:
    return {
        "changes": sorted((c.type, c.course_id, slug(c.title)) for c in diff.changes),
        "pending_removals": sorted((c.course_id, slug(c.title)) for c in diff.pending_removals),
        "unreadable": sorted(c.course_id for c in diff.unreadable),
    }


def expected_summary(expected: dict[str, Any]) -> dict[str, list[tuple]]:
    return {
        "changes": sorted((c["type"], c["course_id"], slug(c["title"])) for c in expected.get("changes", [])),
        "pending_removals": sorted((c["course_id"], slug(c["title"])) for c in expected.get("pending_removals", [])),
        "unreadable": sorted(c["course_id"] for c in expected.get("unreadable", [])),
    }


# ---------------------------------------------------------------------------

def t1_known_answer_diff(fixtures: Path, root: Path) -> Check:
    c = Check("T1 known-answer diff (day0 -> day1)")
    store = fresh_store(root / "t1", fixtures)
    boot = bootstrap_day0(store, fixtures)
    c.ok(all(ch.type == "added" for ch in boot["diff"].changes), "first run should only add")
    run = plan_run(store, load_readings("day1", fixtures))
    got, want = summarize_diff(run["diff"]), expected_summary(load_expected(fixtures))
    for k in want:
        c.ok(got[k] == want[k], f"{k}: expected {want[k]}, got {got[k]}")
    total = len(got["changes"]) + len(got["pending_removals"]) + len(got["unreadable"])
    c.notes.append(f"{total} planted changes detected, 0 noise")
    return c


def t2_idempotency(fixtures: Path, root: Path) -> Check:
    c = Check("T2 idempotency (replay creates nothing twice)")
    store = fresh_store(root / "t2", fixtures)
    bootstrap_day0(store, fixtures)
    n0 = len(FakeCalendar(store.fake_calendar_path))
    # (a) same night replayed after commit: empty diff, zero ops
    run = plan_run(store, load_readings("day0", fixtures))
    c.ok(run["diff"].changes == [], f"replay after commit produced changes: {summarize_diff(run['diff'])}")
    c.ok(run["review"].approved == [], "replay after commit produced calendar ops")
    fake_apply(store, run["run_id"])
    c.ok(len(FakeCalendar(store.fake_calendar_path)) == n0, "replay after commit changed the calendar")
    # (b) crash between apply and commit: writes were recorded as they happened,
    #     commit never ran. The next plan must recover them and create nothing twice.
    r1 = plan_run(store, load_readings("day1", fixtures))
    creates1 = [o for o in r1["review"].approved if o.op == OP_CREATE]
    c.ok(len(creates1) == 1, f"first day1 plan should create exactly one event, got {len(creates1)}")
    cal = FakeCalendar(store.fake_calendar_path)
    for res in cal.apply(r1["review"].approved):
        store.record_partial(r1["run_id"], res)   # what the bot does after each plugin call
    n_applied = len(FakeCalendar(store.fake_calendar_path))
    r2 = plan_run(store, load_readings("day1", fixtures))  # crash happened; this is the next night
    c.ok(bool(r2["recovered"]), "interrupted run was not recovered from its partial results")
    c.ok(r2["diff"].changes == [], f"after recovery the replay still shows changes: {summarize_diff(r2['diff'])}")
    c.ok(all(o.op != OP_CREATE for o in r2["review"].approved), "recovered replay planned a create (duplicate)")
    fake_apply(store, r2["run_id"])
    final = FakeCalendar(store.fake_calendar_path)
    c.ok(len(final) == n_applied, f"event count changed on replay: {n_applied} -> {len(final)}")
    c.ok(len(final.by_key()) == len(final), "calendar holds two events with the same key (duplicate)")
    # (c) a third replay after everything is committed: zero ops
    r3 = plan_run(store, load_readings("day1", fixtures))
    c.ok(r3["review"].approved == [], "committed replay produced calendar ops")
    c.notes.append(f"{n0} events after day0, {n_applied} after day1, replays add 0, no duplicate keys")
    return c


def t3_destructive_write_guard(fixtures: Path, root: Path) -> Check:
    c = Check("T3 destructive-write guard (empty page, two-read removal)")
    store = fresh_store(root / "t3", fixtures)
    bootstrap_day0(store, fixtures)
    before = {cid: len(evs) for cid, evs in store.all_belief().items()}
    run = plan_run(store, load_readings("day1", fixtures))
    deletes = [o for o in run["ops"] if o.op == OP_DELETE]
    c.ok(deletes == [], f"day1 planned {len(deletes)} delete(s); the empty page and first absence must not delete")
    c.ok(any(u.course_id == "microeconomics" for u in run["diff"].unreadable), "empty page not reported unreadable")
    fake_apply(store, run["run_id"])
    after = {cid: len(evs) for cid, evs in store.all_belief().items()}
    c.ok(after["microeconomics"] == before["microeconomics"],
         f"belief for the unreadable course changed: {before['microeconomics']} -> {after['microeconomics']}")
    c.ok(after["physics-1"] == before["physics-1"],
         "pending removal dropped from belief after one absence")
    # same day again: still pending, no delete
    run_same = plan_run(store, load_readings("day1", fixtures))
    c.ok(all(o.op != OP_DELETE for o in run_same["ops"]), "second read on the same day confirmed a removal")
    fake_apply(store, run_same["run_id"])
    # a later day with the item still absent: confirmed removal, exactly one delete
    run2 = plan_run(store, load_readings("day1", fixtures, read_at="2026-09-07T23:00:00-04:00"))
    removed = [ch for ch in run2["diff"].changes if ch.type == REMOVED]
    deletes2 = [o for o in run2["review"].approved if o.op == OP_DELETE]
    c.ok(len(removed) == 1 and slug(removed[0].title) == "lab report 2", f"expected one confirmed removal, got {[(r.course_id, r.title) for r in removed]}")
    c.ok(len(deletes2) == 1, f"expected exactly one approved delete, got {len(deletes2)}")
    n_before = len(FakeCalendar(store.fake_calendar_path))
    fake_apply(store, run2["run_id"])
    c.ok(len(FakeCalendar(store.fake_calendar_path)) == n_before - 1, "confirmed removal did not delete exactly one event")
    c.notes.append("empty page: 0 deletions; absence confirmed on day 2: 1 deletion")
    return c


ADVERSARIAL: list[tuple[str, str | None, Callable[[Any], bool], str]] = [
    ("Due Friday 10/16 by 11:59pm", None,
     lambda r: r.start == "2026-10-16T23:59:00-04:00" and not r.needs_review, "Oct 16 23:59 course tz"),
    ("Week of Oct 12", None, lambda r: r.needs_review and r.start is None, "needs review, never Oct 12 midnight"),
    ("Next Friday", "2026-10-05",
     lambda r: r.start == "2026-10-09" and r.needs_review, "resolves against the post date (Oct 9) and is flagged"),
    ("Dec 18, finals", None, lambda r: r.start == "2026-12-18" and not r.needs_review, "same year, no roll-forward"),
    ("TBD", None, lambda r: r.needs_review and r.start is None, "needs review, no event"),
    ("Oct 14 changed to Oct 16", None,
     lambda r: r.start == "2026-10-16" and r.end == "2026-10-16" and not r.needs_review, "one event on the 16th"),
    ("Oct 16 at 5pm", None,
     lambda r: r.start == "2026-10-16T17:00:00-04:00" and any("assumed course timezone" in a for a in r.assumptions),
     "course tz assumed and recorded"),
    ("Oct 20 to 22", None, lambda r: r.start == "2026-10-20" and r.end == "2026-10-22" and r.all_day, "one multi-day event"),
    ("before class", None, lambda r: r.needs_review and r.start is None, "needs review"),
    ("Mon/Wed 3:30-4:45 PM", None, lambda r: r.needs_review, "recurring meeting goes to review"),
]


def t4_date_parsing(fixtures: Path, root: Path) -> Check:
    c = Check("T4 date parsing (adversarial set)")
    ref = "2026-09-05T23:00:00-04:00"
    for text, posted, pred, why in ADVERSARIAL:
        r = parse_date_text(text, ref, posted_at=posted)
        c.ok(pred(r), f"{text!r}: expected {why}; got start={r.start} end={r.end} review={r.needs_review} ({r.reason})")
    # dedup across sources is checked on the fixtures: Project 1 appears twice, resolves once
    store = fresh_store(root / "t4", fixtures)
    run = plan_run(store, load_readings("day0", fixtures))
    p1 = [ch for ch in run["diff"].changes if ch.course_id == "data-structures" and slug(ch.title) == "project 1"]
    c.ok(len(p1) == 1, f"Project 1 listed twice should resolve to one event, got {len(p1)}")
    c.ok(p1 and len(p1[0].after.sources) == 2, "deduplicated event should keep both source URLs")
    c.ok(p1 and p1[0].after.start == "2026-10-23T23:59:00-04:00", "deduplicated event should keep the source with a clock time")
    c.notes.append(f"{len(ADVERSARIAL)} adversarial strings + cross-source dedup")
    return c


def t5_timezone(fixtures: Path, root: Path) -> Check:
    c = Check("T5 timezone (America/New_York)")
    r = parse_date_text("Oct 16 11:59 PM", "2026-09-05", tz="America/New_York")
    c.ok(r.start == "2026-10-16T23:59:00-04:00", f"expected -04:00 offset in October, got {r.start}")
    dt = datetime.fromisoformat(r.start)
    c.ok(dt.hour == 23 and dt.minute == 59, "local time is not 23:59")
    utc = dt.astimezone(timezone.utc)
    c.ok(utc.hour == 3 and utc.day == 17, f"UTC conversion should be 03:59 on the 17th, got {utc.isoformat()}")
    c.ok(dt.astimezone(ZoneInfo("America/New_York")).date().isoformat() == "2026-10-16", "date shifted")
    r2 = parse_date_text("Dec 18 11:59 PM", "2026-09-05", tz="America/New_York")
    c.ok(r2.start == "2026-12-18T23:59:00-05:00", f"expected -05:00 offset after DST ends, got {r2.start}")
    r3 = parse_date_text("Oct 16 11:59 PM PT", "2026-09-05", tz="America/New_York")
    c.ok(r3.start == "2026-10-17T02:59:00-04:00", f"explicit PT should convert into course tz, got {r3.start}")
    c.notes.append("EDT and EST offsets, UTC round-trip, explicit PT conversion")
    return c


CHECKS = [t1_known_answer_diff, t2_idempotency, t3_destructive_write_guard, t4_date_parsing, t5_timezone]


def run_selftest(fixtures: Path | None = None, keep: Path | None = None) -> tuple[bool, str]:
    fixtures = fixtures or fixture_dir()
    tmp = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="vidya-selftest-"))
    lines = [f"vidya selftest  fixtures={fixtures}"]
    all_ok = True
    try:
        for fn in CHECKS:
            try:
                chk = fn(fixtures, tmp)
            except Exception as e:  # a crash is a failure with a traceback summary
                chk = Check(fn.__doc__ or fn.__name__)
                chk.failures.append(f"crashed: {type(e).__name__}: {e}")
            status = "PASS" if chk.passed else "FAIL"
            all_ok &= chk.passed
            lines.append(f"[{status}] {chk.name}" + (f"  — {'; '.join(chk.notes)}" if chk.notes and chk.passed else ""))
            for f in chk.failures:
                lines.append(f"        - {f}")
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
    lines.append("ALL PASS" if all_ok else "FAILURES PRESENT")
    return all_ok, "\n".join(lines)
