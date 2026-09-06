"""T2. Run the full pipeline twice against the same snapshot. The second run
must produce zero changes and zero new events. A crash between applying and
committing must not produce duplicates either."""

from vidya.fake_calendar import FakeCalendar
from vidya.fixtures import load_readings
from vidya.model import OP_CREATE
from vidya.pipeline import fake_apply, plan_run
from vidya.selftest import t2_idempotency


def test_selftest_t2(fixtures, tmp_path):
    chk = t2_idempotency(fixtures, tmp_path)
    assert chk.passed, chk.failures


def test_replay_after_commit_is_a_noop(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    n = len(FakeCalendar(store.fake_calendar_path))
    for _ in range(3):
        run = plan_run(store, load_readings("day0", fixtures))
        assert run["diff"].changes == []
        assert run["review"].approved == []
        fake_apply(store, run["run_id"])
    assert len(FakeCalendar(store.fake_calendar_path)) == n


def test_crash_between_apply_and_commit_creates_nothing_twice(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    r1 = plan_run(store, load_readings("day1", fixtures))
    cal = FakeCalendar(store.fake_calendar_path)
    for res in cal.apply(r1["review"].approved):
        store.record_partial(r1["run_id"], res)
    n = len(FakeCalendar(store.fake_calendar_path))
    # no commit: simulate the bot dying here
    r2 = plan_run(store, load_readings("day1", fixtures))
    assert r2["recovered"] and r2["recovered"][0]["run_id"] == r1["run_id"]
    assert [o for o in r2["review"].approved if o.op == OP_CREATE] == []
    fake_apply(store, r2["run_id"])
    final = FakeCalendar(store.fake_calendar_path)
    assert len(final) == n
    assert len(final.by_key()) == len(final)


def test_ledger_matches_calendar_after_rewording(store, fixtures):
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    run = plan_run(store, load_readings("day1", fixtures))
    fake_apply(store, run["run_id"])
    cal = FakeCalendar(store.fake_calendar_path)
    assert set(store.ledger) == set(cal.by_key())
    assert "writing-seminar::essay 1 draft" not in store.ledger
    assert "writing-seminar::essay 1 first draft" in store.ledger


def test_reset_forgets_dry_run_but_keeps_courses(store, fixtures):
    """Setup playbook step 7: dry run on the fake calendar, `vidya reset`, then
    the first real plan must recreate everything and the run history must not
    contain the fake baseline."""
    boot = plan_run(store, load_readings("day0", fixtures))
    fake_apply(store, boot["run_id"])
    assert store.fake_calendar_path.exists()
    assert store.ledger
    courses_before = store.courses

    removed = store.reset()

    assert "ledger.json" in removed and "fake_calendar.json" in removed
    assert store.courses == courses_before
    assert store.ledger == {} and store.all_belief() == {}
    assert store.latest_run_id() is None
    assert not store.fake_calendar_path.exists()
    real = plan_run(store, load_readings("day0", fixtures))
    assert all(op.op == OP_CREATE for op in real["review"].approved)
    assert len(real["review"].approved) == len(boot["review"].approved)
