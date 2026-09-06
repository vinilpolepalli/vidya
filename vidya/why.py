"""Every date has a receipt. `vidya why <key or title>` explains where a
calendar event came from: the page text as written, every assumption, each time
it moved and what the source said, and the calendar event it maps to."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .digest import committed_runs
from .model import ADDED, MOVED, REMOVED, REWORDED, Event
from .store import Store


def find_events(store: Store, query: str) -> list[Event]:
    """Exact key first, then case-insensitive title match, then substring."""
    q = query.strip()
    belief = store.all_belief()
    everything = [e for evs in belief.values() for e in evs]
    exact = [e for e in everything if e.key == q]
    if exact:
        return exact
    ql = q.lower()
    same_title = [e for e in everything if e.title.lower() == ql]
    if same_title:
        return same_title
    return [e for e in everything if ql in e.title.lower() or ql in e.key.lower()]


def _when(iso: Optional[str], all_day: bool) -> str:
    if not iso:
        return "no date"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    if all_day:
        return dt.strftime("%a %b %d, %Y")
    off = dt.strftime("%z")
    off = f" ({off[:3]}:{off[3:]})" if off else ""
    return dt.strftime("%a %b %d, %Y %-I:%M %p") + off


def explain(store: Store, query: str) -> str:
    matches = find_events(store, query)
    if not matches:
        return f"Nothing in the belief matches {query!r}. Try `vidya status` for the exact titles."
    if len(matches) > 1 and len({e.key for e in matches}) > 1:
        lines = [f"{len(matches)} items match {query!r}; ask again with one of these keys:"]
        for e in matches:
            lines.append(f"- {e.key}  ({e.title}, {store.course_names().get(e.course_id, e.course_id)}, {_when(e.start, e.all_day)})")
        return "\n".join(lines)
    e = matches[0]
    names = store.course_names()
    course = names.get(e.course_id, e.course_id)
    lines = [f"# {e.title} — {course}", ""]
    lines.append(f"**Now:** {_when(e.start, e.all_day)}" + (f" to {_when(e.end, e.all_day)}" if e.end and e.end != e.start else ""))
    lines.append(f"**As written on the page:** \"{e.date_text}\"")
    if e.sources:
        lines.append("**Source" + ("s" if len(e.sources) > 1 else "") + ":** " + ", ".join(e.sources))
    lines.append(f"**Last read:** {e.read_at or 'unknown'}   **Confidence:** {e.confidence:.2f}")
    if e.assumptions:
        lines.append("**Assumptions I had to make:**")
        for a in e.assumptions:
            lines.append(f"- {a}")
    if e.needs_review:
        lines.append(f"**Needs review:** {e.review_reason} (not on the calendar)")
    entry = store.ledger.get(e.key)
    ev_id = entry.get("event_id") if isinstance(entry, dict) else entry
    written = f" (written {entry['written_at'][:16]})" if isinstance(entry, dict) and entry.get("written_at") else ""
    lines.append(f"**Calendar event:** {ev_id or 'none (not written yet)'}{written}   **key:** `{e.key}`")
    missing = store.missing.get(e.key)
    if missing:
        lines.append(f"**Pending removal:** missing since {missing['first_missing']} ({missing['count']}/2 reads)")
    lines.append("")
    lines.append("## History")
    history = _history(store, e.key)
    if not history:
        lines.append("- no committed run mentions this item yet")
    for h in history:
        lines.append(h)
    return "\n".join(lines)


def _history(store: Store, key: str) -> list[str]:
    out: list[str] = []
    for run in committed_runs(store):
        day = (run["as_of"] or "")[:10] or run["run_id"]
        for c in run["changes"]:
            if c.key != key and not (c.after and c.after.key == key) and not (c.before and c.before.key == key):
                continue
            src = (c.after or c.before)
            s = f" (source: {src.sources[0]})" if src and src.sources else ""
            if c.type == ADDED and c.after:
                out.append(f"- {day}: first seen, {_when(c.after.start, c.after.all_day)}, page said \"{c.after.date_text}\"{s}")
            elif c.type == MOVED and c.before and c.after:
                out.append(f"- {day}: moved from {_when(c.before.start, c.before.all_day)} to {_when(c.after.start, c.after.all_day)}; "
                           f"page changed from \"{c.before.date_text}\" to \"{c.after.date_text}\"{s}")
            elif c.type == REWORDED and c.after:
                out.append(f"- {day}: title reworded to \"{c.after.title}\" (same date){s}")
            elif c.type == REMOVED:
                out.append(f"- {day}: confirmed removed after two successful reads")
            else:
                out.append(f"- {day}: {c.type} — {c.note}")
    return out


def explain_dict(store: Store, query: str) -> dict[str, Any]:
    matches = find_events(store, query)
    return {"query": query, "matches": [m.to_dict() for m in matches],
            "history": _history(store, matches[0].key) if len({m.key for m in matches}) == 1 else []}
