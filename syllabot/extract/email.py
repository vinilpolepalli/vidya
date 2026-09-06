"""Read-only email adapter.

A professor who emails "the midterm is moved to Thursday" without touching the
LMS is exactly the case a page scrape misses. This turns one .eml into a
Reading for a course: sentences that mention a date or a change phrase become
items, matched by title similarity against the titles the bot already believes
for that course so "the midterm" lands on "Midterm 1" instead of creating a new
item. Unmatched mentions arrive with low confidence and go to needs-review.

Nothing here sends mail. Sending from a public template is a footgun.
"""

from __future__ import annotations

import email
import email.policy
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from ..dates import CHANGE_AFTER_RE, CHANGE_BEFORE_RE
from ..extract.html import DATE_HINT
from ..model import KIND_ANNOUNCEMENT, KIND_EXAM, STATUS_ERROR, STATUS_OK, Item, Reading
from ..normalize import clean_text, slug
from .canvas import strip_html

SUBJECT_NOISE = re.compile(r"^\s*((re|fwd?|fw)\s*:\s*|\[[^\]]*\]\s*)+", re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
ITEM_HINT = re.compile(
    r"\b((?:final|midterm|mid-term)\s*(?:exam)?(?:\s*\d+)?|exam\s*\d*|quiz\s*\d*|"
    r"(?:homework|hw|problem set|pset|ps|lab(?: report)?|project|essay|paper|assignment|reading response)\s*\d*(?:\s*(?:draft|final))?)\b",
    re.I,
)
MATCH_THRESHOLD = 0.55


def parse_eml(raw: bytes) -> dict:
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    body = ""
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is not None:
        content = part.get_content()
        body = strip_html(content) if part.get_content_type() == "text/html" else content
    sent = None
    if msg.get("Date"):
        try:
            sent = parsedate_to_datetime(msg["Date"]).date().isoformat()
        except (TypeError, ValueError):
            sent = None
    return {"subject": clean_text(msg.get("Subject", "")), "from": msg.get("From", ""),
            "date": sent, "body": body or "", "message_id": msg.get("Message-ID", "")}


def candidate_sentences(body: str) -> list[str]:
    """Sentences that carry a date or a change phrase. Paragraph breaks split
    too, so a greeting line never rides along with the sentence that matters."""
    out = []
    for s in SENTENCE_SPLIT.split(body):
        s = clean_text(s)
        if not s:
            continue
        if DATE_HINT.search(s) or CHANGE_AFTER_RE.search(s) or CHANGE_BEFORE_RE.search(s):
            out.append(s)
    return out


def extract_email(raw: bytes, course_id: str, read_at: Optional[str] = None,
                  known_titles: Optional[list[str]] = None, timezone: str = "America/New_York",
                  source_url: str = "") -> Reading:
    read_at = read_at or datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        parsed = parse_eml(raw)
    except Exception as e:
        return Reading(course_id, source_url, read_at, status=STATUS_ERROR, error=f"email: {e}", timezone=timezone)
    subject = SUBJECT_NOISE.sub("", parsed["subject"]).strip() or "(no subject)"
    src = source_url or (f"email:{parsed['message_id']}" if parsed["message_id"] else "email")
    items: list[Item] = []
    seen: set[str] = set()
    for sentence in candidate_sentences(parsed["body"]):
        title, review_reason = _title_for(sentence, subject, known_titles or [])
        if not title:
            continue
        k = slug(title)
        if k in seen:
            continue
        seen.add(k)
        kind = KIND_EXAM if re.search(r"\b(exam|midterm|quiz|test|final)\b", title, re.I) else KIND_ANNOUNCEMENT
        items.append(Item(
            title=title, date_text=sentence, kind=kind, url=src, section="email", posted_at=parsed["date"],
            detail=f"From: {parsed['from']} — Subject: {parsed['subject']}",
            review_reason=review_reason,
        ))
    return Reading(course_id, src, read_at, status=STATUS_OK, items=items, timezone=timezone, partial=True)


def _title_for(sentence: str, subject: str, known: list[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (title, review_reason).

    A known title mentioned in the sentence or subject wins, matched on words
    only: character-level similarity on short strings is how "project 1" gets
    scored against "oct 14". One clear match -> that title. Several equally
    good matches ("the midterm" when both Midterm 1 and Midterm 2 exist) or no
    match -> the mention is kept but flagged for review; it never lands on the
    calendar as a guess."""
    scores: dict[str, float] = {}
    for t in known:
        s = max(_mention_score(t, sentence), _mention_score(t, subject) * 0.9)
        if s >= MATCH_THRESHOLD:
            scores[t] = s
    if scores:
        top = max(scores.values())
        winners = [t for t, s in scores.items() if s == top]
        if len(winners) == 1:
            # unique among everything the bot believes for this course
            return winners[0], None
        return winners[0], "email mention matches several items: " + ", ".join(sorted(winners)) + "; confirm which one"
    m = ITEM_HINT.search(sentence) or ITEM_HINT.search(subject)
    if m:
        return clean_text(m.group(1)).title(), "email mentions an item that is not in the course belief; confirm"
    if DATE_HINT.search(sentence):
        return subject, "dated email with no recognizable item; confirm"
    return None, None


def _mention_score(title: str, text: str) -> float:
    st = slug(title)
    if not st:
        return 0.0
    words = st.split()
    low_words = slug(text).split()
    if not low_words:
        return 0.0
    if st in " ".join(low_words):
        return 1.0
    core = [w for w in words if not w.isdigit()]
    if core and all(w in low_words for w in core):
        # "the midterm" mentions "Midterm 1" but cannot tell it from "Midterm 2"
        return 0.8 if not any(w.isdigit() for w in words) else 0.6
    return 0.0
