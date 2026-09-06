"""Heuristic HTML extractor for saved course pages.

This is the deterministic path used by the fixture suite and by the bot when it
can save a page from its browser. It does not know what Brightspace or Canvas
is. It looks for list items, table rows and cards that contain a date-like
string, takes the most title-like text in the block as the title and the most
date-like text as the date. Page chrome (nav, footer, timestamps, session ids)
is skipped, which is what keeps noise out of the diff.

If a page's layout defeats this, the bot's read-course skill falls back to
reading the page itself and writing the Reading JSON by hand.
"""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Optional

from ..dates import MD_RE, NUM_RE, ISO_RE, DM_RE
from ..model import (
    KIND_ANNOUNCEMENT, KIND_ASSIGNMENT, KIND_CLASS, KIND_EXAM, STATUS_EMPTY,
    STATUS_OK, Item, Reading,
)
from ..normalize import clean_text

VOID = {"br", "img", "input", "meta", "link", "hr", "area", "base", "col", "embed", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "template", "svg"}
SKIP_CLASS = re.compile(r"timestamp|generated|breadcrumb|footer|nav\b|navigation|menu|sidebar|meta\b|session|skip", re.I)
BLOCK_TAGS = {"li", "tr", "article"}
BLOCK_CLASS = re.compile(r"item|assignment|card|row|event|entry|announcement|post|deadline|task", re.I)
TITLE_CLASS = re.compile(r"title|name|subject|heading", re.I)
DATE_CLASS = re.compile(r"\bdate\b|due|deadline|when|time|schedule", re.I)
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
DATE_HINT = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b"
    r"|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b"
    r"|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{4}-\d{2}-\d{2}\b"
    r"|\btb[ad]\b|\b(?:mon|tues?|wed|thur?s?|fri|sat|sun)[a-z]*day|\bweek of\b|\b(?:before|in|after) class\b",
    re.I,
)
EXAM_RE = re.compile(r"\b(exam|midterm|quiz|test)\b|^final\b(?!.*\b(project|paper|essay|portfolio|presentation|report|draft)\b)", re.I)
CLASS_RE = re.compile(r"\b(lecture|class meeting|class session|lab session|recitation|seminar meeting)\b", re.I)
SECTION_RE = {
    "announcements": re.compile(r"announcement|news|updates", re.I),
    "assignments": re.compile(r"assignment|homework|assessment|dropbox|quizzes|to[- ]do", re.I),
    "syllabus": re.compile(r"syllabus|schedule|calendar|course outline|important dates", re.I),
}
POSTED_RE = re.compile(r"\bposted\b[:\s]*([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})", re.I)


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict[str, str], parent: Optional["Node"]):
        self.tag = tag
        self.attrs = attrs
        self.children: list = []  # Node or str
        self.parent = parent

    @property
    def cls(self) -> str:
        return (self.attrs.get("class") or "") + " " + (self.attrs.get("id") or "")

    def text(self) -> str:
        parts = []
        for c in self.children:
            if isinstance(c, str):
                parts.append(c)
            elif c.tag not in SKIP_TAGS and not SKIP_CLASS.search(c.cls):
                parts.append(c.text())
        return clean_text(" ".join(parts))

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find(self, pred) -> Optional["Node"]:
        for n in self.iter():
            if pred(n):
                return n
        return None


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.children.append(data)


def parse_html(html: str) -> Node:
    b = _TreeBuilder()
    b.feed(html)
    b.close()
    return b.root


def extract_html(html: str, course_id: str, source_url: str, read_at: Optional[str] = None,
                 timezone: str = "America/New_York") -> Reading:
    read_at = read_at or datetime.now().astimezone().isoformat(timespec="seconds")
    if not html or not html.strip():
        return Reading(course_id, source_url, read_at, status=STATUS_EMPTY,
                       error="empty document (0 bytes of content)", timezone=timezone)
    root = parse_html(html)
    body_text = root.text()
    if len(body_text) < 20:
        return Reading(course_id, source_url, read_at, status=STATUS_EMPTY,
                       error=f"document has almost no text ({len(body_text)} chars)", timezone=timezone)
    items: list[Item] = []
    _walk(root, "", items, source_url)
    return Reading(course_id, source_url, read_at, status=STATUS_OK, items=items, timezone=timezone)


def _section_for(node: Node, inherited: str) -> str:
    # a heading directly inside this node names the section for its content
    for c in node.children:
        if isinstance(c, Node) and c.tag in HEADINGS:
            t = c.text()
            for name, rx in SECTION_RE.items():
                if rx.search(t):
                    return name
    return inherited


