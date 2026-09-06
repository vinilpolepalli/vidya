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

## Claims to avoid unless you have the frame

- "24/7" or "always" — say "every night at 11 PM".
- "Works with any LMS" — say "built to generalize; tested on <what you tested>".
- "Never wrong" about dates — say "never guesses; ambiguous dates go to review".
- Anything about location, attendance, or auto-applying. Cut from the plan for a reason.

## Sign-off

- [ ] Every ☐ above is ☑ or the sentence was cut/softened
- [ ] Template link opens in a private window
- [ ] Repo link opens in a private window
- [ ] Video is a native upload with captions
- [ ] `#GrokBotForStudents` present
- [ ] Submitted at tinyurl.com/grokbot-student before 11:59 PM Pacific (treat as 2:59 AM ET; do not spend the PST/PDT hour)
