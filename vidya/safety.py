"""Opt-in safety check-ins. Off unless the owner turns it on and names contacts.

The Bot cannot see the owner's phone, so this is not location tracking. It is a
dead-man's switch on a schedule the owner picks:

  1. At the check-in time the Bot asks the owner (in their own conversation)
     to check in. Anything the owner says counts; `vidya safety checkin`
     records it.
  2. If the owner has not checked in by check-in time + grace, the engine
     approves one alert per contact, once per day, with the last check-in and
     (only if the owner shares it) a last-known place.
  3. If the owner checks in after an alert went out, one all-clear per alerted
     contact is approved.
  4. The owner can ask for a message to a contact ("tell mom I'm home").
     Owner-requested messages are approved because the owner is the source.
  5. Optionally, a weekly schedule share: next seven days of exams and
     deadlines to chosen contacts, once per week.

Everything the Bot may send comes out of `plan` with an idempotency key and is
logged with `record`. Nothing else is ever approved. The Bot sends through its
Gmail plugin; a contact "address" may be an email or a carrier SMS gateway
address if the carrier still offers one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from .store import Store

KIND_OWNER_REMINDER = "owner_reminder"   # sent in the owner's own conversation, never to a contact
KIND_MISSED_CHECKIN = "missed_checkin"
KIND_ALL_CLEAR = "all_clear"
KIND_OWNER_MESSAGE = "owner_message"
KIND_SCHEDULE_SHARE = "schedule_share"

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

DEFAULT_SAFETY: dict[str, Any] = {
    "enabled": False,
    "owner_name": "",
    "contacts": [],
    "checkin": {"enabled": True, "due": "21:00", "grace_minutes": 90, "days": list(DAYS)},
    "quiet_hours": {"start": "23:00", "end": "07:00"},
    "schedule_share": {"enabled": False, "day": "sun", "time": "18:00", "contacts": []},
    "max_messages_per_contact_per_day": 2,
    # The owner may share a last-known place (e.g. Google Maps location sharing
    # read by the Bot's browser). It is only ever included in a missed check-in
    # alert. Off by default.
    "include_location_in_alerts": False,
}


@dataclass
class Message:
    key: str
    kind: str
    to: str            # contact id, or "owner"
    to_name: str
    to_address: str    # empty for the owner (delivered in the Bot conversation)
    subject: str
    body: str
    reason: str
    blocked: Optional[str] = None  # set when the plan refuses to approve it

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyPlan:
    approved: list[Message] = field(default_factory=list)
    blocked: list[Message] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"approved": [m.to_dict() for m in self.approved],
                "blocked": [m.to_dict() for m in self.blocked],
                "notes": self.notes}


class Safety:
    def __init__(self, store: Store):
        self.store = store
        self.root = store.root / "safety"

    # ---- config -----------------------------------------------------------
    @property
    def config(self) -> dict[str, Any]:
        cfg = json.loads(json.dumps(DEFAULT_SAFETY))
        user = self.store.config.get("safety") or {}
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
        return cfg

    def save_config(self, safety_cfg: dict[str, Any]) -> None:
        cfg = self.store.config
        cfg["safety"] = safety_cfg
        self.store.save_config(cfg)

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.store.timezone)

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def contacts(self) -> list[dict[str, Any]]:
        return list(self.config.get("contacts") or [])

    def contact(self, cid: str) -> Optional[dict[str, Any]]:
        return next((c for c in self.contacts() if c["id"] == cid), None)

    # ---- state ------------------------------------------------------------
    def _read(self, name: str, default: Any) -> Any:
        return self.store._read(self.root / name, default)

    def _write(self, name: str, data: Any) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.store._write(self.root / name, data)

    @property
    def checkins(self) -> dict[str, dict[str, Any]]:
        return self._read("checkins.json", {})

    @property
    def sent(self) -> dict[str, dict[str, Any]]:
        return self._read("sent.json", {})

    @property
    def outbox(self) -> list[dict[str, Any]]:
        return self._read("outbox.json", [])

    # ---- owner actions ----------------------------------------------------
    def checkin(self, at: Optional[datetime] = None, note: str = "", location: str = "") -> dict[str, Any]:
        at = at or self.now()
        entry = {"at": at.isoformat(timespec="seconds"), "note": note, "location": location or None}
        c = self.checkins
        c[at.date().isoformat()] = entry
        self._write("checkins.json", c)
        return entry

    def last_checkin(self, before: Optional[date] = None) -> Optional[tuple[str, dict[str, Any]]]:
        items = sorted(self.checkins.items())
        if before is not None:
            items = [(d, e) for d, e in items if d <= before.isoformat()]
        return items[-1] if items else None

    def say(self, contact_id: str, text: str, at: Optional[datetime] = None) -> Message:
        """Queue an owner-requested message. Approved by `plan` because the
        owner is the source; still logged and idempotent."""
        c = self.contact(contact_id)
        if not c:
            raise KeyError(contact_id)
        at = at or self.now()
        digest = hashlib.sha1(f"{contact_id}|{text}|{at.date()}".encode()).hexdigest()[:10]
        name = self.config.get("owner_name") or "your student"
        msg = Message(
            key=f"say:{at.date()}:{contact_id}:{digest}", kind=KIND_OWNER_MESSAGE,
            to=contact_id, to_name=c["name"], to_address=c["address"],
            subject=f"Message from {name}",
            body=f"{text}\n\n(Sent by Vidya at {name}'s request, {at.strftime('%b %d, %I:%M %p %Z')}.)",
            reason="owner asked for it",
        )
        ob = self.outbox
        if not any(m["key"] == msg.key for m in ob):
            ob.append(msg.to_dict())
            self._write("outbox.json", ob)
        return msg

    def record(self, key: str, status: str = "ok", error: str = "", at: Optional[datetime] = None) -> dict[str, Any]:
        at = at or self.now()
        s = self.sent
        entry = {"status": status, "at": at.isoformat(timespec="seconds")}
        if error:
            entry["error"] = error
        kind, _, rest = key.partition(":")
        entry["kind"] = kind
        entry["to"] = self._to_from_key(key)
        s[key] = entry
        self._write("sent.json", s)
        if status == "ok" and key.startswith("say:"):
            self._write("outbox.json", [m for m in self.outbox if m["key"] != key])
        return entry

    @staticmethod
    def _to_from_key(key: str) -> str:
        parts = key.split(":")
        if parts[0] == "remind":
            return "owner"
        return parts[2] if len(parts) > 2 else ""

    # ---- the plan ---------------------------------------------------------
    def plan(self, now: Optional[datetime] = None) -> SafetyPlan:
        cfg = self.config
        out = SafetyPlan()
        if not cfg.get("enabled"):
            out.notes.append("safety check-ins are off (vidya safety enable)")
            return out
        now = now or self.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.tz)
        today = now.date()
        contacts = self.contacts()
        if not contacts:
            out.notes.append("no contacts; nothing can be sent")
        sent = self.sent
        sent_ok_today = {k for k, v in sent.items() if v.get("status") == "ok" and v.get("at", "")[:10] == today.isoformat()}

        def sent_ok(key: str) -> bool:
            return sent.get(key, {}).get("status") == "ok"

        def under_cap(cid: str) -> bool:
            n = sum(1 for k in sent_ok_today if self._to_from_key(k) == cid and not k.startswith("clear:"))
            return n < int(cfg.get("max_messages_per_contact_per_day", 2))

        def consider(msg: Message) -> None:
            if sent_ok(msg.key):
                return
            if msg.to != "owner" and not under_cap(msg.to) and msg.kind != KIND_ALL_CLEAR:
                msg.blocked = f"daily cap reached for {msg.to}"
                out.blocked.append(msg)
                return
            out.approved.append(msg)

        # 1-3. check-in
        ci = cfg["checkin"]
        weekday = DAYS[today.weekday()]
        if ci.get("enabled") and weekday in [d.lower()[:3] for d in ci.get("days", DAYS)]:
            due = datetime.combine(today, _parse_time(ci["due"]), tzinfo=now.tzinfo)
            grace_end = due + timedelta(minutes=int(ci.get("grace_minutes", 90)))
            todays = self.checkins.get(today.isoformat())
            if todays is None:
                if now >= grace_end:
                    for c in contacts:
                        consider(self._missed_alert(c, today, due, cfg))
                    if not contacts:
                        out.notes.append(f"check-in missed at {grace_end.strftime('%H:%M')} but there is nobody to tell")
                elif now >= due:
                    consider(Message(
                        key=f"remind:{today}", kind=KIND_OWNER_REMINDER, to="owner", to_name="owner", to_address="",
                        subject="Check-in",
                        body=(f"Quick check-in: are you good tonight? Reply with anything and I'll log it. "
                              f"If I don't hear from you by {grace_end.strftime('%-I:%M %p')}, I'll let "
                              f"{_names(contacts)} know I couldn't reach you."),
                        reason=f"check-in due {due.strftime('%H:%M')}, not yet received",
                    ))
                else:
                    out.notes.append(f"check-in due at {due.strftime('%H:%M %Z')}")
            else:
                out.notes.append(f"checked in today at {todays['at'][11:16]}")
                for c in contacts:
                    alert_key = f"missed:{today}:{c['id']}"
                    if sent_ok(alert_key):
                        consider(self._all_clear(c, today, todays, cfg))
        elif ci.get("enabled"):
            out.notes.append(f"no check-in scheduled on {weekday}")

        # 4. owner-requested messages
        for m in self.outbox:
            consider(Message(**m))

        # 5. weekly schedule share
        sh = cfg.get("schedule_share") or {}
        if sh.get("enabled") and sh.get("contacts"):
            share_day = DAYS.index(str(sh.get("day", "sun")).lower()[:3])
            share_at = datetime.combine(today, _parse_time(sh.get("time", "18:00")), tzinfo=now.tzinfo)
            if today.weekday() == share_day and now >= share_at:
                if _in_quiet_hours(now, cfg.get("quiet_hours") or {}):
                    out.notes.append("schedule share held: quiet hours")
                else:
                    week = today.isocalendar()
                    body = self._schedule_body(today, cfg)
                    for cid in sh["contacts"]:
                        c = self.contact(cid)
                        if not c:
                            out.notes.append(f"schedule share: unknown contact {cid}")
                            continue
                        consider(Message(
                            key=f"share:{week[0]}-W{week[1]:02d}:{cid}", kind=KIND_SCHEDULE_SHARE,
                            to=cid, to_name=c["name"], to_address=c["address"],
                            subject=f"{cfg.get('owner_name') or 'Your student'}'s week: exams and deadlines",
                            body=body, reason="weekly schedule share is on for this contact",
                        ))
        return out

    # ---- message bodies ---------------------------------------------------
    def _missed_alert(self, c: dict[str, Any], today: date, due: datetime, cfg: dict[str, Any]) -> Message:
        name = cfg.get("owner_name") or "your student"
        last = self.last_checkin(before=today - timedelta(days=1))
        last_line = "no earlier check-in on record"
        if last:
            d, e = last
            when = datetime.fromisoformat(e["at"]).strftime("%a %b %d, %-I:%M %p")
            last_line = f"last check-in {when}" + (f' ("{e["note"]}")' if e.get("note") else "")
        loc_line = ""
        if cfg.get("include_location_in_alerts"):
            loc = (last or ("", {}))[1].get("location") if last else None
            loc_line = f"\nLast known place shared by {name}: {loc or 'not available'}."
        body = (
            f"Hi {c['name']},\n\n"
            f"This is Vidya, {name}'s check-in assistant. {name} set up a nightly check-in with me and asked me "
            f"to let you know if I couldn't confirm it. Tonight I did not get a check-in by "
            f"{due.strftime('%-I:%M %p')} ({self.store.timezone}) plus the grace period.\n\n"
            f"This is an automatic message and does not mean anything is wrong; the usual reason is a phone on "
            f"silent or a long night in the library. A text or call to {name} is the right next step. "
            f"I will send you one more message if {name} checks in later.\n\n"
            f"Record: {last_line}.{loc_line}\n\n"
            f"You are receiving this because {name} added you as a safety contact. Reply to {name} directly; "
            f"this address is {name}'s own mailbox."
        )
        return Message(key=f"missed:{today}:{c['id']}", kind=KIND_MISSED_CHECKIN, to=c["id"], to_name=c["name"],
                       to_address=c["address"], subject=f"Check-in: could not reach {name} tonight",
                       body=body, reason=f"no check-in by {due.strftime('%H:%M')} + grace")

    def _all_clear(self, c: dict[str, Any], today: date, entry: dict[str, Any], cfg: dict[str, Any]) -> Message:
        name = cfg.get("owner_name") or "your student"
        when = datetime.fromisoformat(entry["at"]).strftime("%-I:%M %p")
        note = f' and said: "{entry["note"]}"' if entry.get("note") else ""
        body = (f"Hi {c['name']},\n\nAll clear: {name} checked in at {when}{note}. "
                f"Sorry for the worry, and thanks for being on the list.\n\nVidya")
        return Message(key=f"clear:{today}:{c['id']}", kind=KIND_ALL_CLEAR, to=c["id"], to_name=c["name"],
                       to_address=c["address"], subject=f"All clear: {name} checked in",
                       body=body, reason="owner checked in after an alert went out")

    def _schedule_body(self, today: date, cfg: dict[str, Any]) -> str:
        name = cfg.get("owner_name") or "Your student"
        names = self.store.course_names()
        horizon = today + timedelta(days=7)
        upcoming = []
        for evs in self.store.all_belief().values():
            for e in evs:
                if not e.start:
                    continue
                d = date.fromisoformat(e.start[:10])
                if today <= d <= horizon and e.kind in ("exam", "assignment"):
                    upcoming.append((d, e))
        upcoming.sort(key=lambda t: (t[0], t[1].title))
        lines = [f"{name}'s exams and deadlines, {today.strftime('%b %d')} to {horizon.strftime('%b %d')}:", ""]
        if not upcoming:
            lines.append("- nothing due this week")
        for d, e in upcoming:
            lines.append(f"- {d.strftime('%a %b %d')}: {e.title} ({names.get(e.course_id, e.course_id)}, {e.kind})")
        lines += ["", f"Shared weekly by Vidya because {name} turned this on. Dates come from the course pages; "
                      f"anything the pages left ambiguous is not listed."]
        return "\n".join(lines)


# ---- helpers -----------------------------------------------------------------

def _parse_time(s: str) -> time:
    h, _, m = str(s).partition(":")
    return time(int(h), int(m or 0))


def _in_quiet_hours(now: datetime, q: dict[str, Any]) -> bool:
    if not q or not q.get("start") or not q.get("end"):
        return False
    start, end = _parse_time(q["start"]), _parse_time(q["end"])
    t = now.time().replace(second=0, microsecond=0)
    if start <= end:
        return start <= t < end
    return t >= start or t < end


def _names(contacts: list[dict[str, Any]]) -> str:
    n = [c["name"] for c in contacts]
    if not n:
        return "nobody (no contacts yet)"
    if len(n) == 1:
        return n[0]
    return ", ".join(n[:-1]) + " and " + n[-1]
