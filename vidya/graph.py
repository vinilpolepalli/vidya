"""Graphiti episodes from a run.

Graphiti (Zep) is temporally aware: each fact carries a validity window, so
"the midterm was Oct 14, now it is Oct 16" becomes an edge with history instead
of an overwrite. That is what lets the digest answer "how many times has this
professor moved a deadline" without building anything.

This module only *builds* episodes; posting them is either the bot calling the
Graphiti MCP `add_memory` tool with each JSONL line, or `push_with_graphiti_core`
if graphiti-core is installed and a server is reachable (optional extra).

Episode shape (matches Graphiti's add_memory / add_episode parameters):
  name, episode_body, source ("text" | "json"), source_description,
  reference_time (ISO), group_id, uuid (deterministic per run+key: re-posting a
  run does not duplicate episodes)
"""

from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from datetime import datetime
from typing import Any, Optional

from .model import ADDED, MOVED, REMOVED, REWORDED, Change, Event
from .store import Store

NAMESPACE = _uuid.UUID("2f1c1d7e-6d3a-4d24-9e3f-7c1b1a7b0a11")


def episode_uuid(run_id: str, key: str, kind: str) -> str:
    return str(_uuid.uuid5(NAMESPACE, f"{run_id}|{kind}|{key}"))


def _when(ev: Optional[Event]) -> str:
    if ev is None or ev.start is None:
        return "an unknown date"
    if ev.all_day:
        return ev.start if ev.end in (None, ev.start) else f"{ev.start} to {ev.end}"
    return ev.start


def change_episode(run_id: str, ch: Change, names: dict[str, str], group_id: str, reference_time: str) -> Optional[dict[str, Any]]:
    course = names.get(ch.course_id, ch.course_id)
    src = (ch.after or ch.before)
    source_url = src.sources[0] if src and src.sources else "unknown source"
    if ch.type == MOVED:
        body = (f"In the course {course} ({ch.course_id}), the {ch.after.kind} '{ch.title}' was scheduled for "
                f"{_when(ch.before)} and is now scheduled for {_when(ch.after)}. Observed on {reference_time[:10]}. "
                f"Source: {source_url}.")
    elif ch.type == ADDED:
        body = (f"In the course {course} ({ch.course_id}), a new {ch.after.kind} '{ch.title}' is scheduled for "
                f"{_when(ch.after)}. First seen on {reference_time[:10]}. Source: {source_url}.")
    elif ch.type == REMOVED:
        body = (f"In the course {course} ({ch.course_id}), the {ch.before.kind} '{ch.title}' previously scheduled for "
                f"{_when(ch.before)} was removed from the course page. Confirmed absent on {reference_time[:10]}.")
    elif ch.type == REWORDED:
        body = (f"In the course {course} ({ch.course_id}), the item '{ch.before.title}' is now titled '{ch.after.title}'; "
                f"its date {_when(ch.after)} did not change. Observed on {reference_time[:10]}.")
    else:
        return None
    return {
        "uuid": episode_uuid(run_id, ch.key, ch.type),
        "name": f"{ch.type}: {ch.title} ({ch.course_id})",
        "episode_body": body,
        "source": "text",
        "source_description": f"vidya nightly diff, run {run_id}",
        "reference_time": reference_time,
        "group_id": group_id,
    }


def snapshot_episode(run_id: str, course_id: str, events: list[Event], names: dict[str, str], group_id: str,
                     reference_time: str) -> dict[str, Any]:
    payload = {
        "course": {"id": course_id, "name": names.get(course_id, course_id)},
        "observed_on": reference_time[:10],
        "items": [
            {"title": e.title, "kind": e.kind, "start": e.start, "end": e.end, "all_day": e.all_day,
             "source": e.sources[0] if e.sources else None}
            for e in events if e.start
        ],
    }
    return {
        "uuid": episode_uuid(run_id, course_id, "snapshot"),
        "name": f"snapshot: {names.get(course_id, course_id)} on {reference_time[:10]}",
        "episode_body": json.dumps(payload, ensure_ascii=False),
        "source": "json",
        "source_description": f"vidya belief snapshot, run {run_id}",
        "reference_time": reference_time,
        "group_id": group_id,
    }


def export_episodes(store: Store, run_id: str, group_id: str = "vidya", include_snapshots: bool = True) -> list[dict[str, Any]]:
    run = store.read_run(run_id)
    names = store.course_names()
    diff = run["diff"]
    ref = run["meta"].get("created_at") or datetime.now().astimezone().isoformat()
    for r in (store.run_dir(run_id) / "readings").glob("*.json"):
        try:
            ref = max(ref, json.loads(r.read_text(encoding="utf-8")).get("read_at", ""))
        except (OSError, ValueError):
            pass
    episodes: list[dict[str, Any]] = []
    for c in diff.get("changes", []):
        ep = change_episode(run_id, Change.from_dict(c), names, group_id, ref)
        if ep:
            episodes.append(ep)
    if include_snapshots:
        for cid, evs in diff.get("proposed_belief", {}).items():
            events = [Event.from_dict(e) for e in evs]
            if events:
                episodes.append(snapshot_episode(run_id, cid, events, names, group_id, ref))
    return episodes


def push_with_graphiti_core(episodes: list[dict[str, Any]], uri: str, user: str = "", password: str = "") -> int:
    """Optional: post episodes straight to a Graphiti instance with graphiti-core.
    Requires `pip install vidya[graph]`, a running FalkorDB/Neo4j and an LLM
    key in the environment (Graphiti extracts entities with an LLM on ingest)."""
    import asyncio

    from graphiti_core import Graphiti  # type: ignore
    from graphiti_core.nodes import EpisodeType  # type: ignore

    async def _run() -> int:
        g = Graphiti(uri, user, password)
        try:
            await g.build_indices_and_constraints()
            n = 0
            for ep in episodes:
                await g.add_episode(
                    name=ep["name"], episode_body=ep["episode_body"],
                    source=EpisodeType.json if ep["source"] == "json" else EpisodeType.text,
                    source_description=ep["source_description"],
                    reference_time=datetime.fromisoformat(ep["reference_time"]),
                    group_id=ep["group_id"], uuid=ep["uuid"],
                )
                n += 1
            return n
        finally:
            await g.close()

    return asyncio.run(_run())


def content_hash(ep: dict[str, Any]) -> str:
    return hashlib.sha1(ep["episode_body"].encode("utf-8")).hexdigest()[:12]
