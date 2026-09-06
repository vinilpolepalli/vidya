"""Diff last night's belief against tonight's readings.

Invariants enforced here (see tests T1-T3):

* A failed or empty read never produces a deletion. The course's belief is
  left exactly as it was and the course is reported as unreadable.
* A deletion requires the item to be absent on two successful reads made on
  different days. The first absence is reported as pending_removal and the
  event stays in the belief so tomorrow's read can confirm or clear it.
* An item whose date became unparseable (TBD, 'week of') is not a removal.
  The old event stays and the item is reported for review.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from .model import (
    ADDED, MOVED, NOT_READ, PENDING_REMOVAL, REMOVED, REWORDED, SOURCE_FAILED, STATUS_OK, UNREADABLE,
    Change, DiffResult, Event, Reading,
)
from .normalize import title_similarity
from .resolve import resolve_reading

REWORD_THRESHOLD = 0.55
REMOVAL_CONFIRMATIONS = 2


def _read_day(read_at: str) -> date:
    try:
        return datetime.fromisoformat(read_at.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(read_at[:10])


def diff_course(
    course_id: str,
    previous: list[Event],
    reading: Optional[Reading],
    missing: dict[str, dict[str, Any]],
) -> tuple[DiffResult, list[Event], dict[str, dict[str, Any]]]:
    """Diff one course. Returns (result, new_belief, new_missing_entries).

    `missing` holds the pending-removal tracker for this course's keys:
    {key: {"count": int, "first_missing": "YYYY-MM-DD", "last_counted": "YYYY-MM-DD", "event": {...}}}
    """
    result = DiffResult()
    prev_by_key = {e.key: e for e in previous}
    new_missing = {k: dict(v) for k, v in missing.items()}

    if reading is None:
        result.unreadable.append(Change(NOT_READ, course_id, f"{course_id}::*", course_id,
                                        note="no reading produced this run; belief unchanged"))
        return result, list(previous), new_missing

    if reading.status != STATUS_OK:
        result.unreadable.append(Change(UNREADABLE, course_id, f"{course_id}::*", course_id,
                                        note=f"read status '{reading.status}': {reading.error or 'no detail'}; belief unchanged"))
        return result, list(previous), new_missing

    events, review = resolve_reading(reading)
    result.needs_review.extend(review)

    if reading.partial:
        return _diff_partial(course_id, previous, events, result, new_missing)

    if not events and previous:
        result.unreadable.append(Change(UNREADABLE, course_id, f"{course_id}::*", course_id,
                                        note=f"read returned zero dated items but belief holds {len(previous)}; treated as an empty read, belief unchanged"))
        return result, list(previous), new_missing

    cur_by_key = {e.key: e for e in events}
    review_keys = {e.key for e in review}
    added_keys = [k for k in cur_by_key if k not in prev_by_key]
    removed_keys = [k for k in prev_by_key if k not in cur_by_key]

    for k in cur_by_key:
        if k in prev_by_key and not prev_by_key[k].same_schedule(cur_by_key[k]):
            result.changes.append(Change(MOVED, course_id, k, cur_by_key[k].title,
                                         before=prev_by_key[k], after=cur_by_key[k],
                                         note=f"{_fmt(prev_by_key[k])} -> {_fmt(cur_by_key[k])}"))

    # Reworded: a removed and an added item with the same schedule and similar titles.
    pairs: list[tuple[float, str, str]] = []
    for r in removed_keys:
        for a in added_keys:
            if prev_by_key[r].same_schedule(cur_by_key[a]):
                sim = title_similarity(prev_by_key[r].title, cur_by_key[a].title)
                if sim >= REWORD_THRESHOLD:
                    pairs.append((sim, r, a))
    used_r: set[str] = set()
    used_a: set[str] = set()
    for sim, r, a in sorted(pairs, reverse=True):
        if r in used_r or a in used_a:
            continue
        used_r.add(r)
        used_a.add(a)
        result.changes.append(Change(REWORDED, course_id, a, cur_by_key[a].title,
                                     before=prev_by_key[r], after=cur_by_key[a],
                                     note=f"'{prev_by_key[r].title}' -> '{cur_by_key[a].title}' (similarity {sim:.2f})"))
    added_keys = [k for k in added_keys if k not in used_a]
    removed_keys = [k for k in removed_keys if k not in used_r]

    for k in added_keys:
        result.changes.append(Change(ADDED, course_id, k, cur_by_key[k].title, after=cur_by_key[k],
                                     note=_fmt(cur_by_key[k])))

    belief: dict[str, Event] = dict(cur_by_key)
    today = _read_day(reading.read_at)
    for k in removed_keys:
        prev = prev_by_key[k]
        if k in review_keys:
            belief[k] = prev
            marker = next(e for e in review if e.key == k)
            marker.review_reason = f"date became unparseable ({marker.review_reason}); calendar keeps {_fmt(prev)} until you decide"
            continue
        entry = new_missing.get(k)
        if entry is None:
            entry = {"count": 1, "first_missing": today.isoformat(), "last_counted": today.isoformat(),
                     "event": prev.to_dict()}
        elif date.fromisoformat(entry["last_counted"]) < today:
            entry = {**entry, "count": int(entry["count"]) + 1, "last_counted": today.isoformat()}
        if int(entry["count"]) >= REMOVAL_CONFIRMATIONS:
            result.changes.append(Change(REMOVED, course_id, k, prev.title, before=prev,
                                         note=f"absent on {entry['count']} successful reads "
                                              f"({entry['first_missing']} .. {entry['last_counted']}); confirmed"))
            new_missing.pop(k, None)
        else:
            belief[k] = prev
            new_missing[k] = entry
            result.pending_removals.append(Change(PENDING_REMOVAL, course_id, k, prev.title, before=prev,
                                                  note=f"missing since {entry['first_missing']} ({entry['count']}/{REMOVAL_CONFIRMATIONS}); "
                                                       f"will be removed if still absent on a later day"))

    for k in list(new_missing):
        if k in cur_by_key:
            del new_missing[k]

    new_belief = sorted(belief.values(), key=lambda e: (e.start or "9999", e.title))
    return result, new_belief, new_missing


def _diff_partial(course_id: str, previous: list[Event], events: list[Event], result: DiffResult,
                  new_missing: dict[str, dict[str, Any]]) -> tuple[DiffResult, list[Event], dict[str, dict[str, Any]]]:
    """A partial reading (email) can move or add items; it cannot remove anything."""
    belief = {e.key: e for e in previous}
    for ev in events:
        prev = belief.get(ev.key)
        if prev is None:
            result.changes.append(Change(ADDED, course_id, ev.key, ev.title, after=ev, note=_fmt(ev) + " (from a partial source)"))
            belief[ev.key] = ev
        elif not prev.same_schedule(ev):
            result.changes.append(Change(MOVED, course_id, ev.key, ev.title, before=prev, after=ev,
                                         note=f"{_fmt(prev)} -> {_fmt(ev)} (from a partial source)"))
            belief[ev.key] = ev
    new_belief = sorted(belief.values(), key=lambda e: (e.start or "9999", e.title))
    return result, new_belief, new_missing


def merge_readings(readings: list[Reading]) -> tuple[Optional[Reading], list[Reading]]:
    """Combine every reading of one course for one night.

    Returns (merged, failed_full). A successful full reading (page, API, feed)
    absorbs the items of every other successful reading, partial ones included.
    If no full reading succeeded, the partial readings are merged on their own
    and stay partial, and the failed full readings are returned so the course
    can be reported unreadable.
    """
    if not readings:
        return None, []
    full = [r for r in readings if not r.partial]
    parts = [r for r in readings if r.partial and r.ok]
    ok_full = [r for r in full if r.ok]
    failed_full = [r for r in full if not r.ok]
    base_list = ok_full or parts
    if not base_list:
        return (failed_full[0] if failed_full else None), failed_full[1:]
    base = base_list[0]
    items = []
    for r in (ok_full + parts) if ok_full else parts:
        items.extend(r.items)
    merged = Reading(
        course_id=base.course_id,
        source_url=base.source_url,
        read_at=max(r.read_at for r in base_list + parts),
        status=STATUS_OK,
        items=items,
        timezone=base.timezone,
        partial=not ok_full,
    )
    return merged, failed_full


def diff_all(
    belief: dict[str, list[Event]],
    readings: list[Reading],
    missing: dict[str, dict[str, Any]],
    course_ids: Optional[list[str]] = None,
) -> DiffResult:
    """Diff every course. Courses configured but not read this run are left untouched."""
    total = DiffResult()
    grouped: dict[str, list[Reading]] = {}
    for r in readings:
        grouped.setdefault(r.course_id, []).append(r)
    by_course: dict[str, Optional[Reading]] = {}
    failed_notes: dict[str, list[Reading]] = {}
    for cid, group in grouped.items():
        merged, failed = merge_readings(group)
        by_course[cid] = merged
        if merged is not None and merged.ok and failed:
            failed_notes[cid] = failed
    ids = list(course_ids or [])
    for cid in list(belief) + list(by_course):
        if cid not in ids:
            ids.append(cid)
    for cid in ids:
        course_missing = {k: v for k, v in missing.items() if k.startswith(f"{cid}::")}
        res, new_belief, new_missing = diff_course(cid, belief.get(cid, []), by_course.get(cid), course_missing)
        for failed in failed_notes.get(cid, []):
            res.unreadable.append(Change(SOURCE_FAILED, cid, f"{cid}::*", cid,
                                         note=f"{failed.source_url or 'a source'} failed ({failed.error or failed.status}); "
                                              f"other sources for this course were used"))
        total.changes.extend(res.changes)
        total.pending_removals.extend(res.pending_removals)
        total.unreadable.extend(res.unreadable)
        total.needs_review.extend(res.needs_review)
        total.proposed_belief[cid] = new_belief
        total.proposed_missing.update(new_missing)
    for k, v in missing.items():
        cid = k.split("::", 1)[0]
        if cid not in ids:
            total.proposed_missing[k] = v
    return total


def _fmt(e: Event) -> str:
    if e.start is None:
        return "(no date)"
    if e.all_day:
        return e.start if e.end in (None, e.start) else f"{e.start}..{e.end}"
    return e.start
