# syllabot

The deterministic middle of a Grok Bot that watches your course pages every night, notices when a professor moves a deadline, and keeps your calendar honest.

**LLM at the edges, code in the middle.** The bot's model reads pages and applies calendar operations through its plugins. Everything in between is plain Python here: normalizing items, parsing dates, diffing against last night's belief, refusing destructive writes on failed reads, gating the plan, and keeping the calendar ledger idempotent. That is the part that could wipe a semester, so it is code with a fixture suite, not a prompt.

Built for the Grok Bot Student Build Challenge (`#GrokBotForStudents`). The Grok Bot template text that uses this engine lives in [`template/`](template/); the submission material in [`submission/`](submission/).

## What it does

```
        gather                  launch                    review                    merge
 ┌────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐   ┌─────────────────┐
 │ 11 PM routine  │ → │ one reader per course│ → │ syllabot plan        │ → │ approved ops →  │
 │ reads course   │   │ saves page / writes  │   │ normalize · parse ·  │   │ Google Calendar │
 │ list + belief  │   │ Reading JSON         │   │ diff · guard · gate  │   │ syllabot commit │
 └────────────────┘   └──────────────────────┘   └──────────────────────┘   └─────────────────┘
```

Invariants the engine enforces (each has a test):

| | Rule | Test |
|---|---|---|
| 1 | No calendar write without passing the review gate | `tests/test_t1…`, `review.py` |
| 2 | A failed or empty read never produces a deletion | T3 |
| 3 | A deletion needs the item absent on two successful reads on different days | T3 |
| 4 | Anything ambiguous goes to a needs-review bucket, never guessed onto the calendar | T4 |
| 5 | Re-running a night creates nothing twice, even after a crash mid-apply | T2 |
| 6 | 11:59 PM means 11:59 PM in the course timezone | T5 |

Every calendar event carries provenance (source URL, read time, the text as written, every assumption made, a confidence score) and a `syllabot-key:` marker so it can be found again if the ledger is lost.

## Install

Standard library only. Python 3.10+.

```bash
git clone <this repo> syllabot && cd syllabot
python3 -m pip install -e .
syllabot selftest
```

`selftest` runs the fixture suite (T1–T5) against six synthetic course pages across two nights with five planted changes. It should end with `ALL PASS` in about a second.

## Run a night by hand

```bash
export SYLLABOT_STATE=~/syllabot-state
syllabot init --timezone America/New_York
syllabot add-course data-structures --name "CS 201 Data Structures" --url https://lms.example.edu/d2l/home/41001 --platform brightspace

# 1. produce one Reading JSON per course (saved page, Canvas API, iCal feed or email)
syllabot extract html saved/data-structures.html --course data-structures --url https://lms.example.edu/d2l/home/41001 --out tonight/data-structures.json

# 2. diff against last night's belief, run the review gate, write the run
syllabot plan --readings tonight/
#    prints the owner summary and the approved operations

# 3. apply each approved op through the calendar plugin, recording each write immediately
syllabot record <run-id> --key "data-structures::midterm 1" --op update --event-id <calendar-event-id>

# 4. advance belief + ledger
syllabot commit <run-id>
```

Dry run without a calendar: `syllabot plan --readings tonight/ --fake-apply` applies to a JSON fake calendar under the state dir and commits.

`syllabot status` shows believed items per course, pending removals, the needs-review bucket, and the ledger. `syllabot digest` writes the weekly digest. `syllabot graph <run>` exports a run as Graphiti episodes.

## Reading JSON

Extractors produce it; the bot can also write it directly after reading a page itself.

```json
{
  "course_id": "data-structures",
  "source_url": "https://lms.example.edu/d2l/home/41001",
  "read_at": "2026-09-06T23:02:11-04:00",
  "status": "ok",
  "timezone": "America/New_York",
  "items": [
    {"title": "Midterm 1", "kind": "exam", "date_text": "Oct 16, 11:00 AM", "url": "", "section": "syllabus"},
    {"title": "Office hours", "kind": "announcement", "date_text": "Wednesdays 3-4 PM", "posted_at": "2026-09-03"}
  ]
}
```

`status` is `ok`, `empty` or `error`. Only `ok` counts as a successful read for the deletion rule.

## Layout

```
syllabot/            engine (stdlib only)
  dates.py           date parsing, confidence, needs-review, timezone
  resolve.py         items -> events, cross-source dedup
  diff.py            belief vs reading; destructive-write guard
  review.py          the gate every op passes before the bot may apply it
  calendar_plan.py   ops with idempotency keys and provenance
  pipeline.py        plan / record / commit, crash recovery
  extract/           html, canvas, ical, email -> Reading
  fixtures/          synthetic T0 set: six courses, two nights, five planted changes
  selftest.py        T1-T5 without pytest
tests/               pytest suite (same checks, more edge cases)
template/            Grok Bot template text: profile, skills, routines, setup playbook
submission/          description, post draft, claim audit, test log
docs/                architecture, Graphiti
```

## Tests

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest
```

## Capturing your own T0 fixtures

Save each course page as HTML into `fixtures/real/day0/<course-id>.html`, copy the folder to `day1`, hand-edit exactly the changes you want to plant, describe them in `expected.json` (same shape as `syllabot/fixtures/expected.json`), add a `courses.json`, then `syllabot selftest --fixtures fixtures/real`. `fixtures/real/` is git-ignored.
