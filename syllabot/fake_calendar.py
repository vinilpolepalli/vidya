"""A JSON-backed stand-in for Google Calendar.

Used by the test suite, by `syllabot selftest`, and by an installer who wants
to watch the loop run end to end before connecting a real calendar. It applies
the same operations the bot would apply through its calendar plugin and
returns the same shape of results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .model import OP_CREATE, OP_DELETE, OP_UPDATE, CalendarOp


class FakeCalendar:
    def __init__(self, path: Optional[Path] = None):
        self.path = path
        self.events: dict[str, dict[str, Any]] = {}
        self._seq = 0
        if path and path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.events = data.get("events", {})
            self._seq = int(data.get("seq", len(self.events)))

    def apply(self, ops: list[CalendarOp]) -> list[dict[str, Any]]:
        results = []
        for op in ops:
            try:
                results.append(self._apply_one(op))
            except KeyError as e:
                results.append({"key": op.key, "op": op.op, "status": "failed", "error": str(e)})
        self.save()
        return results

    def _apply_one(self, op: CalendarOp) -> dict[str, Any]:
        base = {"key": op.key, "op": op.op, "summary": op.summary, "start": op.start, "end": op.end}
        if op.op == OP_CREATE:
            self._seq += 1
            eid = f"fake-{self._seq:04d}"
            self.events[eid] = self._body(op, eid)
            return {**base, "event_id": eid, "status": "ok"}
        if op.op == OP_UPDATE:
            if not op.event_id or op.event_id not in self.events:
                raise KeyError(f"event {op.event_id!r} not found for update")
            self.events[op.event_id] = self._body(op, op.event_id)
            return {**base, "event_id": op.event_id, "status": "ok"}
        if op.op == OP_DELETE:
            if not op.event_id or op.event_id not in self.events:
                raise KeyError(f"event {op.event_id!r} not found for delete")
            del self.events[op.event_id]
            return {**base, "event_id": op.event_id, "status": "ok"}
        raise KeyError(f"unknown op {op.op}")

    @staticmethod
    def _body(op: CalendarOp, eid: str) -> dict[str, Any]:
        return {
            "id": eid, "summary": op.summary, "start": op.start, "end": op.end,
            "all_day": op.all_day, "timezone": op.timezone, "colorId": op.color_id,
            "description": op.description, "key": op.key,
        }

    def save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"seq": self._seq, "events": self.events}, indent=2), encoding="utf-8")

    def __len__(self) -> int:
        return len(self.events)

    def by_key(self) -> dict[str, dict[str, Any]]:
        return {e["key"]: e for e in self.events.values()}
