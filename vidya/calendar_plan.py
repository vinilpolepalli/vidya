"""Turn confirmed changes into calendar operations with idempotency keys.

The ledger maps item key -> calendar event id. Every event description also
carries a `vidya-key:` marker so an event can be found again even if the
ledger is lost. Creating an item whose key is already in the ledger becomes an
update of the existing event, which is what makes a re-run after a crash safe.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from .model import (
    ADDED, COLOR_PEACOCK, COLOR_TOMATO, KIND_CLASS, KIND_EXAM, MOVED, OP_CREATE,
    OP_DELETE, OP_UPDATE, REMOVED, REWORDED, CalendarOp, DiffResult, Event,
)

MARKER = "vidya-key:"


def build_plan(
    diff: DiffResult,
    ledger: dict[str, dict[str, Any]],
    course_names: Optional[dict[str, str]] = None,
    tz: str = "America/New_York",
) -> list[CalendarOp]:
    names = course_names or {}
    ops: list[CalendarOp] = []
    for ch in diff.changes:
        if ch.type in (ADDED, MOVED, REWORDED):
            assert ch.after is not None
            entry = ledger.get(ch.key) or (ledger.get(ch.before.key) if ch.before else None)
            replaces = ch.before.key if (ch.type == REWORDED and ch.before and ch.before.key != ch.key) else None
            if entry and entry.get("event_id"):
                ops.append(_op(OP_UPDATE, ch.after, names, tz, event_id=entry["event_id"],
                               reason=f"{ch.type}: {ch.note}" if ch.type != ADDED else
                               "added, but key already in ledger; re-syncing existing event",
                               replaces_key=replaces))
            else:
                ops.append(_op(OP_CREATE, ch.after, names, tz,
                               reason=f"{ch.type}: {ch.note}" + ("" if ch.type == ADDED else " (not in ledger; creating)"),
                               replaces_key=replaces))
        elif ch.type == REMOVED:
            assert ch.before is not None
            entry = ledger.get(ch.key)
            if entry and entry.get("event_id"):
                ops.append(_op(OP_DELETE, ch.before, names, tz, event_id=entry["event_id"],
                               reason=f"removed: {ch.note}"))
            # not in the ledger: nothing of ours to delete
    return ops


def _op(op: str, ev: Event, names: dict[str, str], tz: str, event_id: Optional[str] = None,
        reason: str = "", replaces_key: Optional[str] = None) -> CalendarOp:
    start, end = _api_bounds(ev)
    return CalendarOp(
        replaces_key=replaces_key,
        op=op,
        key=ev.key,
        course_id=ev.course_id,
        summary=summary_for(ev, names),
        start=start,
        end=end,
        all_day=ev.all_day,
        timezone=tz,
        color_id=COLOR_PEACOCK if ev.kind == KIND_CLASS else COLOR_TOMATO,
        description=description_for(ev),
        event_id=event_id,
        reason=reason,
    )


def summary_for(ev: Event, names: dict[str, str]) -> str:
    course = names.get(ev.course_id, ev.course_id)
    if ev.kind == KIND_EXAM:
        return f"Exam: {ev.title} ({course})"
    if ev.kind == KIND_CLASS:
        return f"{ev.title} ({course})"
    return f"Due: {ev.title} ({course})"


def description_for(ev: Event) -> str:
    lines = [
        f"Course: {ev.course_id}",
        f"Kind: {ev.kind}",
        f'As written: "{ev.date_text}"',
    ]
    for s in ev.sources:
        lines.append(f"Source: {s} (read {ev.read_at})")
    if ev.assumptions:
        lines.append("Assumptions: " + "; ".join(ev.assumptions))
    lines.append(f"Confidence: {ev.confidence:.2f}")
    if ev.detail:
        lines.append(f"Notes: {ev.detail}")
    lines.append(f"{MARKER} {ev.key}")
    return "\n".join(lines)


def _api_bounds(ev: Event) -> tuple[Optional[str], Optional[str]]:
    """Google Calendar all-day events use an exclusive end date."""
    if ev.start is None:
        return None, None
    if ev.all_day:
        end_inclusive = date.fromisoformat((ev.end or ev.start)[:10])
        return ev.start[:10], (end_inclusive + timedelta(days=1)).isoformat()
    return ev.start, ev.end or ev.start


def apply_results_to_ledger(ledger: dict[str, dict[str, Any]], results: list[dict[str, Any]],
                            applied_at: str, plan: Optional[list[CalendarOp]] = None) -> dict[str, dict[str, Any]]:
    """results: [{"key", "op", "event_id", "status": "ok"|"failed", ...}] as
    reported by whoever applied the ops (the bot via its calendar plugin, or the
    fake calendar). Only successful ops touch the ledger. `plan` supplies the
    replaces_key for reworded items so the retired key is dropped."""
    replaces = {(o.key, o.op): o.replaces_key for o in (plan or []) if o.replaces_key}
    new = {k: dict(v) for k, v in ledger.items()}
    for r in results:
        if r.get("status") != "ok":
            continue
        key = r["key"]
        if r["op"] == OP_DELETE:
            new.pop(key, None)
        else:
            new[key] = {"event_id": r.get("event_id"), "summary": r.get("summary"),
                        "start": r.get("start"), "end": r.get("end"), "written_at": applied_at}
            old = r.get("replaces_key") or replaces.get((key, r["op"]))
            if old and old != key:
                new.pop(old, None)
    return new
