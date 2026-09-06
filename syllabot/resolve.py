"""Turn a Reading's raw items into date-resolved, deduplicated Events."""

from __future__ import annotations

from .dates import parse_date_text
from .model import Event, Reading
from .normalize import clean_text, item_key


def resolve_reading(reading: Reading) -> tuple[list[Event], list[Event]]:
    """Return (events, needs_review).

    events are safe to diff and to write. needs_review never reach the belief
    snapshot, so they can never produce a calendar operation.

    Duplicates inside one reading (the same deadline on the syllabus and on the
    assignments page) merge into one Event that keeps every source URL; if the
    two sources disagree on the date the item goes to needs_review instead of
    letting either source win silently.
    """
    by_key: dict[str, Event] = {}
    review: list[Event] = []
    for item in reading.items:
        title = clean_text(item.title)
        if not title:
            continue
        parsed = parse_date_text(
            item.date_text, reading.read_at, tz=reading.timezone, posted_at=item.posted_at
        )
        ev = Event(
            key=item_key(reading.course_id, title),
            course_id=reading.course_id,
            title=title,
            kind=item.kind,
            start=parsed.start,
            end=parsed.end,
            all_day=parsed.all_day,
            date_text=clean_text(item.date_text),
            sources=[item.url or reading.source_url],
            read_at=reading.read_at,
            confidence=parsed.confidence,
            needs_review=parsed.needs_review,
            review_reason=parsed.reason,
            assumptions=list(parsed.assumptions),
            detail=clean_text(item.detail)[:500],
        )
        existing = by_key.get(ev.key)
        if existing is None:
            by_key[ev.key] = ev
            continue
        by_key[ev.key] = _merge(existing, ev)

    events: list[Event] = []
    for ev in by_key.values():
        (review if ev.needs_review else events).append(ev)
    events.sort(key=lambda e: (e.start or "9999", e.title))
    review.sort(key=lambda e: e.title)
    return events, review


def _merge(a: Event, b: Event) -> Event:
    sources = list(dict.fromkeys(a.sources + b.sources))
    if a.needs_review and not b.needs_review:
        keep, other = b, a
    elif b.needs_review and not a.needs_review:
        keep, other = a, b
    elif a.needs_review and b.needs_review:
        keep, other = a, b
    else:
        same_day = (a.start or "")[:10] == (b.start or "")[:10]
        if not same_day:
            merged = Event(**{**a.to_dict(), "sources": sources})
            merged.needs_review = True
            merged.review_reason = (
                f"sources disagree: '{a.date_text}' vs '{b.date_text}'"
            )
            merged.assumptions = a.assumptions + b.assumptions
            return merged
        # same day: prefer the one with a clock time, then higher confidence
        if a.all_day != b.all_day:
            keep, other = (b, a) if a.all_day else (a, b)
        else:
            keep, other = (a, b) if a.confidence >= b.confidence else (b, a)
    merged = Event(**{**keep.to_dict(), "sources": sources})
    merged.assumptions = list(dict.fromkeys(keep.assumptions + [f"also listed as '{other.date_text}'"]))
    if other.detail and not merged.detail:
        merged.detail = other.detail
    return merged
