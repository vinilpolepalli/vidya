"""On-disk state. Plain JSON so the owner can open any of it in a text editor.

state/
  config.json                 timezone, calendar id, course list
  belief/<course>.json        what we currently believe each course's dated items are
  missing.json                pending-removal tracker (key -> count, dates, event)
  ledger.json                 key -> calendar event id (idempotency)
  needs_review.json           key -> first_seen/last_seen/reason
  runs/<run_id>/              readings, diff, plan, review, summary for one run
  history/<course>/<run>.json readings archive (digest and graph episodes read this)
  fake_calendar.json          only when running with the built-in fake calendar
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .model import DEFAULT_TZ, CalendarOp, DiffResult, Event, Reading, ReviewResult

DEFAULT_CONFIG = {
    "timezone": DEFAULT_TZ,
    "calendar_id": "primary",
    "courses": [],
}


class Store:
    def __init__(self, root: os.PathLike | str):
        self.root = Path(root)

    # ---- layout -----------------------------------------------------------
    @property
    def config_path(self) -> Path:
        return self.root / "config.json"

    def init(self, timezone_name: str = DEFAULT_TZ, courses: Optional[list[dict[str, Any]]] = None) -> None:
        for sub in ("belief", "runs", "history", "readings"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            cfg = dict(DEFAULT_CONFIG)
            cfg["timezone"] = timezone_name
            cfg["courses"] = courses or []
            self._write(self.config_path, cfg)
        for name in ("missing.json", "ledger.json", "needs_review.json"):
            p = self.root / name
            if not p.exists():
                self._write(p, {})

    def exists(self) -> bool:
        return self.config_path.exists()

    # ---- config -----------------------------------------------------------
    @property
    def config(self) -> dict[str, Any]:
        return self._read(self.config_path, dict(DEFAULT_CONFIG))

    def save_config(self, cfg: dict[str, Any]) -> None:
        self._write(self.config_path, cfg)

    @property
    def timezone(self) -> str:
        return self.config.get("timezone") or DEFAULT_TZ

    @property
    def courses(self) -> list[dict[str, Any]]:
        return list(self.config.get("courses") or [])

    def course_names(self) -> dict[str, str]:
        return {c["id"]: c.get("name") or c["id"] for c in self.courses}

    def course_ids(self) -> list[str]:
        return [c["id"] for c in self.courses]

    # ---- belief / missing / ledger / review --------------------------------
    def belief(self, course_id: str) -> list[Event]:
        data = self._read(self.root / "belief" / f"{course_id}.json", {"events": []})
        return [Event.from_dict(e) for e in data.get("events", [])]

    def all_belief(self) -> dict[str, list[Event]]:
        out: dict[str, list[Event]] = {}
        for p in sorted((self.root / "belief").glob("*.json")):
            out[p.stem] = self.belief(p.stem)
        return out

    def save_belief(self, course_id: str, events: list[Event], as_of: str) -> None:
        self._write(self.root / "belief" / f"{course_id}.json",
                    {"course_id": course_id, "as_of": as_of, "events": [e.to_dict() for e in events]})

    @property
    def missing(self) -> dict[str, dict[str, Any]]:
        return self._read(self.root / "missing.json", {})

    def save_missing(self, m: dict[str, dict[str, Any]]) -> None:
        self._write(self.root / "missing.json", m)

    @property
    def ledger(self) -> dict[str, dict[str, Any]]:
        return self._read(self.root / "ledger.json", {})

    def save_ledger(self, l: dict[str, dict[str, Any]]) -> None:
        self._write(self.root / "ledger.json", l)

    @property
    def needs_review(self) -> dict[str, dict[str, Any]]:
        return self._read(self.root / "needs_review.json", {})

    def save_needs_review(self, nr: dict[str, dict[str, Any]]) -> None:
        self._write(self.root / "needs_review.json", nr)

    def record_needs_review(self, events: list[Event], seen_at: str) -> dict[str, dict[str, Any]]:
        """Track review items across runs. An item the owner resolved stays
        resolved while its source text is unchanged; new wording reopens it."""
        nr = self.needs_review
        for e in events:
            cur = nr.get(e.key) or {"first_seen": seen_at}
            if cur.get("resolved") and cur.get("date_text") != e.date_text:
                cur.pop("resolved", None)
                cur.pop("resolution", None)
                cur["reopened_at"] = seen_at
            cur.update({"last_seen": seen_at, "course_id": e.course_id, "title": e.title,
                        "date_text": e.date_text, "reason": e.review_reason,
                        "candidate": e.start, "sources": e.sources})
            nr[e.key] = cur
        self.save_needs_review(nr)
        return nr

    def resolve_review(self, key: str, note: str, at: str) -> bool:
        nr = self.needs_review
        if key not in nr:
            return False
        nr[key].update({"resolved": True, "resolution": note, "resolved_at": at})
        self.save_needs_review(nr)
        return True

    def open_review_keys(self) -> set[str]:
        return {k for k, v in self.needs_review.items() if not v.get("resolved")}

    # ---- runs -------------------------------------------------------------
    def new_run_id(self, now: Optional[datetime] = None) -> str:
        now = now or datetime.now(timezone.utc)
        base = now.strftime("%Y%m%d-%H%M%S")
        rid, n = base, 1
        while (self.root / "runs" / rid).exists():
            n += 1
            rid = f"{base}-{n}"
        return rid

    def run_dir(self, run_id: str) -> Path:
        return self.root / "runs" / run_id

    def write_run(self, run_id: str, readings: list[Reading], diff: DiffResult,
                  plan: list[CalendarOp], review: ReviewResult, summary: str) -> Path:
        d = self.run_dir(run_id)
        (d / "readings").mkdir(parents=True, exist_ok=True)
        for r in readings:
            self._write(d / "readings" / f"{r.course_id}.json", r.to_dict())
            hist = self.root / "history" / r.course_id
            hist.mkdir(parents=True, exist_ok=True)
            self._write(hist / f"{run_id}.json", r.to_dict())
        self._write(d / "diff.json", diff.to_dict())
        self._write(d / "plan.json", [o.to_dict() for o in plan])
        self._write(d / "review.json", review.to_dict())
        (d / "summary.md").write_text(summary, encoding="utf-8")
        self._write(d / "meta.json", {"run_id": run_id, "committed": False,
                                      "created_at": datetime.now(timezone.utc).isoformat()})
        return d

    def read_run(self, run_id: str) -> dict[str, Any]:
        d = self.run_dir(run_id)
        if not d.exists():
            raise FileNotFoundError(f"no run {run_id} under {d.parent}")
        return {
            "meta": self._read(d / "meta.json", {}),
            "diff": self._read(d / "diff.json", {}),
            "plan": [CalendarOp.from_dict(o) for o in self._read(d / "plan.json", [])],
            "review": self._read(d / "review.json", {}),
            "summary": (d / "summary.md").read_text(encoding="utf-8") if (d / "summary.md").exists() else "",
        }

    def latest_run_id(self) -> Optional[str]:
        runs = sorted(p.name for p in (self.root / "runs").glob("*") if p.is_dir())
        return runs[-1] if runs else None

    def mark_committed(self, run_id: str, results: list[dict[str, Any]]) -> None:
        d = self.run_dir(run_id)
        meta = self._read(d / "meta.json", {})
        meta.update({"committed": True, "committed_at": datetime.now(timezone.utc).isoformat()})
        self._write(d / "meta.json", meta)
        self._write(d / "results.json", results)
        partial = d / "results.partial.json"
        if partial.exists():
            partial.unlink()

    def record_partial(self, run_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
        """Append one applied-op result right after the write happened, so a
        crash before commit cannot lose the event id (and cause a duplicate)."""
        p = self.run_dir(run_id) / "results.partial.json"
        results = self._read(p, [])
        results = [r for r in results if not (r.get("key") == result.get("key") and r.get("op") == result.get("op"))]
        results.append(result)
        self._write(p, results)
        return results

    def partial_results(self, run_id: str) -> list[dict[str, Any]]:
        return self._read(self.run_dir(run_id) / "results.partial.json", [])

    def uncommitted_runs(self) -> list[str]:
        out = []
        for p in sorted(x for x in (self.root / "runs").glob("*") if x.is_dir()):
            if not self._read(p / "meta.json", {}).get("committed"):
                out.append(p.name)
        return out

    # ---- fake calendar ----------------------------------------------------
    @property
    def fake_calendar_path(self) -> Path:
        return self.root / "fake_calendar.json"

    # ---- io ---------------------------------------------------------------
    @staticmethod
    def _read(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
            f.write("\n")
        os.replace(tmp, path)
