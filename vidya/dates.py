"""Date parsing with confidence, timezone handling and a needs-review bucket.

Design rule: never guess onto the calendar. Anything ambiguous comes back with
needs_review=True and (where possible) a candidate date so a human can confirm
in one click. The adversarial set this must satisfy is tests/test_t4_dates.py.

Standard library only (re, datetime, zoneinfo).
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from .model import DEFAULT_TZ, ParsedDate
from .normalize import clean_text

NEEDS_REVIEW_BELOW = 0.6

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
WEEKDAYS = {
    "monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "tues": 1, "wednesday": 2,
    "wed": 2, "thursday": 3, "thu": 3, "thur": 3, "thurs": 3, "friday": 4,
    "fri": 4, "saturday": 5, "sat": 5, "sunday": 6, "sun": 6,
}
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TZ_ABBR = {
    "et": "America/New_York", "est": "America/New_York", "edt": "America/New_York",
    "ct": "America/Chicago", "cst": "America/Chicago", "cdt": "America/Chicago",
    "mt": "America/Denver", "mst": "America/Denver", "mdt": "America/Denver",
    "pt": "America/Los_Angeles", "pst": "America/Los_Angeles", "pdt": "America/Los_Angeles",
    "utc": "UTC", "gmt": "UTC",
}

_MONTH = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
_ORD = r"(?:st|nd|rd|th)?"
_WD = r"(?:" + "|".join(sorted(WEEKDAYS, key=len, reverse=True)) + r")"

ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MD_RE = re.compile(rf"\b({_MONTH})\.?\s+(\d{{1,2}}){_ORD}(?:,?\s+(\d{{4}}))?\b", re.I)
DM_RE = re.compile(rf"\b(\d{{1,2}}){_ORD}\s+(?:of\s+)?({_MONTH})\.?(?:,?\s+(\d{{4}}))?\b", re.I)
NUM_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
# "Oct 20 to 22", "Oct 20-22": a bare day number right after a month-name date
DAY_TAIL_RE = re.compile(r"^\s*(?:-|to|through|thru|until|till)\s*(\d{1,2})\b(?![:/]|\s*[ap]\.?m)", re.I)
RANGE_JOIN_RE = re.compile(r"^\s*(?:-|to|through|thru|until|till)\s*$", re.I)
TIME_RANGE_RE = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?\s*(?:-|to|until|till)\s*(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)\b", re.I
)
TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s?m\.?\b", re.I)
TIME24_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
TZ_RE = re.compile(r"\b(est|edt|et|cst|cdt|ct|mst|mdt|mt|pst|pdt|pt|utc|gmt)\b", re.I)
WD_RE = re.compile(rf"\b(next|this|coming)?\s*({_WD})\b", re.I)
_CHANGE_VERB = r"(?:changed|moved|pushed(?: back)?|rescheduled|postponed|extended|shifted|bumped)"
CHANGE_AFTER_RE = re.compile(
    rf"{_CHANGE_VERB}\s+from\s+[^,;]*?\s+(?:to|until|till)\b"  # "moved from Oct 14 to Oct 16"
    rf"|{_CHANGE_VERB}\s+(?:to|until|till)\b"                  # "moved to Oct 16"
    r"|now\s+due\b|\bnow\b|->|→",
    re.I,
)
CHANGE_BEFORE_RE = re.compile(r"\binstead of\b|\b(?:not|rather than|previously|was)\b", re.I)
RECURRING_RE = re.compile(r"\b(every|each|weekly|biweekly|daily|recurring)\b", re.I)
REVIEW_PHRASES = [
    (re.compile(r"\btb[ad]\b|\bto be (?:determined|announced|confirmed|scheduled)\b", re.I), "date is TBD/TBA"),
    (re.compile(r"\bweek of\b", re.I), "'week of' names a week, not a day"),
    (re.compile(r"\b(?:end|start|beginning) of (?:the )?(?:semester|term|month)\b", re.I), "vague period, not a date"),
    (re.compile(r"\bfinals? week\b", re.I), "'finals week' without a date"),
    (re.compile(r"\bmid[- ]?terms? week\b", re.I), "'midterm week' without a date"),
]
CLASS_PHRASE_RE = re.compile(r"\b(?:before|in|during|after|at the (?:start|beginning|end) of)\s+(?:the\s+)?(?:next\s+)?(?:class|lecture|lab|section|recitation)\b", re.I)


def _to_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(s[:10])


def resolve_year(month: int, day: int, reference: date) -> tuple[date, str]:
    """Pick the year that puts month/day inside the academic window around the
    reference date: 60 days back to 300 days forward. 'Dec 18' read in
    September stays in the same year; 'Jan 20' read in December rolls forward."""
    candidates = []
    for y in (reference.year - 1, reference.year, reference.year + 1):
        try:
            d = date(y, month, day)
        except ValueError:
            continue
        candidates.append(d)
    if not candidates:
        raise ValueError(f"invalid month/day {month}/{day}")
    in_window = [d for d in candidates if -60 <= (d - reference).days <= 300]
    if in_window:
        chosen = min(in_window, key=lambda d: abs((d - reference).days))
    else:
        future = [d for d in candidates if d >= reference]
        chosen = min(future, key=lambda d: (d - reference).days) if future else max(candidates)
    return chosen, f"year inferred as {chosen.year} from read date {reference.isoformat()}"


def _find_dates(text: str, reference: date) -> tuple[list[dict], str]:
    """Return date tokens (with spans) and the text with those spans blanked."""
    found: list[dict] = []
    work = text

    def blank(s: int, e: int) -> None:
        nonlocal work
        work = work[:s] + (" " * (e - s)) + work[e:]

    for m in ISO_RE.finditer(work):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            found.append({"date": date(y, mo, d), "span": m.span(), "explicit_year": True})
        except ValueError:
            continue
    for f in found:
        blank(*f["span"])

    for regex, order in ((MD_RE, "md"), (DM_RE, "dm")):
        for m in regex.finditer(work):
            if order == "md":
                mon, day, year = MONTHS[m.group(1).lower()], int(m.group(2)), m.group(3)
            else:
                day, mon, year = int(m.group(1)), MONTHS[m.group(2).lower()], m.group(3)
            if not 1 <= day <= 31:
                continue
            entry: dict = {"span": m.span(), "explicit_year": bool(year), "month": mon, "day": day}
            if year:
                try:
                    entry["date"] = date(int(year), mon, day)
                except ValueError:
                    continue
            else:
                try:
                    entry["date"], entry["assumption"] = resolve_year(mon, day, reference)
                except ValueError:
                    continue
            found.append(entry)
        for f in found:
            blank(*f["span"])

    for m in NUM_RE.finditer(work):
        mon, day, year = int(m.group(1)), int(m.group(2)), m.group(3)
        if not (1 <= mon <= 12 and 1 <= day <= 31):
            continue
        entry = {"span": m.span(), "explicit_year": bool(year), "month": mon, "day": day}
        if year:
            y = int(year)
            y = y + 2000 if y < 100 else y
            try:
                entry["date"] = date(y, mon, day)
            except ValueError:
                continue
        else:
            try:
                entry["date"], entry["assumption"] = resolve_year(mon, day, reference)
            except ValueError:
                continue
        found.append(entry)
    for f in found:
        blank(*f["span"])

    found.sort(key=lambda f: f["span"][0])
    return found, work


def _find_time(text: str) -> tuple[Optional[time], Optional[time], list[str]]:
    """Return (start_time, end_time, assumptions)."""
    assumptions: list[str] = []
    low = text.lower()
    m = TIME_RANGE_RE.search(text)
    if m:
        h1, mi1, ap1, h2, mi2, ap2 = m.groups()
        ap1 = (ap1 or ap2)[0].lower()
        t1 = _mk_time(int(h1), int(mi1 or 0), ap1)
        t2 = _mk_time(int(h2), int(mi2 or 0), ap2[0].lower())
        if t1 and t2:
            return t1, t2, assumptions
    m = TIME_RE.search(text)
    if m:
        t = _mk_time(int(m.group(1)), int(m.group(2) or 0), m.group(3).lower())
        if t:
            return t, None, assumptions
    if re.search(r"\bnoon\b", low):
        return time(12, 0), None, assumptions
    if re.search(r"\bmidnight\b", low):
        assumptions.append("'midnight' interpreted as 11:59 PM of the stated day")
        return time(23, 59), None, assumptions
    m = TIME24_RE.search(text)
    if m:
        return time(int(m.group(1)), int(m.group(2))), None, assumptions
    return None, None, assumptions


def _mk_time(h: int, mi: int, ap: str) -> Optional[time]:
    if not (1 <= h <= 12 and 0 <= mi <= 59):
        return None
    if ap == "p" and h != 12:
        h += 12
    if ap == "a" and h == 12:
        h = 0
    return time(h, mi)


def _review(reason: str, confidence: float = 0.0, candidate: Optional[date] = None,
            assumptions: Optional[list[str]] = None) -> ParsedDate:
    return ParsedDate(
        start=candidate.isoformat() if candidate else None,
        end=candidate.isoformat() if candidate else None,
        all_day=True,
        confidence=confidence,
        needs_review=True,
        reason=reason,
        assumptions=assumptions or [],
    )


def parse_date_text(
    text: str,
    reference,
    tz: str = DEFAULT_TZ,
    posted_at=None,
) -> ParsedDate:
    """Parse free text into a ParsedDate.

    reference: the date the text was read (ISO string, date or datetime). Used
        to infer the year when the text omits it.
    tz: the course timezone. Times without an explicit zone resolve here and
        the assumption is recorded.
    posted_at: for announcements/email, the date the text was written.
        Relative words ('next Friday', 'tomorrow') resolve against this, never
        against today.
    """
    raw = clean_text(text or "")
    if not raw:
        return _review("no date text")
    ref = _to_date(reference)
    base = _to_date(posted_at) if posted_at else ref
    assumptions: list[str] = []
    confidence = 0.0

    for regex, reason in REVIEW_PHRASES:
        if regex.search(raw):
            return _review(reason)
    if RECURRING_RE.search(raw) and not ISO_RE.search(raw) and not MD_RE.search(raw) and not NUM_RE.search(raw):
        return _review("recurring schedule; one-off events only")

    # Inline change: "Oct 14 changed to Oct 16" -> keep the text after the last
    # change phrase; "Oct 16 instead of Oct 14" -> keep the text before it.
    segment = raw
    old_segment = ""
    changed = False
    after_matches = list(CHANGE_AFTER_RE.finditer(raw))
    before_match = CHANGE_BEFORE_RE.search(raw)
    if after_matches:
        segment = raw[after_matches[-1].end():]
        old_segment = raw[: after_matches[-1].end()]
        changed = True
    elif before_match:
        segment = raw[: before_match.start()]
        old_segment = raw[before_match.end():]
        changed = True
    if changed:
        assumptions.append("inline change detected; using the newly stated date")

    dates, remainder = _find_dates(segment, ref)
    superseded: Optional[str] = None
    if changed and not dates:
        # the change phrase had no date after it; it was ordinary prose
        dates, remainder = _find_dates(raw, ref)
        segment = raw
        changed = False
        assumptions = [a for a in assumptions if not a.startswith("inline change")]
    elif changed:
        old_dates, _ = _find_dates(old_segment, ref)
        if old_dates:
            superseded = old_dates[-1]["date"].isoformat()

    weekday_hits = WD_RE.findall(segment)
    if not dates and len(weekday_hits) >= 2:
        return _review("several weekdays and no date; looks like a recurring class meeting")

    explicit_tz = None
    tzm = TZ_RE.search(segment)
    if tzm:
        explicit_tz = TZ_ABBR[tzm.group(1).lower()]

    wd_match = WD_RE.search(segment)
    wd_idx = WEEKDAYS[wd_match.group(2).lower()] if wd_match else None
    wd_qualifier = (wd_match.group(1) or "").lower() if wd_match else ""

    if not dates:
        if re.search(r"\btomorrow\b", segment, re.I):
            cand = base + timedelta(days=1)
            assumptions.append(f"'tomorrow' resolved against {base.isoformat()}")
            return _finish(cand, None, segment, tz, explicit_tz, 0.7, assumptions, ref)
        if re.search(r"\btoday\b", segment, re.I):
            assumptions.append(f"'today' resolved against {base.isoformat()}")
            return _finish(base, None, segment, tz, explicit_tz, 0.7, assumptions, ref)
        if wd_idx is not None:
            days_ahead = (wd_idx - base.weekday()) % 7 or 7
            cand = base + timedelta(days=days_ahead)
            src = "announcement date" if posted_at else "read date"
            assumptions.append(f"'{wd_match.group(0).strip()}' resolved against {src} {base.isoformat()}")
            if wd_qualifier in ("next", "coming"):
                return _review(
                    f"relative weekday '{wd_match.group(0).strip()}' is ambiguous; candidate {cand.isoformat()}",
                    confidence=0.5, candidate=cand, assumptions=assumptions,
                )
            return _finish(cand, None, segment, tz, explicit_tz, 0.7, assumptions, ref)
        if CLASS_PHRASE_RE.search(raw):
            return _review("relative to a class meeting, no date given")
        return _review("no date found")

    first = dates[0]
    start_d: date = first["date"]
    end_d: Optional[date] = None
    if "assumption" in first:
        assumptions.append(first["assumption"])

    # Range forms: "Oct 20 to 22", "Oct 20 - Nov 2", "10/20-10/22"
    tail = segment[first["span"][1]:]
    if len(dates) >= 2:
        between = segment[first["span"][1]: dates[1]["span"][0]]
        if RANGE_JOIN_RE.match(between):
            end_d = dates[1]["date"]
    if end_d is None:
        m = DAY_TAIL_RE.match(tail)
        if m:
            try:
                end_d = date(start_d.year, start_d.month, int(m.group(1)))
            except ValueError:
                end_d = None
    if end_d is not None and end_d < start_d:
        end_d = None

    if len(dates) >= 2 and end_d is None and not changed:
        assumptions.append("multiple dates present; used the first")
        confidence -= 0.1

    if wd_idx is not None and end_d is None and start_d.weekday() != wd_idx:
        return _review(
            f"weekday '{WEEKDAY_NAMES[wd_idx]}' does not match {start_d.isoformat()} ({WEEKDAY_NAMES[start_d.weekday()]})",
            confidence=0.3, candidate=start_d, assumptions=assumptions,
        )

    base_conf = 0.85
    if first["explicit_year"]:
        base_conf += 0.05
    if wd_idx is not None:
        base_conf += 0.05
    if changed:
        base_conf -= 0.1
    confidence += base_conf
    out = _finish(start_d, end_d, remainder, tz, explicit_tz, confidence, assumptions, ref)
    out.superseded = superseded
    return out


def _finish(start_d: date, end_d: Optional[date], time_text: str, tz: str,
            explicit_tz: Optional[str], confidence: float, assumptions: list[str],
            ref: date) -> ParsedDate:
    start_t, end_t, t_assump = _find_time(time_text)
    assumptions = assumptions + t_assump
    zone = ZoneInfo(tz)
    if start_t is None:
        # all-day; inclusive end
        end_out = (end_d or start_d).isoformat()
        conf = min(confidence, 0.98)
        return ParsedDate(
            start=start_d.isoformat(), end=end_out, all_day=True,
            confidence=round(conf, 2), needs_review=conf < NEEDS_REVIEW_BELOW,
            reason="" if conf >= NEEDS_REVIEW_BELOW else "low confidence",
            assumptions=assumptions + (["no time given; all-day event"] if not end_d else []),
        )
    if explicit_tz:
        src_zone = ZoneInfo(explicit_tz)
        confidence += 0.05
    else:
        src_zone = zone
        assumptions.append(f"no timezone given; assumed course timezone {tz}")
    start_dt = datetime.combine(start_d, start_t, tzinfo=src_zone).astimezone(zone)
    if end_t is not None:
        end_dt = datetime.combine(end_d or start_d, end_t, tzinfo=src_zone).astimezone(zone)
        if end_dt < start_dt:
            end_dt = start_dt
    else:
        end_dt = datetime.combine(end_d, start_t, tzinfo=src_zone).astimezone(zone) if end_d else start_dt
    conf = min(confidence + 0.05, 0.98)
    return ParsedDate(
        start=start_dt.isoformat(), end=end_dt.isoformat(), all_day=False,
        confidence=round(conf, 2), needs_review=conf < NEEDS_REVIEW_BELOW,
        reason="" if conf >= NEEDS_REVIEW_BELOW else "low confidence",
        assumptions=assumptions,
    )
