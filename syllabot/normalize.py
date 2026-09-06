"""Text normalization and item identity.

The diff compares normalized items, never raw HTML, so page noise (timestamps,
session ids, "posted 3 hours ago") cannot show up as a change.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"), "-")
_QUOTES = {
    ord("\u2018"): "'",
    ord("\u2019"): "'",
    ord("\u201c"): '"',
    ord("\u201d"): '"',
    ord("\u00a0"): " ",
}
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^a-z0-9 ]+")


def clean_text(s: str) -> str:
    """Unicode-normalize, fold dashes and quotes, collapse whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_DASHES).translate(_QUOTES)
    return _WS.sub(" ", s).strip()


def slug(s: str) -> str:
    """Lowercase alphanumeric words joined by single spaces. Used for identity keys."""
    s = clean_text(s).lower()
    s = _PUNCT.sub(" ", s)
    return _WS.sub(" ", s).strip()


def item_key(course_id: str, title: str) -> str:
    """Identity of an item across nights: course plus normalized title.

    Kind is deliberately excluded: a heuristic classifier flipping between
    'exam' and 'assignment' must not look like a removal plus an addition.
    """
    return f"{course_id}::{slug(title)}"


def title_similarity(a: str, b: str) -> float:
    """0..1 similarity used to recognize a reworded title. Max of sequence ratio
    and token Jaccard so both 'Essay 1 draft'/'Essay 1: first draft' and
    reordered word forms score high."""
    sa, sb = slug(a), slug(b)
    if not sa or not sb:
        return 0.0
    ratio = SequenceMatcher(None, sa, sb).ratio()
    ta, tb = set(sa.split()), set(sb.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return max(ratio, jaccard)
