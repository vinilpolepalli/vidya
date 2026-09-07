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


def cmd_reset(args) -> int:
    store = _store(args)
    if not args.yes:
        sys.exit("reset forgets belief, ledger, runs, history and the review bucket (courses are kept); "
                 "re-run with --yes to confirm")
    removed = store.reset()
    print(f"reset {store.root}: cleared {', '.join(removed) or 'nothing'}; kept config.json ({len(store.courses)} course(s)) and readings/")
    return 0


def cmd_add_course(args) -> int:
    store = _store(args)
    cfg = store.config
    courses = [c for c in cfg.get("courses", []) if c["id"] != args.id]
    courses.append({"id": args.id, "name": args.name or args.id, "platform": args.platform,
                    "url": args.url or "", "timezone": args.timezone or store.timezone,
                    "kind": args.kind or "course"})
    cfg["courses"] = courses
    store.save_config(cfg)
    print(f"{args.kind or 'course'} {args.id} saved ({len(courses)} source(s) total)")
    return 0


def cmd_why(args) -> int:
    from .why import explain, explain_dict
    store = _store(args)
    query = " ".join(args.query)
    if args.json:
        _print_json(explain_dict(store, query))
    else:
        print(explain(store, query))
    return 0


def cmd_track(args) -> int:
    from .track import Track
    store = _store(args)
    tr = Track(store)
    try:
        if args.track_cmd == "add":
            new = tr.add(args.kind, args.key, note=args.note or "")
            print(("tracked" if new else "already tracked") + f" {args.kind}: {args.key}")
            return 0 if new else 1
        if args.track_cmd == "has":
            found = tr.has(args.kind, args.key)
            print(("yes" if found else "no") + f" {args.kind}: {args.key}")
            return 0 if found else 1
        if args.track_cmd == "remove":
            print(("removed" if tr.remove(args.kind, args.key) else "not tracked") + f" {args.kind}: {args.key}")
            return 0
        if args.track_cmd == "list":
            kinds = [args.kind] if args.kind else tr.kinds()
            for k in kinds:
                entries = tr.entries(k)
                print(f"{k}: {len(entries)}")
                for key, v in sorted(entries.items(), key=lambda kv: kv[1]["added_at"]):
                    print(f"  - {v['added_at'][:16]} {key}" + (f" — {v['note']}" if v.get("note") else ""))
            if not kinds:
                print("nothing tracked yet")
            return 0
    except ValueError as e:
        sys.exit(str(e))
    sys.exit(f"unknown track command {args.track_cmd}")


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
    kinds = {c["id"]: c.get("kind", "course") for c in store.courses}
    for cid in store.course_ids() or sorted(belief):
        evs = belief.get(cid, [])
        kind = kinds.get(cid, "course")
        tag = "" if kind == "course" else f" [{kind}]"
        print(f"- {names.get(cid, cid)}{tag} ({cid}): {len(evs)} believed item(s)")
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


