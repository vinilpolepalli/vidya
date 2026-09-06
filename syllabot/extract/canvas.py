"""Canvas LMS via its REST API. No scraping, no MFA fight: a per-user access
token (Account > Settings > New Access Token) and three documented endpoints.

  GET /api/v1/courses/:id/assignments                       name, due_at, html_url
  GET /api/v1/courses/:id/discussion_topics?only_announcements=true
                                                            title, message, posted_at
  GET /api/v1/calendar_events?context_codes[]=course_:id    title, start_at, end_at, all_day

The same functions also accept the JSON those endpoints return, saved to files,
so the adapter is testable offline (fixtures/canvas/*.json) and the bot can
capture a sandbox course once and replay it.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any, Optional

from ..model import (
    KIND_ANNOUNCEMENT, KIND_ASSIGNMENT, KIND_EXAM, KIND_OTHER, STATUS_ERROR, STATUS_OK,
    Item, Reading,
)
from ..normalize import clean_text
from .html import DATE_HINT

EXAM_RE = re.compile(r"\b(exam|midterm|quiz|test)\b|^final\b(?!.*\b(project|paper|essay|portfolio|presentation|report|draft)\b)", re.I)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "tr"):
            self.parts.append(" ")


def strip_html(html: str) -> str:
    if not html:
        return ""
    t = _Text()
    t.feed(html)
    return clean_text(" ".join(t.parts))


def items_from_canvas(assignments: list[dict[str, Any]], announcements: list[dict[str, Any]],
                      events: list[dict[str, Any]]) -> list[Item]:
    items: list[Item] = []
    for a in assignments or []:
        if a.get("published") is False:
            continue
        name = clean_text(a.get("name") or "")
        if not name:
            continue
        due = a.get("due_at")
        if not due:
            items.append(Item(title=name, date_text="no due date set", kind=_kind(name), url=a.get("html_url") or "",
                              section="assignments", detail="Canvas assignment without a due date"))
            continue
        items.append(Item(title=name, date_text=f"due {due}", kind=_kind(name), url=a.get("html_url") or "",
                          section="assignments", start=due, end=due, all_day=False))
    for ann in announcements or []:
        title = clean_text(ann.get("title") or "")
        body = strip_html(ann.get("message") or "")
        posted = (ann.get("posted_at") or ann.get("delayed_post_at") or "")[:10] or None
        if not title or not body or not DATE_HINT.search(body):
            continue  # an announcement with no date in it is not a dated item
        items.append(Item(title=title, date_text=body, kind=KIND_ANNOUNCEMENT, url=ann.get("html_url") or "",
                          section="announcements", posted_at=posted, detail=body[:500]))
    for ev in events or []:
        title = clean_text(ev.get("title") or "")
        start = ev.get("start_at")
        if not title or not start:
            continue
        all_day = bool(ev.get("all_day"))
        if all_day and ev.get("all_day_date"):
            start = ev["all_day_date"]
            end = ev["all_day_date"]
        else:
            end = ev.get("end_at") or start
        items.append(Item(title=title, date_text=f"{start} to {end}", kind=_kind(title) if EXAM_RE.search(title) else KIND_OTHER,
                          url=ev.get("html_url") or "", section="calendar", start=start, end=end, all_day=all_day,
                          detail=strip_html(ev.get("description") or "")[:500]))
    return items


def _kind(name: str) -> str:
    return KIND_EXAM if EXAM_RE.search(name) else KIND_ASSIGNMENT


def extract_canvas_files(course_id: str, source_url: str, read_at: str,
                         assignments_json: Optional[str], announcements_json: Optional[str],
                         events_json: Optional[str], timezone: str = "America/New_York") -> Reading:
    def load(p):
        if not p:
            return []
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("items", [])
    try:
        items = items_from_canvas(load(assignments_json), load(announcements_json), load(events_json))
    except (OSError, ValueError) as e:
        return Reading(course_id, source_url, read_at, status=STATUS_ERROR, error=f"canvas json: {e}", timezone=timezone)
    return Reading(course_id, source_url, read_at, status=STATUS_OK, items=items, timezone=timezone)


def fetch_canvas(base_url: str, canvas_course_id: str, token: str, course_id: str, read_at: str,
                 timezone: str = "America/New_York") -> Reading:
    base = base_url.rstrip("/")
    source_url = f"{base}/courses/{canvas_course_id}"
    try:
        assignments = _paged(f"{base}/api/v1/courses/{canvas_course_id}/assignments", token, {"per_page": 100})
        announcements = _paged(f"{base}/api/v1/courses/{canvas_course_id}/discussion_topics", token,
                               {"only_announcements": "true", "per_page": 100})
        events = _paged(f"{base}/api/v1/calendar_events", token,
                        {"context_codes[]": f"course_{canvas_course_id}", "type": "event", "per_page": 100,
                         "start_date": read_at[:10], "end_date": _plus_days(read_at[:10], 365)})
    except Exception as e:  # network, auth, JSON: all are a failed read, never a deletion
        return Reading(course_id, source_url, read_at, status=STATUS_ERROR, error=f"canvas api: {e}", timezone=timezone)
    return Reading(course_id, source_url, read_at, status=STATUS_OK,
                   items=items_from_canvas(assignments, announcements, events), timezone=timezone)


def _plus_days(day: str, n: int) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def _paged(url: str, token: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    next_url: Optional[str] = url + "?" + urllib.parse.urlencode(params)
    for _ in range(50):  # pagination guard
        if not next_url:
            break
        req = urllib.request.Request(next_url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            out.extend(body if isinstance(body, list) else [body])
            link = resp.headers.get("Link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part[part.find("<") + 1: part.find(">")]
    return out