def _is_block(n: Node) -> bool:
    if n.tag in BLOCK_TAGS:
        return True
    return n.tag in ("div", "section", "p") and bool(BLOCK_CLASS.search(n.cls))


def _walk(node: Node, section: str, items: list[Item], source_url: str) -> bool:
    """Depth-first. Returns True if this subtree emitted at least one item."""
    if node.tag in SKIP_TAGS or SKIP_CLASS.search(node.cls):
        return False
    section = _section_for(node, section)
    emitted = False
    for c in node.children:
        if isinstance(c, Node):
            emitted = _walk(c, section, items, source_url) or emitted
    if emitted:
        return True
    if _is_block(node):
        text = node.text()
        if text and DATE_HINT.search(text) and not _is_header_row(node):
            item = _item_from_block(node, section, source_url, text)
            if item:
                items.append(item)
                return True
    return False


def _is_header_row(n: Node) -> bool:
    if n.tag != "tr":
        return False
    cells = [c for c in n.children if isinstance(c, Node) and c.tag in ("td", "th")]
    return bool(cells) and all(c.tag == "th" for c in cells)


def _item_from_block(node: Node, section: str, source_url: str, text: str) -> Optional[Item]:
    title_node = node.find(lambda n: TITLE_CLASS.search(n.cls) and n.tag not in SKIP_TAGS)
    if title_node is None:
        title_node = node.find(lambda n: n.tag in HEADINGS)
    if title_node is None and node.tag == "tr":
        cells = [c for c in node.children if isinstance(c, Node) and c.tag in ("td", "th")]
        title_node = cells[0] if cells else None
    if title_node is None:
        title_node = node.find(lambda n: n.tag in ("a", "strong", "b"))
    title = title_node.text() if title_node is not None else ""

    time_nodes = [n for n in node.iter() if n.tag == "time"]
    date_nodes = [n for n in node.iter()
                  if DATE_CLASS.search(n.cls) and n is not title_node and n.tag != "time"]
    date_text = "; ".join(dict.fromkeys(n.text() for n in date_nodes if n.text()))
    if not date_text:
        # the block text minus the title and minus posting metadata: the date an
        # announcement was posted is not the date it talks about
        rest = text.replace(title, " ", 1) if title else text
        for tn in time_nodes:
            rest = rest.replace(tn.text(), " ")
        rest = POSTED_RE.sub(" ", rest)
        date_text = clean_text(rest)
    if not title:
        m = DATE_HINT.search(text)
        title = clean_text(text[: m.start()]) if m else ""
        title = re.sub(r"\b(due|deadline|on|by|at|posted)\b\s*[:\-]?\s*$", "", title, flags=re.I).strip(" :-")
    if not title or not DATE_HINT.search(date_text):
        return None

    posted_at = None
    t = node.find(lambda n: n.tag == "time" and n.attrs.get("datetime"))
    if t is not None:
        posted_at = t.attrs["datetime"][:10]
    else:
        pm = POSTED_RE.search(text)
        if pm:
            posted_at = _iso_from_text(pm.group(1))

    url_node = node.find(lambda n: n.tag == "a" and n.attrs.get("href"))
    url = url_node.attrs["href"] if url_node is not None else ""
    if url and url.startswith("/") and source_url:
        m = re.match(r"^(https?://[^/]+)", source_url)
        url = (m.group(1) if m else "") + url
    url = re.sub(r"([?&])(sid|session|token|_t)=[^&]*", r"\1", url).rstrip("?&")

    kind = KIND_ASSIGNMENT
    if section == "announcements":
        kind = KIND_ANNOUNCEMENT
    if EXAM_RE.search(title):
        kind = KIND_EXAM
    elif CLASS_RE.search(title):
        kind = KIND_CLASS

    detail = ""
    if section == "announcements":
        body = node.find(lambda n: n.tag == "p")
        detail = body.text() if body is not None else ""
    return Item(title=title, date_text=date_text, kind=kind, url=url or "", section=section,
                posted_at=posted_at, detail=detail)


def _iso_from_text(s: str) -> Optional[str]:
    s = clean_text(s)
    m = ISO_RE.search(s)
    if m:
        return m.group(0)
    m = MD_RE.search(s)
    if m and m.group(3):
        from ..dates import MONTHS
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = NUM_RE.search(s)
    if m and m.group(3):
        y = int(m.group(3))
        y = y + 2000 if y < 100 else y
        return f"{y:04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = DM_RE.search(s)
    if m and m.group(3):
        from ..dates import MONTHS
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return None