def cmd_safety(args) -> int:
    from .safety import DAYS, Safety
    store = _store(args)
    sf = Safety(store)
    cfg = sf.config
    sub = args.safety_cmd

    def _now(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=sf.tz)

    if sub == "enable":
        cfg["enabled"] = True
        if args.owner_name:
            cfg["owner_name"] = args.owner_name
        sf.save_config(cfg)
        print(f"safety check-ins ON for {cfg.get('owner_name') or '(owner name not set: --owner-name)'}; "
              f"{len(cfg['contacts'])} contact(s); check-in {cfg['checkin']['due']} + {cfg['checkin']['grace_minutes']} min grace")
        if not cfg["contacts"]:
            print("add a contact: vidya safety add-contact mom --name Mom --address mom@example.com --consented")
        return 0
    if sub == "disable":
        cfg["enabled"] = False
        sf.save_config(cfg)
        print("safety check-ins OFF; nothing will be sent")
        return 0
    if sub == "add-contact":
        if not args.consented:
            sys.exit("a contact must have agreed to receive messages; re-run with --consented after asking them")
        contacts = [c for c in cfg["contacts"] if c["id"] != args.id]
        contacts.append({"id": args.id, "name": args.name or args.id, "address": args.address,
                         "relationship": args.relationship or "", "added_at": _now_iso(), "consented": True})
        cfg["contacts"] = contacts
        sf.save_config(cfg)
        print(f"contact {args.id} ({args.address}) saved; {len(contacts)} total")
        return 0
    if sub == "remove-contact":
        cfg["contacts"] = [c for c in cfg["contacts"] if c["id"] != args.id]
        cfg["schedule_share"]["contacts"] = [c for c in cfg["schedule_share"].get("contacts", []) if c != args.id]
        sf.save_config(cfg)
        print(f"contact {args.id} removed")
        return 0
    if sub == "set-checkin":
        ci = cfg["checkin"]
        if args.due:
            ci["due"] = args.due
        if args.grace is not None:
            ci["grace_minutes"] = args.grace
        if args.days:
            days = [d.strip().lower()[:3] for d in args.days.split(",")]
            bad = [d for d in days if d not in DAYS]
            if bad:
                sys.exit(f"unknown day(s): {bad}; use mon,tue,...")
            ci["days"] = days
        if args.off:
            ci["enabled"] = False
        if args.on:
            ci["enabled"] = True
        if args.include_location is not None:
            cfg["include_location_in_alerts"] = args.include_location
        sf.save_config(cfg)
        print(f"check-in {'on' if ci['enabled'] else 'off'}: due {ci['due']}, grace {ci['grace_minutes']} min, "
              f"days {','.join(ci['days'])}; location in alerts: {cfg['include_location_in_alerts']}")
        return 0
    if sub == "set-share":
        sh = cfg["schedule_share"]
        if args.off:
            sh["enabled"] = False
        else:
            sh["enabled"] = True
            if args.contacts:
                ids = [c.strip() for c in args.contacts.split(",")]
                unknown = [c for c in ids if not sf.contact(c)]
                if unknown:
                    sys.exit(f"unknown contact(s): {unknown}")
                sh["contacts"] = ids
            if args.day:
                sh["day"] = args.day.lower()[:3]
            if args.time:
                sh["time"] = args.time
        sf.save_config(cfg)
        print(f"weekly schedule share {'on' if sh['enabled'] else 'off'}: {sh['day']} {sh['time']} to {sh.get('contacts')}")
        return 0
    if sub == "checkin":
        e = sf.checkin(at=_now(args.at), note=args.note or "", location=args.location or "")
        print(f"checked in at {e['at']}" + (f" ({e['note']})" if e["note"] else ""))
        return 0
    if sub == "plan-note":
        day = datetime.fromisoformat(args.date).date()
        notes = sf.add_plan_note(day, args.note)
        print(f"{day}: {'; '.join(notes)} — the check-in reminder that night will mention it")
        return 0
    if sub == "location":
        e = sf.set_location(args.place, seen_at=_now(args.seen), source=args.source or "")
        print(f"last known place: {e['place']} (seen {e['seen_at']}); used only inside a missed-check-in alert"
              + ("" if cfg.get("include_location_in_alerts") else " — and location in alerts is currently OFF"))
        return 0
    if sub == "say":
        try:
            m = sf.say(args.contact, args.text, at=_now(args.at))
        except KeyError:
            sys.exit(f"unknown contact {args.contact!r}; see `vidya safety status`")
        print(f"queued {m.key}; it will appear in `vidya safety plan` until recorded as sent")
        return 0
    if sub == "plan":
        plan = sf.plan(now=_now(args.now))
        for n in plan.notes:
            print(f"note: {n}")
        if not plan.approved and not plan.blocked:
            print("nothing to send")
        for m in plan.blocked:
            print(f"blocked: {m.key} -> {m.to_name}: {m.blocked}")
        if plan.approved:
            print(f"\nApproved messages ({len(plan.approved)}); send each, then `vidya safety record <key>`:")
            _print_json([m.to_dict() for m in plan.approved])
        return 0
    if sub == "record":
        e = sf.record(args.key, status=args.status, error=args.error or "", at=_now(args.at))
        print(f"recorded {args.key} ({e['status']})")
        return 0
    if sub == "status":
        print(f"safety: {'ON' if cfg.get('enabled') else 'OFF'}   owner: {cfg.get('owner_name') or '-'}   tz: {store.timezone}")
        ci = cfg["checkin"]
        print(f"check-in: {'on' if ci['enabled'] else 'off'} at {ci['due']} + {ci['grace_minutes']} min grace on {','.join(ci['days'])}")
        sh = cfg["schedule_share"]
        print(f"schedule share: {'on' if sh.get('enabled') else 'off'} ({sh.get('day')} {sh.get('time')} to {sh.get('contacts') or []})")
        print(f"location in alerts: {cfg.get('include_location_in_alerts')}   cap: {cfg.get('max_messages_per_contact_per_day')}/contact/day")
        print(f"contacts: {len(cfg['contacts'])}")
        for c in cfg["contacts"]:
            print(f"  - {c['id']}: {c['name']} <{c['address']}> {c.get('relationship', '')}")
        last = sf.last_checkin()
        print(f"last check-in: {last[1]['at'] if last else 'never'}" + (f" ({last[1]['note']})" if last and last[1].get("note") else ""))
        loc = sf.location
        if loc:
            print(f"last known place: {loc['place']} (seen {loc['seen_at']})")
        ob = sf.outbox
        if ob:
            print(f"queued owner messages: {len(ob)}")
        sent = sf.sent
        if sent:
            print(f"sent log: {len(sent)} message(s)")
            for k, v in sorted(sent.items())[-5:]:
                print(f"  - {v['at']} {k} ({v['status']})")
        return 0
    sys.exit(f"unknown safety command {sub}")


