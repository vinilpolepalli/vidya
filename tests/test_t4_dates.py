"""T4. The adversarial set real syllabi actually contain."""

import pytest

from vidya.dates import parse_date_text, resolve_year
from vidya.selftest import ADVERSARIAL, t4_date_parsing

REF = "2026-09-05T23:00:00-04:00"


def test_selftest_t4(fixtures, tmp_path):
    chk = t4_date_parsing(fixtures, tmp_path)
    assert chk.passed, chk.failures


@pytest.mark.parametrize("text,posted,pred,why", ADVERSARIAL, ids=[a[0] for a in ADVERSARIAL])
def test_adversarial(text, posted, pred, why):
    r = parse_date_text(text, REF, posted_at=posted)
    assert pred(r), f"{text!r}: expected {why}; got {r}"


def test_next_friday_resolves_against_post_date_not_today():
    posted = "2026-10-05"  # a Monday
    r = parse_date_text("Next Friday", REF, posted_at=posted)
    assert r.start == "2026-10-09"
    assert r.needs_review
    r_today = parse_date_text("Next Friday", REF)
    assert r_today.start == "2026-09-11"  # relative to the read date when there is no post date
    assert r.start != r_today.start


def test_inline_change_forms_yield_one_event_on_the_new_date():
    for text in ["Oct 14 changed to Oct 16", "moved from Oct 14 to Oct 16", "Oct 16 instead of Oct 14",
                 "was Oct 14, now Oct 16", "Oct 14 -> Oct 16", "rescheduled to Oct 16 (was Oct 14)"]:
        r = parse_date_text(text, REF)
        assert r.start.startswith("2026-10-16"), (text, r)
        assert r.end.startswith("2026-10-16"), (text, r)
        assert not r.needs_review, (text, r)


def test_weekday_conflict_goes_to_review():
    r = parse_date_text("Friday Oct 15", REF)  # Oct 15, 2026 is a Thursday
    assert r.needs_review and "does not match" in r.reason
    assert r.start == "2026-10-15"  # candidate kept for the reviewer


def test_year_inference_window():
    ref = __import__("datetime").date(2026, 9, 5)
    assert resolve_year(12, 18, ref)[0].isoformat() == "2026-12-18"
    assert resolve_year(1, 20, ref)[0].isoformat() == "2027-01-20"
    assert resolve_year(8, 30, ref)[0].isoformat() == "2026-08-30"
    dec_ref = __import__("datetime").date(2026, 12, 10)
    assert resolve_year(1, 20, dec_ref)[0].isoformat() == "2027-01-20"


def test_explicit_years_and_ranges():
    assert parse_date_text("10/16/26 5pm", REF).start == "2026-10-16T17:00:00-04:00"
    assert parse_date_text("October 16th, 2026", REF).start == "2026-10-16"
    r = parse_date_text("Oct 30 - Nov 2", REF)
    assert (r.start, r.end, r.all_day) == ("2026-10-30", "2026-11-02", True)
    r = parse_date_text("10/20-10/22", REF)
    assert (r.start, r.end) == ("2026-10-20", "2026-10-22")


def test_midnight_and_noon():
    assert parse_date_text("Oct 16 midnight", REF).start == "2026-10-16T23:59:00-04:00"
    assert parse_date_text("Oct 16 at noon", REF).start == "2026-10-16T12:00:00-04:00"


def test_no_date_and_vague_periods_go_to_review():
    for text in ["", "end of semester", "finals week", "see syllabus", "every Friday"]:
        r = parse_date_text(text, REF)
        assert r.needs_review and r.start is None, text
