# T8. Claim audit

Go line by line through the description and the post. For each claim, point at
the frame in the video or the test that proves it. Any claim with neither gets
cut or softened. Do this last, immediately before publishing.

Legend: **frame** = a segment of the video; **test** = a passing test in this
repo; **live** = something you did on the real bot and can show if asked.

| # | Claim (as written in the post/description) | Evidence type | Where | Status |
|---|---|---|---|---|
| 1 | Reads course pages every night on its own cloud computer at 11 PM | frame | Segment 1: the overnight summary message that arrived while you slept; routine visible in the app | ☐ |
| 2 | Compares against last night and writes confirmed changes to Google Calendar | frame + test | Segment 2: moved deadline on the calendar; `tests/test_t1_known_answer_diff.py` | ☐ |
| 3 | Classes in peacock, deadlines in tomato | frame + test | Segment 2; `calendar_plan.py` color ids 7/11, `test_t5_timezone.py::test_calendar_ops_carry_timezone…` | ☐ |
| 4 | Source link in every event | frame + test | Segment 2 (open one event's description); `calendar_plan.description_for` includes `Source:` and `vidya-key:` | ☐ |
| 5 | Sends one summary including what it refused to guess | frame | Segment 1 (summary shows "Needs review" section) | ☐ |
| 6 | Merges professor emails that move a date (Gmail, read-only) | frame + test | Gmail segment if recorded; `tests/test_ical_and_email.py::test_email_change_supersedes_stale_page` | ☐ soften to "built to merge…" if no Gmail frame |
| 7 | A failed or empty page read never deletes anything | test | `test_t3_destructive_write_guard.py::test_empty_page_changes_nothing`, `selftest` T3 | ☐ |
| 8 | Deletion needs the item gone on two successful reads on different days | test | `test_t3…::test_error_read_does_not_count_toward_removal`, `selftest` T3 | ☐ |
| 9 | "TBD", "week of", "next Friday" go to needs-review, never the calendar | test | `test_t4_dates.py` adversarial set; `review.py` blocks `needs_review` events | ☐ |
| 10 | Re-running a night creates nothing twice, even after a crash mid-write | test | `test_t2_idempotency.py::test_crash_between_apply_and_commit_creates_nothing_twice` | ☐ |
| 11 | Stops and asks on MFA / login instead of logging in | frame or live | Segment showing the "please take over the computer" message, or the skill text in the template | ☐ soften to template text if no frame |
| 12 | Six course pages, two nights, five planted changes | test | `vidya/fixtures/expected.json`, `selftest` T1 line "5 planted changes detected, 0 noise" | ☐ |
| 13 | Known-answer diff, idempotency, destructive-write guard, adversarial dates, timezone | test | `selftest` output frame (optional) + `tests/` | ☐ |
| 14 | Canvas sandbox through the same loop with zero code changes | test (+ frame if recorded) | `tests/test_t6_multi_lms.py`; the loop has no platform branch. **Wording rule:** "tested on Brightspace and Canvas" only if you also ran it against a real Canvas sandbox; otherwise "built to generalize; Canvas path covered by the fixture suite" | ☐ |
| 15 | `selftest` prints ALL PASS in a second on a clean machine | frame or live | Run it during T7 on the fresh bot; record if convenient | ☐ |
| 16 | Graphiti for "how many times has this professor moved a deadline" | frame | Segment 5: the temporal query showing Oct 14 then Oct 16. **If not wired:** use the softened sentence from POST_DRAFT.md | ☐ |
| 17 | Template is public, includes a setup playbook, installs and self-tests before touching the calendar | live | T7 timing; `template/skills/setup-playbook.md` steps 1–2 | ☐ |
| 18 | Works on Brightspace | frame | Segments 1–2 are Brightspace | ☐ |
| 19 | "Group chat of course bots reporting back" (only if you say it) | frame | Segment 3, or cut the claim and describe sequential reads | ☐ |
| 20 | Standard-library Python engine | test | `pyproject.toml` has `dependencies = []`; `selftest` runs without pip | ☐ |
| 21 | Nightly check-in: asks me first, one email per contact after the grace period, one all-clear when I reply | test (+ frame if recorded) | `tests/test_safety.py::test_owner_is_reminded_first_and_only_once`, `::test_missed_checkin_alerts_each_contact_once`, `::test_late_checkin_after_alert_sends_one_all_clear`. Frame: the reminder in chat, then the email in a parent's inbox, then the all-clear. **If no frame:** "built in and tested; I have not run a real missed night yet" | ☐ |
| 22 | Off by default, only to people I named who agreed | test | `::test_off_by_default_sends_nothing`; `add-contact` refuses without `--consented` (`cli.py`) | ☐ |
| 23 | "It can't see my phone; a check-in, not tracking" | test | `::test_location_only_when_opted_in`: no place in any alert unless opted in, and then only what the owner supplied | ☐ |
| 24 | Works with Brightspace, Canvas, Blackboard, anything with a course page | test + wording rule | Same rule as row 14. Brightspace fixtures + Canvas fixture are tested; Blackboard/Moodle/Classroom/Schoology are the zero-code "Read course" path. Say "tested on <what you ran>; built to work with any course page" | ☐ |
| 25 | "A receipt inside every event" / "ask why and it shows every time it moved" | test + frame | `tests/test_why_and_track.py::test_why_explains_a_move_with_both_dates_and_the_source`; frame: `vidya why "Midterm 1"` output, and the event description in Google Calendar | ☐ |
| 26 | Watches registrar / aid / housing / club pages, not just courses | test (kind is just a label) + frame | `add-source --kind`; the engine does not branch on kind. Frame: `vidya status` showing a `[registrar]` source. **Only claim what you actually added.** | ☐ |
| 27 | Alert can say where I last was, via Google Maps sharing | test + live | `test_shared_location_appears_only_when_opted_in_and_is_not_a_checkin`. Live: do one Maps read yourself before claiming; otherwise say "can include a last-known place you share" | ☐ |
| 28 | Applications "submitted only as a batch I approve", "nothing happens twice" | test + frame | `test_track_dedupes`; the Opportunity scout skill stops at Submit. Frame: the batch summary and one confirmation screenshot. **If you have not run a real application yet, say "built to" and cut the number.** | ☐ |
| 29 | Resume: "every line traces to my master resume" | live | Open one `facts.md` next to the tailored PDF in the video, or soften to "designed so that" | ☐ |
| 30 | Lecture notes into Notion, assignment coach, club fit report, coffee chats, cold outreach, calendar concierge | frame or cut | Each needs one frame (a Notion page, a coaching note, a fit report, a drafted note, an operation list). Cut any you did not record; the post already carries the deadline story | ☐ |
| 31 | "79 tests" | test | `python3 -m pytest -q` output frame or the CI badge; update the number if it changes | ☐ |
| 33 | Fun: "concerts by artists I actually listen to", "a ticket walked to the Pay button" | frame or cut | Frame: the Thursday shortlist with a "because you listen to" line, and one cart screenshot stopped at payment. Say "reads my Spotify" only if the Live Events page was actually used; never claim it bought anything you did not approve | ☐ |
| 34 | Tutor: "teaches the semester from the syllabus", "every claim labelled", "graded honestly" | test + frame | `tests/test_teach.py` (map around believed exams, review before each, weak list). Frame: the printed semester map, one Core-concept step with both labels visible, one graded answer. Never claim learning gains; ClassDay's own page says the Kestin RCT numbers are not theirs, and they are not ours either | ☐ |
| 32 | "Works for high school" | wording | The engine is page-agnostic and the playbook names Schoology/Classroom/PowerSchool/counseling pages. Say "built for" unless a high school student ran it | ☐ |

## Claims to avoid unless you have the frame

- "24/7" or "always" — say "every night at 11 PM".
- "Works with any LMS" — say "built to generalize; tested on <what you tested>".
- "Never wrong" about dates — say "never guesses; ambiguous dates go to review".
- Location tracking, attendance, or auto-applying. The Bot has no sensor; the safety check-in is the honest version (the owner checks in, or contacts are told they did not). Never write "knows where I am".
- "Texts my parents" — say "emails" unless you verified the carrier gateway delivered as a text on your parent's phone.
- "Auto-applies to jobs" — say "prepares applications I approve as a batch". Unattended submission is not what it does and would not be a feature.
- "Builds projects for my resume" — say "helps me build" / "pair-programs". The README labels AI-assisted work and so should you.
- "Buys tickets for me" — say "walks a ticket to the Pay button; I say pay".
- "Knows where I am" — never. "Can tell my mom where I last was, if I share my location and only when I've gone quiet" is the true sentence.

## Sign-off

- [ ] Every ☐ above is ☑ or the sentence was cut/softened
- [ ] Template link opens in a private window
- [ ] Repo link opens in a private window
- [ ] Video is a native upload with captions
- [ ] `#GrokBotForStudents` present
- [ ] Submitted at tinyurl.com/grokbot-student before 11:59 PM Pacific (treat as 2:59 AM ET; do not spend the PST/PDT hour)
