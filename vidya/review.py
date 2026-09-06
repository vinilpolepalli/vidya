"""The review gate. Nothing is written to a calendar without passing here.

The diff already refuses to emit destructive changes on failed reads; this
second pass checks the concrete operations, because that is what the plan
hands to the bot, and it is the last place a bad write can be stopped.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from .dates import NEEDS_REVIEW_BELOW
from .model import OP_CREATE, OP_DELETE, OP_UPDATE, UNREADABLE, CalendarOp, DiffResult, ReviewResult

MAX_DELETES_PER_COURSE = 2
PAST_WINDOW_DAYS = 120
FUTURE_WINDOW_DAYS = 400


def review_plan(
    ops: list[CalendarOp],
    diff: DiffResult,
    belief_counts: dict[str, int],
    today: Optional[date] = None,
) -> ReviewResult:
    today = today or date.today()
    result = ReviewResult()
    unreadable = {c.course_id for c in diff.unreadable if c.type == UNREADABLE}
    changed_by_key = {c.key: c for c in diff.changes}
    deletes_by_course: dict[str, int] = {}
    for op in ops:
        if op.op == OP_DELETE:
            deletes_by_course[op.course_id] = deletes_by_course.get(op.course_id, 0) + 1

    for op in ops:
        reason = _block_reason(op, unreadable, changed_by_key, belief_counts, deletes_by_course, today)
        if reason:
            result.blocked.append({"op": op.to_dict(), "reason": reason})
        else:
            result.approved.append(op)

    if result.blocked:
        result.notes.append(f"{len(result.blocked)} operation(s) blocked; see blocked[].reason")
    if diff.pending_removals:
        result.notes.append(f"{len(diff.pending_removals)} item(s) missing once; no deletion until confirmed on a later day")
    n_unreadable = sum(1 for c in diff.unreadable if c.type == UNREADABLE)
    if n_unreadable:
        result.notes.append(f"{n_unreadable} course(s) unreadable; their beliefs were left untouched")
    if diff.needs_review:
        result.notes.append(f"{len(diff.needs_review)} item(s) need review and were not written")
    return result


def _block_reason(
    op: CalendarOp,
    unreadable: set[str],
    changed_by_key: dict[str, Any],
    belief_counts: dict[str, int],
    deletes_by_course: dict[str, int],
    today: date,
) -> str:
    if op.op not in (OP_CREATE, OP_UPDATE, OP_DELETE):
        return f"unknown op '{op.op}'"
    if op.course_id in unreadable:
        return "course was unreadable this run"
    ch = changed_by_key.get(op.key)
    if ch is None:
        return "operation has no matching change in this run's diff"
    ev = ch.after if op.op != OP_DELETE else ch.before
    if ev is None:
        return "operation has no event"
    if ev.needs_review:
        return f"event needs review: {ev.review_reason}"
    if ev.confidence < NEEDS_REVIEW_BELOW:
        return f"confidence {ev.confidence:.2f} below {NEEDS_REVIEW_BELOW}"
    if op.op in (OP_UPDATE, OP_DELETE) and not op.event_id:
        return "update/delete without a ledger event id"
    if op.op == OP_DELETE:
        if ch.type != "removed" or "confirmed" not in ch.note:
            return "delete without a confirmed removal"
        count = belief_counts.get(op.course_id, 0)
        n = deletes_by_course.get(op.course_id, 0)
        if n > MAX_DELETES_PER_COURSE and n * 2 >= max(count, 1):
            return (f"mass deletion: {n} of {count} events in {op.course_id} would be removed in one run; "
                    "confirm manually")
        return ""
    if op.start is None:
        return "no start date"
    start_day = _day(op.start)
    if start_day < today - timedelta(days=PAST_WINDOW_DAYS):
        return f"start {start_day} is more than {PAST_WINDOW_DAYS} days in the past"
    if start_day > today + timedelta(days=FUTURE_WINDOW_DAYS):
        return f"start {start_day} is more than {FUTURE_WINDOW_DAYS} days ahead"
    return ""


def _day(iso: str) -> date:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(iso[:10])