def cmd_teach(args) -> int:
    from .teach import Mastery, build_map, render_map
    store = _store(args)
    if args.teach_cmd == "map":
        topics = json.loads(Path(args.topics).read_text(encoding="utf-8"))
        start = datetime.fromisoformat(args.start).date() if args.start else datetime.now().astimezone().date()
        days = [d.strip() for d in args.days.split(",")] if args.days else None
        plan = build_map(store, args.course, topics, start, per_week=args.per_week, days=days)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(render_map(store, plan))
        if args.out:
            print(f"\nplan -> {args.out}")
        return 0
    m = Mastery(store, args.course)
    if args.teach_cmd == "record":
        try:
            e = m.record(args.concept, args.score, note=args.note or "")
        except ValueError as err:
            sys.exit(str(err))
        print(f"{args.course}: {args.concept!r} = {args.score} ({len(e['history'])} attempt(s))")
        return 0
    if args.teach_cmd == "weak":
        weak = m.weak()
        if not weak:
            print("nothing weak on record")
        for concept, score, at in weak:
            print(f"- {concept} (latest {score}, {at[:10]})")
        return 0
    if args.teach_cmd == "status":
        s = m.summary()
        print(f"{args.course}: {s['concepts']} concept(s) on record, {s['solid']} solid, {s['weak']} weak")
        return 0
    sys.exit(f"unknown teach command {args.teach_cmd}")


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

    s = sub.add_parser("reset", help="forget belief/ledger/runs/history but keep the course list (dry run -> real calendar)")
    s.add_argument("--yes", action="store_true", help="confirm")
    s.set_defaults(fn=cmd_reset)

    s = sub.add_parser("add-source", aliases=["add-course"],
                       help="add or replace one watched source (a course, or any page with dates: registrar, aid, housing, club)")
    s.add_argument("id")
    s.add_argument("--name")
    s.add_argument("--url")
    s.add_argument("--platform", default="other", choices=["brightspace", "canvas", "blackboard", "classroom", "schoology", "moodle", "ical", "other"])
    s.add_argument("--kind", default="course", choices=["course", "registrar", "aid", "housing", "club", "program", "other"],
                   help="what kind of source this is (default course)")
    s.add_argument("--timezone")
    s.set_defaults(fn=cmd_add_course)

    s = sub.add_parser("why", help="the receipt for one item: page text, sources, assumptions, every move")
    s.add_argument("query", nargs="+", help="a key like data-structures::midterm 1, or a title")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_why)

    s = sub.add_parser("track", help="dedupe ledger for actions in the world (applications, outreach, coffee chats)")
    ts = s.add_subparsers(dest="track_cmd", required=True)
    x = ts.add_parser("add", help="record one action; exit 1 if it was already recorded"); x.add_argument("kind"); x.add_argument("key"); x.add_argument("--note")
    x = ts.add_parser("has", help="exit 0 if recorded, 1 if not"); x.add_argument("kind"); x.add_argument("key")
    x = ts.add_parser("remove"); x.add_argument("kind"); x.add_argument("key")
    x = ts.add_parser("list"); x.add_argument("kind", nargs="?")
    s.set_defaults(fn=cmd_track)

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

    s = sub.add_parser("safety", help="opt-in safety check-ins and messages to contacts the owner named")
    ss = s.add_subparsers(dest="safety_cmd", required=True)
    x = ss.add_parser("enable", help="turn safety check-ins on"); x.add_argument("--owner-name")
    ss.add_parser("disable", help="turn everything off")
    x = ss.add_parser("add-contact", help="add a person who agreed to receive messages")
    x.add_argument("id"); x.add_argument("--name"); x.add_argument("--address", required=True, help="email, or a carrier SMS gateway address")
    x.add_argument("--relationship"); x.add_argument("--consented", action="store_true", help="they agreed to be a contact")
    x = ss.add_parser("remove-contact"); x.add_argument("id")
    x = ss.add_parser("set-checkin", help="when the nightly check-in is due")
    x.add_argument("--due", help="HH:MM in the owner's time zone"); x.add_argument("--grace", type=int, help="minutes before contacts are told")
    x.add_argument("--days", help="comma list, e.g. mon,tue,wed,thu,fri,sat,sun")
    x.add_argument("--on", action="store_true"); x.add_argument("--off", action="store_true")
    x.add_argument("--include-location", dest="include_location", action="store_true", default=None, help="put the owner's shared last-known place in alerts")
    x.add_argument("--no-location", dest="include_location", action="store_false")
    x = ss.add_parser("set-share", help="weekly exams-and-deadlines email to chosen contacts")
    x.add_argument("--contacts", help="comma list of contact ids"); x.add_argument("--day", help="mon..sun"); x.add_argument("--time", help="HH:MM")
    x.add_argument("--off", action="store_true")
    x = ss.add_parser("checkin", help="the owner checked in (anything they say counts)")
    x.add_argument("--note"); x.add_argument("--location", help="only if the owner shares it"); x.add_argument("--at", help="ISO timestamp (default now)")
    x = ss.add_parser("plan-note", help="the owner has plans that night; the check-in reminder mentions them")
    x.add_argument("date", help="YYYY-MM-DD"); x.add_argument("note", help="short, e.g. 'home game, then the Sigma Chi mixer'")
    x = ss.add_parser("location", help="record a last-known place the owner shares (not a check-in)")
    x.add_argument("place"); x.add_argument("--seen", help="ISO timestamp it was observed (default now)"); x.add_argument("--source", help="e.g. google-maps-sharing")
    x = ss.add_parser("say", help="owner asks for a message to a contact")
    x.add_argument("contact"); x.add_argument("text"); x.add_argument("--at")
    x = ss.add_parser("plan", help="what may be sent right now (idempotent; safe to run every 30 minutes)")
    x.add_argument("--now", help="ISO timestamp to evaluate at (tests)")
    x = ss.add_parser("record", help="log one sent message right after the plugin call")
    x.add_argument("key"); x.add_argument("--status", default="ok", choices=["ok", "failed"]); x.add_argument("--error"); x.add_argument("--at")
    ss.add_parser("status")
    s.set_defaults(fn=cmd_safety)

    s = sub.add_parser("teach", help="semester map on real dates around the believed exams; mastery ledger")
    tt = s.add_subparsers(dest="teach_cmd", required=True)
    x = tt.add_parser("map", help="lay ordered topics onto session days; review before each exam")
    x.add_argument("course"); x.add_argument("--topics", required=True, help="JSON list of {title, source, exam?}")
    x.add_argument("--start", help="YYYY-MM-DD (default today)"); x.add_argument("--per-week", type=int, default=2)
    x.add_argument("--days", help="comma list, e.g. mon,wed"); x.add_argument("--out", help="write plan JSON here")
    x = tt.add_parser("record", help="how a concept went: 0 confused, 1 shaky, 2 got it, 3 taught it back")
    x.add_argument("course"); x.add_argument("concept"); x.add_argument("score", type=int); x.add_argument("--note")
    x = tt.add_parser("weak", help="concepts to re-teach before the exam"); x.add_argument("course")
    x = tt.add_parser("status"); x.add_argument("course")
    s.set_defaults(fn=cmd_teach)

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
