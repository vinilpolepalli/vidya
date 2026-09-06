"""Turn a Reading's raw items into date-resolved, deduplicated Events."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .dates import parse_date_text
from .model import Event, ParsedDate, Reading
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
        if item.start:
            parsed = _exact(item, reading.timezone)
        else:
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
            superseded=parsed.superseded,
        )
        if item.review_reason:
            ev.needs_review = True
            ev.review_reason = item.review_reason + (f" ({ev.review_reason})" if ev.review_reason else "")
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


def _exact(item, tz: str) -> ParsedDate:
    """An item that arrived with machine timestamps (API or iCal). Rendered in
    the course timezone so it compares equal to the same deadline read from a page."""
    zone = ZoneInfo(tz)
    try:
        if item.all_day or (len(item.start) == 10 and "T" not in item.start):
            start_d = date.fromisoformat(item.start[:10])
            end_d = date.fromisoformat((item.end or item.start)[:10])
            return ParsedDate(start=start_d.isoformat(), end=end_d.isoformat(), all_day=True,
                              confidence=0.98, needs_review=False,
                              assumptions=["exact date from the source system"])
        start = datetime.fromisoformat(item.start.replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=zone)
        end = datetime.fromisoformat(item.end.replace("Z", "+00:00")) if item.end else start
        if end.tzinfo is None:
            end = end.replace(tzinfo=zone)
        start, end = start.astimezone(zone), end.astimezone(zone)
        if end < start:
            end = start
        return ParsedDate(start=start.isoformat(), end=end.isoformat(), all_day=False,
                          confidence=0.98, needs_review=False,
                          assumptions=["exact timestamp from the source system"])
    except ValueError as e:
        return ParsedDate(start=None, end=None, all_day=True, confidence=0.0, needs_review=True,
                          reason=f"unparseable machine timestamp {item.start!r}: {e}")


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
            # One source states a change whose OLD date is what the other source
            # still shows ("moved from Oct 14 to Oct 16" vs a page saying Oct 14).
            # That is an acknowledged update, not a disagreement: the change wins.
            for newer, older in ((a, b), (b, a)):
                if newer.superseded and older.start and newer.superseded == older.start[:10]:
                    merged = Event(**{**newer.to_dict(), "sources": sources})
                    merged.assumptions = list(dict.fromkeys(
                        newer.assumptions + [f"supersedes '{older.date_text}' still shown at {older.sources[0]}"]))
                    if older.detail and not merged.detail:
                        merged.detail = older.detail
                    return merged
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
