"""Safety check-ins. Off by default; when on, the engine decides what may be
sent and every message is idempotent. The Bot only sends what `plan` approves."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from vidya.fixtures import load_readings
from vidya.pipeline import fake_apply, plan_run
from vidya.safety import (KIND_ALL_CLEAR, KIND_MISSED_CHECKIN, KIND_OWNER_MESSAGE, KIND_OWNER_REMINDER,
                          KIND_SCHEDULE_SHARE, Safety)

TZ = ZoneInfo("America/New_York")


def at(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=TZ)


@pytest.fixture
def safety(store):
    sf = Safety(store)
    cfg = sf.config
    cfg.update({"enabled": True, "owner_name": "Sam"})
    cfg["contacts"] = [
        {"id": "mom", "name": "Mom", "address": "mom@example.com", "consented": True},
        {"id": "dad", "name": "Dad", "address": "5551234567@vtext.com", "consented": True},
    ]
    cfg["checkin"] = {"enabled": True, "due": "21:00", "grace_minutes": 90, "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]}
    sf.save_config(cfg)
    return sf


def keys(plan):
    return sorted(m.key for m in plan.approved)


def test_off_by_default_sends_nothing(store):
    sf = Safety(store)
    plan = sf.plan(now=at("2026-09-07T23:59"))
    assert plan.approved == [] and plan.blocked == []
    assert any("off" in n for n in plan.notes)


def test_nothing_before_due(safety):
    assert keys(safety.plan(now=at("2026-09-07T20:59"))) == []


def test_owner_is_reminded_first_and_only_once(safety):
    p = safety.plan(now=at("2026-09-07T21:05"))
    assert [m.kind for m in p.approved] == [KIND_OWNER_REMINDER]
    assert p.approved[0].to == "owner" and p.approved[0].to_address == ""
    safety.record(p.approved[0].key, at=at("2026-09-07T21:05"))
    assert keys(safety.plan(now=at("2026-09-07T21:45"))) == []
    # still inside the grace period: contacts are not told
    assert all(m.kind != KIND_MISSED_CHECKIN for m in safety.plan(now=at("2026-09-07T22:29")).approved)


def test_checkin_before_grace_ends_means_no_alert(safety):
    safety.checkin(at=at("2026-09-07T21:40"), note="library")
    p = safety.plan(now=at("2026-09-07T23:30"))
    assert keys(p) == []
    assert any("checked in today" in n for n in p.notes)


def test_missed_checkin_alerts_each_contact_once(safety):
    p = safety.plan(now=at("2026-09-07T22:31"))
    assert keys(p) == ["missed:2026-09-07:dad", "missed:2026-09-07:mom"]
    m = next(x for x in p.approved if x.to == "mom")
    assert m.to_address == "mom@example.com" and "Sam" in m.body and "does not mean anything is wrong" in m.body
    assert "Last known place" not in m.body  # location is opt-in
    safety.record("missed:2026-09-07:mom", at=at("2026-09-07T22:32"))
    safety.record("missed:2026-09-07:dad", status="failed", error="bounced", at=at("2026-09-07T22:32"))
    # a failed send is retried, a successful one is not repeated
    assert keys(safety.plan(now=at("2026-09-07T22:45"))) == ["missed:2026-09-07:dad"]
    safety.record("missed:2026-09-07:dad", at=at("2026-09-07T22:46"))
    assert keys(safety.plan(now=at("2026-09-07T23:59"))) == []


def test_late_checkin_after_alert_sends_one_all_clear(safety):
    safety.record("missed:2026-09-07:mom", at=at("2026-09-07T22:32"))
    safety.record("missed:2026-09-07:dad", at=at("2026-09-07T22:32"))
    safety.checkin(at=at("2026-09-07T23:10"), note="phone died")
    p = safety.plan(now=at("2026-09-07T23:11"))
    assert [m.kind for m in p.approved] == [KIND_ALL_CLEAR, KIND_ALL_CLEAR]
    assert "phone died" in p.approved[0].body
    for m in p.approved:
        safety.record(m.key, at=at("2026-09-07T23:12"))
    assert keys(safety.plan(now=at("2026-09-07T23:30"))) == []


def test_all_clear_only_for_contacts_who_were_alerted(safety):
    safety.record("missed:2026-09-07:mom", at=at("2026-09-07T22:32"))
    safety.checkin(at=at("2026-09-07T23:10"))
    assert keys(safety.plan(now=at("2026-09-07T23:11"))) == ["clear:2026-09-07:mom"]


def test_next_day_starts_clean(safety):
    safety.record("missed:2026-09-07:mom", at=at("2026-09-07T22:32"))
    safety.record("missed:2026-09-07:dad", at=at("2026-09-07T22:32"))
    assert keys(safety.plan(now=at("2026-09-08T20:00"))) == []
    assert keys(safety.plan(now=at("2026-09-08T22:31"))) == ["missed:2026-09-08:dad", "missed:2026-09-08:mom"]


def test_days_filter(safety):
    cfg = safety.config
    cfg["checkin"]["days"] = ["fri", "sat"]
    safety.save_config(cfg)
    assert keys(safety.plan(now=at("2026-09-07T23:00"))) == []   # a Monday
    assert len(keys(safety.plan(now=at("2026-09-11T23:00")))) == 2  # a Friday


def test_owner_message_is_approved_and_idempotent(safety):
    m = safety.say("mom", "Home safe, talk tomorrow", at=at("2026-09-07T19:00"))
    assert m.kind == KIND_OWNER_MESSAGE and m.to_address == "mom@example.com"
    p = safety.plan(now=at("2026-09-07T19:01"))
    assert keys(p) == [m.key]
    safety.say("mom", "Home safe, talk tomorrow", at=at("2026-09-07T19:02"))  # same text same day: same key
    assert len(safety.outbox) == 1
    safety.record(m.key, at=at("2026-09-07T19:03"))
    assert safety.outbox == []
    assert keys(safety.plan(now=at("2026-09-07T19:04"))) == []


def test_unknown_contact_is_refused(safety):
    with pytest.raises(KeyError):
        safety.say("uncle", "hi")


def test_daily_cap_blocks_but_never_the_all_clear(safety):
    cfg = safety.config
    cfg["max_messages_per_contact_per_day"] = 1
    safety.save_config(cfg)
    safety.say("mom", "first", at=at("2026-09-07T18:00"))
    safety.record(next(m.key for m in safety.plan(now=at("2026-09-07T18:01")).approved if m.to == "mom"), at=at("2026-09-07T18:01"))
    p = safety.plan(now=at("2026-09-07T22:31"))
    assert keys(p) == ["missed:2026-09-07:dad"]
    assert [b.key for b in p.blocked] == ["missed:2026-09-07:mom"] and "cap" in p.blocked[0].blocked
    # an all-clear is never capped
    safety.record("missed:2026-09-07:dad", at=at("2026-09-07T22:32"))
    safety.checkin(at=at("2026-09-07T23:00"))
    assert keys(safety.plan(now=at("2026-09-07T23:01"))) == ["clear:2026-09-07:dad"]


def test_location_only_when_opted_in(safety):
    safety.checkin(at=at("2026-09-06T21:00"), location="Butler Library")
    body = next(m for m in safety.plan(now=at("2026-09-07T22:31")).approved if m.to == "mom").body
    assert "Butler" not in body
    cfg = safety.config
    cfg["include_location_in_alerts"] = True
    safety.save_config(cfg)
    body = next(m for m in safety.plan(now=at("2026-09-07T22:31")).approved if m.to == "mom").body
    assert "Last known place shared by Sam: Butler Library" in body
    assert "last check-in Sun Sep 06" in body


def test_weekly_schedule_share_once_per_week_from_belief(safety, store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    cfg = safety.config
    cfg["schedule_share"] = {"enabled": True, "day": "sun", "time": "18:00", "contacts": ["mom"]}
    cfg["checkin"]["enabled"] = False
    safety.save_config(cfg)
    assert keys(safety.plan(now=at("2026-09-13T17:59"))) == []          # Sunday, too early
    p = safety.plan(now=at("2026-09-13T18:05"))
    assert [m.kind for m in p.approved] == [KIND_SCHEDULE_SHARE]
    m = p.approved[0]
    assert m.to == "mom" and "Homework 1" in m.body and "Sep 13 to Sep 20" in m.body
    assert "Office hours" not in m.body  # only exams and assignments, never review items
    safety.record(m.key, at=at("2026-09-13T18:06"))
    assert keys(safety.plan(now=at("2026-09-13T19:00"))) == []
    assert keys(safety.plan(now=at("2026-09-14T18:05"))) == []          # Monday: not share day
    assert len(keys(safety.plan(now=at("2026-09-20T18:05")))) == 1      # next week: new key


def test_schedule_share_respects_quiet_hours(safety):
    cfg = safety.config
    cfg["schedule_share"] = {"enabled": True, "day": "sun", "time": "23:30", "contacts": ["mom"]}
    cfg["checkin"]["enabled"] = False
    safety.save_config(cfg)
    p = safety.plan(now=at("2026-09-13T23:45"))
    assert keys(p) == [] and any("quiet hours" in n for n in p.notes)
