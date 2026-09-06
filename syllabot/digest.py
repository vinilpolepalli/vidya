"""Weekly digest from local state: what is due, what moved, which course is
volatile. Works without Graphiti; the graph adds history queries on top."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from .model import ADDED, MOVED, REMOVED, REWORDED, Change, Event
from .store import Store


def _day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(iso[:10])


def committed_runs(store: Store) -> list[dict[str, Any]]:
    out = []
    for p in sorted(x for x in (store.root / "runs").glob("*") if x.is_dir()):
        meta = store._read(p / "meta.json", {})
        if not meta.get("committed"):
            continue
        diff = store._read(p / "diff.json", {})
        as_of = None
        for r in (p / "readings").glob("*.json"):
            ra = store._read(r, {}).get("read_at")
            if ra and (as_of is None or ra > as_of):
                as_of = ra
        out.append({"run_id": p.name, "as_of": as_of or meta.get("created_at", ""),
                    "changes": [Change.from_dict(c) for c in diff.get("changes", [])]})
    return out


def build_digest(store: Store, weeks: int = 1, today: Optional[date] = None) -> str:
    names = store.course_names()
    n = lambda cid: names.get(cid, cid)
    belief = store.all_belief()
    runs = committed_runs(store)
    if today is None:
        latest = max((r["as_of"] for r in runs if r["as_of"]), default=None)
        today = _day(latest) or date.today()
    horizon = today + timedelta(days=7 * weeks)
    since = today - timedelta(days=7 * weeks)

    lines = [f"# Weekly digest — week of {today.isoformat()}", ""]

    # 1. coming up
    upcoming: list[Event] = []
    for evs in belief.values():
        for e in evs:
            d = _day(e.start)
            if d and today <= d <= horizon:
                upcoming.append(e)
    upcoming.sort(key=lambda e: (e.start or "", e.title))
    lines.append(f"## Due in the next {7 * weeks} days ({len(upcoming)})")
    if not upcoming:
        lines.append("- nothing on the calendar in this window")
    cur_day = None
    for e in upcoming:
        d = _day(e.start)
        if d != cur_day:
            cur_day = d
            lines.append(f"**{d.strftime('%a %b %d')}**")
        when = "" if e.all_day else f" {datetime.fromisoformat(e.start).strftime('%-I:%M %p')}"
        lines.append(f"- {e.title} — {n(e.course_id)}{when}")
    lines.append("")

    # 2. what moved this week
    recent = [(r, c) for r in runs if r["as_of"] and _day(r["as_of"]) and since <= _day(r["as_of"]) <= today
              for c in r["changes"]]
    lines.append(f"## What changed since {since.isoformat()} ({len(recent)})")
    if not recent:
        lines.append("- no changes detected")
    for r, c in recent:
        src = (c.after or c.before)
        s = f" (source: {src.sources[0]})" if src and src.sources else ""
        lines.append(f"- {_day(r['as_of'])}: {c.type.upper()} — {n(c.course_id)}: {c.title} — {c.note}{s}")
    lines.append("")

    # 3. volatility this term
    moves: dict[str, int] = {}
    all_changes: dict[str, int] = {}
    for r in runs:
        for c in r["changes"]:
            if c.type == MOVED:
                moves[c.course_id] = moves.get(c.course_id, 0) + 1
            if c.type in (MOVED, ADDED, REMOVED, REWORDED) and not (c.type == ADDED and r is runs[0]):
                all_changes[c.course_id] = all_changes.get(c.course_id, 0) + 1
    lines.append("## Schedule volatility this term")
    if not moves and not all_changes:
        lines.append("- no deadline has moved yet")
    else:
        ranked = sorted(set(moves) | set(all_changes), key=lambda cid: (-moves.get(cid, 0), -all_changes.get(cid, 0), cid))
        for cid in ranked:
            m, a = moves.get(cid, 0), all_changes.get(cid, 0)
            lines.append(f"- {n(cid)}: {m} deadline move(s), {a} change(s) total")
        top = ranked[0]
        if moves.get(top):
            lines.append(f"- most volatile: {n(top)} ({moves[top]} move(s))")
    lines.append("")

    # 4. pending removals and review bucket
    missing = store.missing
    if missing:
        lines.append(f"## Pending removals ({len(missing)})")
        for k, v in missing.items():
            ev = v.get("event", {})
            lines.append(f"- {n(k.split('::')[0])}: {ev.get('title', k)} — missing since {v['first_missing']} ({v['count']}/2)")
        lines.append("")
    review = {k: v for k, v in store.needs_review.items() if not v.get("resolved")}
    if review:
        lines.append(f"## Needs your decision ({len(review)})")
        for k, v in review.items():
            lines.append(f"- {n(v.get('course_id', ''))}: {v.get('title')} — \"{v.get('date_text')}\" — {v.get('reason')}")
        lines.append("")
    return "\n".join(lines)
