"""Command line entry point. Everything the bot runs on its cloud computer goes
through here, so each step is inspectable and re-runnable by hand.

Typical night:
  vidya plan --readings runs/tonight/       # diff + review, prints approved ops
  (bot applies each approved op through its calendar plugin, then:)
  vidya record <run> --key K --op create --event-id ID --status ok
  vidya commit <run>

Dry run without a real calendar:
  vidya plan --readings DIR --fake-apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import __version__
from .model import Reading
from .store import Store

DEFAULT_STATE = os.environ.get("VIDYA_STATE", "state")


def _store(args) -> Store:
    s = Store(args.state)
    if not s.exists() and getattr(args, "cmd", "") not in ("init", "selftest", "extract", "validate"):
        sys.exit(f"no state at {s.root}; run `vidya init --state {s.root}` first")
    return s


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---- commands ----------------------------------------------------------------

def cmd_init(args) -> int:
    store = Store(args.state)
    courses = None
    if args.courses:
        courses = json.loads(Path(args.courses).read_text(encoding="utf-8"))
    store.init(timezone_name=args.timezone, courses=courses)
    if args.calendar_id:
        cfg = store.config
        cfg["calendar_id"] = args.calendar_id
        store.save_config(cfg)
    print(f"initialized {store.root} (timezone {store.timezone}, {len(store.courses)} course(s))")
    if not store.courses:
        print("add courses to config.json: [{\"id\": \"data-structures\", \"name\": \"CS 201\", \"url\": \"https://...\"}]")
    return 0


def cmd_add_course(args) -> int:
    store = _store(args)
    cfg = store.config
    courses = [c for c in cfg.get("courses", []) if c["id"] != args.id]
    courses.append({"id": args.id, "name": args.name or args.id, "platform": args.platform,
                    "url": args.url or "", "timezone": args.timezone or store.timezone})
    cfg["courses"] = courses
    store.save_config(cfg)
    print(f"course {args.id} saved ({len(courses)} total)")
    return 0


def cmd_extract(args) -> int:
    read_at = args.read_at or _now_iso()
    if args.source == "html":
        from .extract.html import extract_html
        html = Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file != "-" else sys.stdin.read()
        reading = extract_html(html, args.course, args.url or "", read_at=read_at, timezone=args.timezone)
    elif args.source == "canvas":
        from .extract.canvas import extract_canvas_files, fetch_canvas
        if args.assignments_json or args.announcements_json or args.events_json:
            reading = extract_canvas_files(args.course, args.url or "", read_at, args.assignments_json,
                                           args.announcements_json, args.events_json, timezone=args.timezone)
        else:
            token = os.environ.get(args.token_env or "CANVAS_TOKEN", "")
            if not (args.base_url and args.canvas_course and token):
                sys.exit("canvas: need --base-url, --canvas-course and a token in $CANVAS_TOKEN (or --token-env)")
            reading = fetch_canvas(args.base_url, args.canvas_course, token, args.course, read_at, timezone=args.timezone)
    elif args.source == "ical":
        from .extract.ical import extract_ical, fetch_ical
        text = fetch_ical(args.file) if args.file.startswith(("http://", "https://")) else Path(args.file).read_text(encoding="utf-8", errors="replace")
        reading = extract_ical(text, args.course, args.url or args.file, read_at=read_at, timezone=args.timezone)
    elif args.source == "email":
        from .extract.email import extract_email
        raw = Path(args.file).read_bytes() if args.file != "-" else sys.stdin.buffer.read()
        store = Store(args.state)
        known = [e.title for e in store.belief(args.course)] if store.exists() else []
        reading = extract_email(raw, args.course, read_at=read_at, known_titles=known, timezone=args.timezone)
    else:
        sys.exit(f"unknown source {args.source}")
    out = json.dumps(reading.to_dict(), indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out + "\n", encoding="utf-8")
        print(f"{reading.course_id}: status={reading.status} items={len(reading.items)} -> {args.out}")
    else:
        print(out)
    return 0


def cmd_validate(args) -> int:
    problems = 0
    for f in _reading_files(args.paths):
        try:
            r = Reading.from_dict(json.loads(Path(f).read_text(encoding="utf-8")))
        except Exception as e:
            print(f"INVALID {f}: {e}")
            problems += 1
            continue
        from .resolve import resolve_reading
        events, review = resolve_reading(r)
        print(f"OK {f}: course={r.course_id} status={r.status} items={len(r.items)} resolved={len(events)} needs_review={len(review)}")
        for e in review:
            print(f"   review: {e.title!r} — {e.date_text!r} — {e.review_reason}")
    return 1 if problems else 0


def _reading_files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            out.extend(sorted(x for x in path.glob("*.json") if x.name not in ("expected.json", "courses.json")))
        else:
            out.append(path)
    return out


def cmd_plan(args) -> int:
    from .pipeline import fake_apply, plan_run
    store = _store(args)
    readings = []
    for f in _reading_files(args.readings):
        readings.append(Reading.from_dict(json.loads(Path(f).read_text(encoding="utf-8"))))
    if not readings:
        sys.exit("no readings found")
    run = plan_run(store, readings, run_id=args.run_id)
    print(run["summary"])
    print(f"run id: {run['run_id']}  (state {store.root})")
    if args.fake_apply:
        results = fake_apply(store, run["run_id"])
        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"fake calendar: applied {ok}/{len(results)} op(s); committed run {run['run_id']}")
    elif run["review"].approved:
        print("\nApproved operations (apply each, then `vidya record`, then `vidya commit`):")
        _print_json([o.to_dict() for o in run["review"].approved])
    return 0


def cmd_record(args) -> int:
    store = _store(args)
    result = {"key": args.key, "op": args.op, "event_id": args.event_id, "status": args.status,
              "summary": args.summary, "recorded_at": _now_iso()}
    if args.error:
        result["error"] = args.error
    results = store.record_partial(args.run_id, result)
    print(f"recorded {args.op} {args.key} -> {args.event_id or '-'} ({args.status}); {len(results)} result(s) so far")
    return 0


def cmd_commit(args) -> int:
    from .pipeline import commit_run
    store = _store(args)
    results: Optional[list[dict[str, Any]]] = None
    if args.results:
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    else:
        results = store.partial_results(args.run_id)
    out = commit_run(store, args.run_id, results)
    _print_json(out)
    return 0


def cmd_resolve_review(args) -> int:
    store = _store(args)
    if store.resolve_review(args.key, args.note or "resolved by owner", _now_iso()):
        print(f"resolved {args.key}; it stays out of summaries until its source text changes")
        return 0
    sys.exit(f"no review item with key {args.key!r}; see `vidya status`")


def cmd_status(args) -> int:
    store = _store(args)
    belief = store.all_belief()
    names = store.course_names()
    print(f"state: {store.root}   timezone: {store.timezone}   calendar: {store.config.get('calendar_id')}")
    for cid in store.course_ids() or sorted(belief):
        evs = belief.get(cid, [])
        print(f"- {names.get(cid, cid)} ({cid}): {len(evs)} believed item(s)")
    missing = store.missing
    if missing:
        print(f"pending removals: {len(missing)}")
        for k, v in missing.items():
            print(f"  - {k}: missing since {v['first_missing']} ({v['count']}/2)")
    nr = {k: v for k, v in store.needs_review.items() if not v.get("resolved")}
    resolved = len(store.needs_review) - len(nr)
    if nr or resolved:
        print(f"needs review: {len(nr)}" + (f" ({resolved} resolved by owner)" if resolved else ""))
        for k, v in nr.items():
            cand = f" candidate {v['candidate']}" if v.get("candidate") else ""
            print(f"  - {k}\n      {v.get('title')!r} ({v.get('course_id')}): \"{v.get('date_text')}\" — {v.get('reason')}{cand}")
    print(f"ledger: {len(store.ledger)} calendar event(s) tracked")
    unc = store.uncommitted_runs()
    if unc:
        print(f"uncommitted runs: {', '.join(unc)}")
    latest = store.latest_run_id()
    if latest:
        print(f"latest run: {latest}")
    return 0


def cmd_show(args) -> int:
    store = _store(args)
    rid = args.run_id or store.latest_run_id()
    if not rid:
        sys.exit("no runs yet")
    run = store.read_run(rid)
    print(run["summary"])
    if args.plan:
        _print_json(run["review"])
    return 0


def cmd_digest(args) -> int:
    from .digest import build_digest
    store = _store(args)
    print(build_digest(store, weeks=args.weeks))
    return 0


def cmd_graph(args) -> int:
    from .graph import export_episodes
    store = _store(args)
    rid = args.run_id or store.latest_run_id()
    if not rid:
        sys.exit("no runs yet")
    episodes = export_episodes(store, rid, group_id=args.group_id)
    if args.out:
        with Path(args.out).open("w", encoding="utf-8") as f:
            for ep in episodes:
                f.write(json.dumps(ep, ensure_ascii=False) + "\n")
        print(f"{len(episodes)} episode(s) -> {args.out}")
    else:
        for ep in episodes:
            print(json.dumps(ep, ensure_ascii=False))
    return 0


def cmd_selftest(args) -> int:
    from .selftest import run_selftest
    ok, report = run_selftest(Path(args.fixtures) if args.fixtures else None,
                              keep=Path(args.keep) if args.keep else None)
    print(report)
    return 0 if ok else 1


# ---- parser ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vidya", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"vidya {__version__}")
    p.add_argument("--state", default=DEFAULT_STATE, help="state directory (default: $VIDYA_STATE or ./state)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a state directory")
    s.add_argument("--timezone", default="America/New_York")
    s.add_argument("--courses", help="JSON file with the course list")
    s.add_argument("--calendar-id", help="Google Calendar id (default primary)")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("add-course", help="add or replace one course in config.json")
    s.add_argument("id")
    s.add_argument("--name")
    s.add_argument("--url")
    s.add_argument("--platform", default="other", choices=["brightspace", "canvas", "classroom", "moodle", "ical", "other"])
    s.add_argument("--timezone")
    s.set_defaults(fn=cmd_add_course)

    s = sub.add_parser("extract", help="turn a saved page / API JSON / iCal / email into a Reading JSON")
    s.add_argument("source", choices=["html", "canvas", "ical", "email"])
    s.add_argument("file", nargs="?", default="-", help="input file, URL (ical) or - for stdin")
    s.add_argument("--course", required=True, help="course id as in config.json")
    s.add_argument("--url", help="source URL to record for provenance")
    s.add_argument("--read-at", help="ISO timestamp of the read (default now)")
    s.add_argument("--timezone", default="America/New_York")
    s.add_argument("--out", help="write the Reading JSON here instead of stdout")
    s.add_argument("--base-url", help="canvas: https://school.instructure.com")
    s.add_argument("--canvas-course", help="canvas: numeric course id")
    s.add_argument("--token-env", help="canvas: env var holding the access token (default CANVAS_TOKEN)")
    s.add_argument("--assignments-json", help="canvas: offline assignments JSON")
    s.add_argument("--announcements-json", help="canvas: offline announcements JSON")
    s.add_argument("--events-json", help="canvas: offline calendar events JSON")
    s.set_defaults(fn=cmd_extract)

    s = sub.add_parser("validate", help="check Reading JSON files and show what would resolve")
    s.add_argument("paths", nargs="+")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("plan", help="diff readings against the belief, review, write the run")
    s.add_argument("--readings", nargs="+", required=True, help="Reading JSON files or directories")
    s.add_argument("--run-id")
    s.add_argument("--fake-apply", action="store_true", help="apply to the built-in fake calendar and commit")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("record", help="record one applied operation right after the plugin call")
    s.add_argument("run_id")
    s.add_argument("--key", required=True)
    s.add_argument("--op", required=True, choices=["create", "update", "delete"])
    s.add_argument("--event-id")
    s.add_argument("--status", default="ok", choices=["ok", "failed"])
    s.add_argument("--summary")
    s.add_argument("--error")
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("commit", help="advance belief and ledger after ops were applied")
    s.add_argument("run_id")
    s.add_argument("--results", help="JSON list of results (default: recorded partial results)")
    s.set_defaults(fn=cmd_commit)

    s = sub.add_parser("status", help="belief counts, pending removals, needs-review, ledger")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("resolve-review", help="mark a needs-review item as handled by the owner")
    s.add_argument("key")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_resolve_review)

    s = sub.add_parser("show", help="print a run's summary")
    s.add_argument("run_id", nargs="?")
    s.add_argument("--plan", action="store_true", help="also print the reviewed plan")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("digest", help="weekly digest: what moved, what is due, which course is volatile")
    s.add_argument("--weeks", type=int, default=1)
    s.set_defaults(fn=cmd_digest)

    s = sub.add_parser("graph", help="export a run as Graphiti episodes (JSONL)")
    s.add_argument("run_id", nargs="?")
    s.add_argument("--group-id", default="vidya")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_graph)

    s = sub.add_parser("selftest", help="run the fixture suite T1-T5")
    s.add_argument("--fixtures", help="fixture folder (default: the synthetic set shipped in the package)")
    s.add_argument("--keep", help="keep the temporary state under this folder for inspection")
    s.set_defaults(fn=cmd_selftest)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
