"""Semester map and mastery ledger for the Course tutor skill.

The LLM teaches; this module decides *when*. Given the ordered topics of a
course and the exam dates the nightly check already believes, it lays numbered
classes onto real session days, keeps the material cumulative, and reserves the
last slot before each exam for review. The mastery ledger records how each
concept went so weak ones come back before the exam.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from .model import KIND_EXAM, Event
from .store import Store

DAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DEFAULT_DAYS = {1: ["tue"], 2: ["mon", "wed"], 3: ["mon", "wed", "fri"], 4: ["mon", "tue", "wed", "thu"],
                5: ["mon", "tue", "wed", "thu", "fri"]}


def _day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
    except ValueError:
        return date.fromisoformat(iso[:10])


def exams_for(store: Store, course_id: str, after: date) -> list[Event]:
    evs = [e for e in store.belief(course_id) if e.kind == KIND_EXAM and not e.needs_review and _day(e.start) and _day(e.start) >= after]
    return sorted(evs, key=lambda e: e.start or "")


def session_slots(start: date, end: date, days: list[str]) -> list[date]:
    idx = {DAY_INDEX[d.lower()[:3]] for d in days}
    out, d = [], start
    while d <= end:
        if d.weekday() in idx:
            out.append(d)
        d += timedelta(days=1)
    return out


def build_map(store: Store, course_id: str, topics: list[dict[str, Any]], start: date,
              per_week: int = 2, days: Optional[list[str]] = None, weeks_if_no_exam: int = 14) -> dict[str, Any]:
    """topics: ordered [{"title": ..., "source": "syllabus week 3", "exam": "<exam title>" (optional)}].
    Returns {"classes": [...], "exams": [...], "notes": [...]}."""
    days = days or DEFAULT_DAYS.get(max(1, min(per_week, 5)), ["mon", "wed"])
    exams = exams_for(store, course_id, start)
    notes: list[str] = []
    end = _day(exams[-1].start) if exams else start + timedelta(weeks=weeks_if_no_exam)
    if not exams:
        notes.append(f"no exam dates in the belief for {course_id}; mapped {weeks_if_no_exam} weeks from {start}")

    # Segments: everything up to each exam, in order. Topics tagged with an exam
    # title go to that segment; untagged topics are split in proportion to slots.
    exam_titles = [e.title for e in exams] or ["end of term"]
    exam_dates = [_day(e.start) for e in exams] or [end]
    seg_slots: list[list[date]] = []
    cursor = start
    for ed in exam_dates:
        slots = [d for d in session_slots(cursor, ed - timedelta(days=1), days)]
        seg_slots.append(slots)
        cursor = ed + timedelta(days=1)

    tagged = {i: [] for i in range(len(exam_titles))}
    untagged: list[dict[str, Any]] = []
    for t in topics:
        tag = (t.get("exam") or "").strip().lower()
        hit = next((i for i, name in enumerate(exam_titles) if tag and tag == name.lower()), None)
        (tagged[hit] if hit is not None else untagged).append(t)
    if untagged:
        total = sum(len(s) for s in seg_slots) or 1
        pos = 0
        for i, slots in enumerate(seg_slots):
            share = round(len(untagged) * len(slots) / total) if i < len(seg_slots) - 1 else len(untagged) - pos
            tagged[i].extend(untagged[pos:pos + share])
            pos += share

    classes: list[dict[str, Any]] = []
    n = 0
    for i, slots in enumerate(seg_slots):
        seg_topics = tagged[i]
        if not slots:
            if seg_topics:
                notes.append(f"no session days before {exam_titles[i]} ({exam_dates[i]}); {len(seg_topics)} topic(s) unplaced")
            continue
        review_slot = slots[-1] if len(slots) > 1 else None
        teach_slots = slots[:-1] if review_slot else slots
        if seg_topics and len(seg_topics) > len(teach_slots):
            notes.append(f"{len(seg_topics)} topics for {len(teach_slots)} classes before {exam_titles[i]}: some classes cover two topics")
        # Spread topics evenly over the teach slots, first topic in the first
        # class; slots left over become practice sessions after the topic that
        # precedes them, so practice always follows teaching.
        by_slot: dict[int, list[dict[str, Any]]] = {}
        if seg_topics and teach_slots:
            for ti, t in enumerate(seg_topics):
                slot = min(len(teach_slots) - 1, ti * len(teach_slots) // len(seg_topics))
                by_slot.setdefault(slot, []).append(t)
        for k, d in enumerate(teach_slots):
            ts = by_slot.get(k, [])
            kind = "class" if ts else "practice"
            n += 1
            classes.append({"n": n, "date": d.isoformat(), "kind": kind,
                            "topics": [t["title"] for t in ts], "sources": [t.get("source", "") for t in ts],
                            "for_exam": exam_titles[i]})
        if review_slot:
            n += 1
            classes.append({"n": n, "date": review_slot.isoformat(), "kind": "review", "topics": [t["title"] for t in seg_topics],
                            "sources": [], "for_exam": exam_titles[i]})
        classes.append({"n": None, "date": exam_dates[i].isoformat(), "kind": "exam", "topics": [], "sources": [],
                        "for_exam": exam_titles[i]})
    return {"course_id": course_id, "start": start.isoformat(), "days": days,
            "exams": [{"title": e.title, "date": _day(e.start).isoformat(), "key": e.key} for e in exams],
            "classes": classes, "notes": notes}


def render_map(store: Store, plan: dict[str, Any]) -> str:
    name = store.course_names().get(plan["course_id"], plan["course_id"])
    taught = [c for c in plan["classes"] if c["kind"] in ("class", "practice", "review")]
    weeks = max(1, (date.fromisoformat(plan["classes"][-1]["date"]) - date.fromisoformat(plan["start"])).days // 7 + 1) if plan["classes"] else 0
    lines = [f"# {name}: semester map", "",
             f"{weeks} weeks · {len(taught)} classes · {len(plan['exams'])} exam(s) · sessions {', '.join(plan['days'])}", ""]
    for c in plan["classes"]:
        d = date.fromisoformat(c["date"]).strftime("%a %b %d")
        if c["kind"] == "exam":
            lines.append(f"- **{d}: EXAM — {c['for_exam']}**")
        elif c["kind"] == "review":
            lines.append(f"- {d}: Class {c['n']} — review for {c['for_exam']} ({len(c['topics'])} topics)")
        elif c["kind"] == "practice":
            lines.append(f"- {d}: Class {c['n']} — practice (before {c['for_exam']})")
        else:
            lines.append(f"- {d}: Class {c['n']} — " + "; ".join(c["topics"]))
    for n in plan["notes"]:
        lines.append(f"\nnote: {n}")
    return "\n".join(lines)


# ---- mastery ledger --------------------------------------------------------------

class Mastery:
    """Per-course record of how each concept went. Scores: 0 confused, 1 shaky,
    2 got it, 3 taught it back. Weak = latest score < 2."""

    def __init__(self, store: Store, course_id: str):
        self.store = store
        self.path = store.root / "teach" / course_id / "mastery.json"

    def entries(self) -> dict[str, dict[str, Any]]:
        return self.store._read(self.path, {})

    def record(self, concept: str, score: int, note: str = "", at: Optional[datetime] = None) -> dict[str, Any]:
        if score not in (0, 1, 2, 3):
            raise ValueError("score must be 0, 1, 2 or 3")
        data = self.entries()
        e = data.setdefault(concept, {"history": []})
        e["history"].append({"at": (at or datetime.now().astimezone()).isoformat(timespec="seconds"), "score": score, "note": note})
        e["latest"] = score
        self.store._write(self.path, data)
        return e

    def weak(self) -> list[tuple[str, int, str]]:
        out = [(c, e["latest"], e["history"][-1]["at"]) for c, e in self.entries().items() if e.get("latest", 0) < 2]
        return sorted(out, key=lambda t: (t[1], t[2]))

    def summary(self) -> dict[str, int]:
        data = self.entries()
        return {"concepts": len(data), "weak": sum(1 for e in data.values() if e.get("latest", 0) < 2),
                "solid": sum(1 for e in data.values() if e.get("latest", 0) >= 2)}
