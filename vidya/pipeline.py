"""The nightly loop, split in two phases so a crash between them is safe.

plan_run   : readings -> diff -> plan -> review. Writes runs/<id>/ and returns
             the approved operations for the bot to apply via its calendar plugin.
commit_run : after the ops are applied, record event ids in the ledger and
             advance the belief snapshots. Failed ops keep the old belief for
             their keys so the change is proposed again next night.
fake_apply : plan -> apply to the built-in fake calendar -> commit. Tests and
             dry runs use this.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from .calendar_plan import apply_results_to_ledger, build_plan
from .diff import diff_all
from .fake_calendar import FakeCalendar
from .model import (
    ADDED, MOVED, NOT_READ, OP_CREATE, OP_DELETE, OP_UPDATE, REMOVED, REWORDED,
    CalendarOp, Change, DiffResult, Event, Reading, ReviewResult,
)
from .review import review_plan
from .store import Store


def plan_run(
    store: Store,
    readings: list[Reading],
    run_id: Optional[str] = None,
    today: Optional[date] = None,
) -> dict[str, Any]:
    run_id = run_id or store.new_run_id()
    recovered = recover_uncommitted(store)
    belief = store.all_belief()
    diff = diff_all(belief, readings, store.missing, course_ids=store.course_ids())
    ops = build_plan(diff, store.ledger, store.course_names(), tz=store.timezone)
    counts = {cid: len(evs) for cid, evs in belief.items()}
    if today is None:
        today = max((_day(r.read_at) for r in readings), default=date.today())
    review = review_plan(ops, diff, counts, today=today)
    seen_at = max((r.read_at for r in readings), default=datetime.now(timezone.utc).isoformat())
    store.record_needs_review(diff.needs_review, seen_at)
    open_keys = store.open_review_keys()
    diff.needs_review = [e for e in diff.needs_review if e.key in open_keys]
    summary = summarize(run_id, diff, review, store.course_names(), seen_at)
    if recovered:
        summary += "\n".join(["## Recovery", *[f"- committed interrupted run {r['run_id']} from its partial results "
                                                f"({r['n_results']} recorded write(s))" for r in recovered], ""])
    store.write_run(run_id, readings, diff, ops, review, summary)
    return {"run_id": run_id, "diff": diff, "ops": ops, "review": review, "summary": summary,
            "recovered": recovered}


def recover_uncommitted(store: Store) -> list[dict[str, Any]]:
    """A run that was applied (partial results recorded) but never committed is
    committed now, so its event ids reach the ledger before we plan again.
    A run with no recorded writes is left alone: nothing was written, so its
    changes will simply be proposed again."""
    recovered = []
    for rid in store.uncommitted_runs():
        partial = store.partial_results(rid)
        if partial:
            commit_run(store, rid, partial)
            recovered.append({"run_id": rid, "n_results": len(partial)})
    return recovered


def commit_run(store: Store, run_id: str, results: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    run = store.read_run(run_id)
    if run["meta"].get("committed"):
        return {"run_id": run_id, "already_committed": True}
    results = results or []
    diff = run["diff"]
    applied_at = datetime.now(timezone.utc).isoformat()

    failed_keys = {r["key"] for r in results if r.get("status") != "ok"}
    approved_keys = {o["key"] for o in run["review"].get("approved", [])}
    reported_keys = {r["key"] for r in results}
    # approved but never reported back counts as failed: we cannot know it was written
    failed_keys |= approved_keys - reported_keys
    blocked_keys = {b["op"]["key"] for b in run["review"].get("blocked", [])}
    hold_keys = failed_keys | blocked_keys

    old_belief = store.all_belief()
    for cid, events in diff.get("proposed_belief", {}).items():
        new_events = [Event.from_dict(e) for e in events]
        if hold_keys:
            prev = {e.key: e for e in old_belief.get(cid, [])}
            merged = {e.key: e for e in new_events}
            for k in hold_keys:
                if k.startswith(f"{cid}::"):
                    if k in prev:
                        merged[k] = prev[k]      # keep old belief; change re-proposed next run
                    else:
                        merged.pop(k, None)      # never written; not believed yet
            new_events = sorted(merged.values(), key=lambda e: (e.start or "9999", e.title))
        store.save_belief(cid, new_events, as_of=applied_at)

    missing = diff.get("proposed_missing", {})
    store.save_missing(missing)
    store.save_ledger(apply_results_to_ledger(store.ledger, results, applied_at, plan=run["plan"]))
    store.mark_committed(run_id, results)
    return {"run_id": run_id, "committed": True, "failed_keys": sorted(failed_keys),
            "held_keys": sorted(hold_keys)}


def fake_apply(store: Store, run_id: str) -> list[dict[str, Any]]:
    run = store.read_run(run_id)
    approved = [CalendarOp.from_dict(o) for o in run["review"].get("approved", [])]
    cal = FakeCalendar(store.fake_calendar_path)
    results = cal.apply(approved)
    for r in results:
        store.record_partial(run_id, r)
    commit_run(store, run_id, results)
    return results


def summarize(run_id: str, diff: DiffResult, review: ReviewResult, names: dict[str, str], as_of: str) -> str:
    n = lambda cid: names.get(cid, cid)
    not_read = [c for c in diff.unreadable if c.type == NOT_READ]
    unreadable = [c for c in diff.unreadable if c.type != NOT_READ]
    lines = [f"# Nightly syllabus check ({run_id})", "", f"As of {as_of}.", ""]
    lines.append(
        f"**{len(diff.changes)} change(s)**, {len(diff.pending_removals)} pending removal(s), "
        f"{len(unreadable)} course(s) unreadable, {len(diff.needs_review)} item(s) need review."
        + (f" {len(not_read)} course(s) not read this run." if not_read else "")
    )
    lines.append("")
    if diff.changes:
        lines.append("## Changes")
        for c in diff.changes:
            lines.append(f"- {c.type.upper()} — {n(c.course_id)}: {c.title} — {c.note}")
            src = (c.after or c.before)
            if src and src.sources:
                lines.append(f"  source: {src.sources[0]}")
        lines.append("")
    if diff.pending_removals:
        lines.append("## Pending removals (nothing deleted yet)")
        for c in diff.pending_removals:
            lines.append(f"- {n(c.course_id)}: {c.title} — {c.note}")
        lines.append("")
    if unreadable:
        lines.append("## Unreadable this run (belief left untouched)")
        for c in unreadable:
            lines.append(f"- {n(c.course_id)}: {c.note}")
        lines.append("")
    if not_read:
        lines.append("Not read this run (belief unchanged): " + ", ".join(n(c.course_id) for c in not_read))
        lines.append("")
    if diff.needs_review:
        lines.append("## Needs review (not written to the calendar)")
        for e in diff.needs_review:
            cand = f" candidate {e.start}" if e.start else ""
            lines.append(f"- {n(e.course_id)}: {e.title} — \"{e.date_text}\" — {e.review_reason}{cand}")
        lines.append("")
    kinds = {OP_CREATE: 0, OP_UPDATE: 0, OP_DELETE: 0}
    for o in review.approved:
        kinds[o.op] = kinds.get(o.op, 0) + 1
    lines.append("## Calendar operations")
    lines.append(f"- approved: {len(review.approved)} (create {kinds[OP_CREATE]}, update {kinds[OP_UPDATE]}, delete {kinds[OP_DELETE]})")
    lines.append(f"- blocked: {len(review.blocked)}")
    for b in review.blocked:
        lines.append(f"  - {b['op']['op']} {b['op']['summary']}: {b['reason']}")
    for note in review.notes:
        lines.append(f"- note: {note}")
    lines.append("")
    return "\n".join(lines)


def _day(read_at: str) -> date:
    try:
        return datetime.fromisoformat(read_at.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(read_at[:10])
