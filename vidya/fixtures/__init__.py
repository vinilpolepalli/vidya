"""Loaders for fixture sets (the synthetic one shipped here, or a real one
captured with the T0 procedure into any folder with the same layout):

  <dir>/courses.json      [{"id","name","url","timezone",...}]
  <dir>/expected.json     planted changes for the day0 -> day1 diff
  <dir>/day0/<id>.html    baseline page per course
  <dir>/day1/<id>.html    page per course with planted changes
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..extract.html import extract_html
from ..model import Reading

HERE = Path(__file__).resolve().parent


def fixture_dir() -> Path:
    return HERE


def load_courses(root: Path = HERE) -> list[dict[str, Any]]:
    return json.loads((root / "courses.json").read_text(encoding="utf-8"))


def load_expected(root: Path = HERE) -> dict[str, Any]:
    return json.loads((root / "expected.json").read_text(encoding="utf-8"))


def load_readings(day: str, root: Path = HERE, read_at: str | None = None) -> list[Reading]:
    courses = load_courses(root)
    expected = load_expected(root)
    read_at = read_at or expected.get("read_at", {}).get(day) or f"2026-09-0{5 if day == 'day0' else 6}T23:00:00-04:00"
    readings = []
    for c in courses:
        path = root / day / f"{c['id']}.html"
        html = path.read_text(encoding="utf-8") if path.exists() else ""
        readings.append(extract_html(html, c["id"], c.get("url", ""), read_at=read_at,
                                     timezone=c.get("timezone", "America/New_York")))
    return readings
