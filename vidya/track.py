"""A generic dedupe ledger for the LLM-side skills that act in the world:
applications submitted, people messaged, coffee chats requested, projects
started. A skill checks `vidya track has <kind> <key>` before acting and
`vidya track add` right after, so nothing happens twice however many times a
routine re-runs. Plain JSON under state/track/<kind>.json."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from .store import Store

KIND_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


class Track:
    def __init__(self, store: Store):
        self.store = store
        self.root = store.root / "track"

    def _path(self, kind: str):
        if not KIND_RE.match(kind):
            raise ValueError(f"bad kind {kind!r}: lowercase letters, digits, - and _ only")
        return self.root / f"{kind}.json"

    def entries(self, kind: str) -> dict[str, dict[str, Any]]:
        return self.store._read(self._path(kind), {})

    def has(self, kind: str, key: str) -> bool:
        return key in self.entries(kind)

    def add(self, kind: str, key: str, note: str = "", at: Optional[datetime] = None) -> bool:
        """Returns True if newly added, False if it was already there (nothing changes)."""
        entries = self.entries(kind)
        if key in entries:
            return False
        entries[key] = {"added_at": (at or datetime.now().astimezone()).isoformat(timespec="seconds"), "note": note}
        self.store._write(self._path(kind), entries)
        return True

    def remove(self, kind: str, key: str) -> bool:
        entries = self.entries(kind)
        if key not in entries:
            return False
        del entries[key]
        self.store._write(self._path(kind), entries)
        return True

    def kinds(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.json"))
