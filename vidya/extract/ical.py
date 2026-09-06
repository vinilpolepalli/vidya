"""iCalendar feeds. Brightspace (Calendar > Subscribe), Canvas (Calendar >
Calendar Feed) and Google Classroom all publish a tokenized .ics URL that needs
no login and survives UI redesigns, which makes it the first thing to try when
multi-factor auth blocks an unattended read.

Standard-library parser: handles line folding, TZID, DATE vs DATE-TIME, UTC 'Z',
and text escapes. Not a full RFC 5545 implementation (no RRULE expansion;
recurring events are reported for review rather than guessed).
"""

from __future__ import annotations

import re
import urllib.request
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ..model import KIND_ASSIGNMENT, KIND_CLASS, KIND_EXAM, STATUS_EMPTY, STATUS_ERROR, STATUS_OK, Item, Reading
from ..normalize import clean_text

EXAM_RE = re.compile(r"\b(exam|midterm|quiz|test)\b|^final\b(?!.*\b(project|paper|essay|portfolio|presentation|report|draft)\b)", re.I)
CLASS_RE = re.compile(r"\b(lecture|class|lab|recitation|seminar|office hours)\b", re.I)
# Brightspace/Canvas decorate summaries: "Homework 1 - Due", "Quiz 2 - Availability Ends", "Essay 1 [CS 201]"
SUFFIX_RE = re.compile(r"\s*[-–:]\s*(due|due date|availability (starts|ends)|starts|ends|opens|closes|available)\s*$", re.I)
BRACKET_RE = re.compile(r"\s*\[[^\]]*\]\s*$")


def unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def unescape(s: str) -> str:
    return s.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def parse_events(text: str) -> list[dict]:
    events: list[dict] = []
    cur: Optional[dict] = None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {}
            continue
        if line == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
            continue
        if cur is None or ":" not in line:
            continue
        head, value = line.split(":", 1)
        name, *params = head.split(";")
        p = {}
        for prm in params:
            if "=" in prm:
                k, v = prm.split("=", 1)
                p[k.upper()] = v
        cur[name.upper()] = {"value": value, "params": p}
    return events


def _to_iso(prop: Optional[dict], default_tz: str) -> tuple[Optional[str], bool]:
    if not prop:
        return None, False
    v = prop["value"].strip()
    params = prop["params"]
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", v):
        return f"{v[:4]}-{v[4:6]}-{v[6:8]}", True
    m = re.fullmatch(r"(\d{8})T(\d{6})(Z?)", v)
    if not m:
        return None, False
    d, t, z = m.groups()
    naive = datetime.strptime(d + t, "%Y%m%d%H%M%S")
    if z:
        dt = naive.replace(tzinfo=ZoneInfo("UTC"))
    else:
        tzid = params.get("TZID") or default_tz
        try:
            dt = naive.replace(tzinfo=ZoneInfo(tzid))
        except Exception:
            dt = naive.replace(tzinfo=ZoneInfo(default_tz))
    return dt.astimezone(ZoneInfo(default_tz)).isoformat(), False


def clean_summary(summary: str) -> str:
    s = clean_text(unescape(summary))
    s = BRACKET_RE.sub("", s)
    s = SUFFIX_RE.sub("", s)
    return s.strip(" -–:")


def extract_ical(text: str, course_id: str, source_url: str, read_at: Optional[str] = None,
                 timezone: str = "America/New_York") -> Reading:
    read_at = read_at or datetime.now().astimezone().isoformat(timespec="seconds")
    if not text or "BEGIN:VCALENDAR" not in text:
        return Reading(course_id, source_url, read_at, status=STATUS_EMPTY if not text.strip() else STATUS_ERROR,
                       error="not an iCalendar document", timezone=timezone)
    items: list[Item] = []
    for ev in parse_events(text):
        summary = ev.get("SUMMARY", {}).get("value", "")
        title = clean_summary(summary)
        if not title:
            continue
        start, all_day = _to_iso(ev.get("DTSTART"), timezone)
        end, _ = _to_iso(ev.get("DTEND") or ev.get("DUE"), timezone)
        if all_day and end:
            # iCal all-day DTEND is exclusive; the model uses inclusive ends
            from datetime import date, timedelta
            end = (date.fromisoformat(end[:10]) - timedelta(days=1)).isoformat()
            if end < start:
                end = start
        url = ev.get("URL", {}).get("value", "") or source_url
        desc = clean_text(unescape(ev.get("DESCRIPTION", {}).get("value", "")))[:500]
        if "RRULE" in ev:
            items.append(Item(title=title, date_text=f"recurring ({ev['RRULE']['value']}) from {start}", kind=KIND_CLASS,
                              url=url, section="calendar", detail=desc))
            continue
        if not start:
            items.append(Item(title=title, date_text="TBD", kind=KIND_ASSIGNMENT, url=url, section="calendar", detail=desc))
            continue
        kind = KIND_EXAM if EXAM_RE.search(title) else (KIND_CLASS if CLASS_RE.search(title) else KIND_ASSIGNMENT)
        items.append(Item(title=title, date_text=f"{start}" + (f" to {end}" if end and end != start else ""), kind=kind,
                          url=url, section="calendar", start=start, end=end or start, all_day=all_day, detail=desc))
    return Reading(course_id, source_url, read_at, status=STATUS_OK, items=items, timezone=timezone)


def fetch_ical(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "vidya/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")
