# vidya

The deterministic middle of a Grok Bot that watches your course pages every night, notices when a professor moves a deadline, and keeps your calendar honest.

**LLM at the edges, code in the middle.** The bot's model reads pages and applies calendar operations through its plugins. Everything in between is plain Python here: normalizing items, parsing dates, diffing against last night's belief, refusing destructive writes on failed reads, gating the plan, and keeping the calendar ledger idempotent. That is the part that could wipe a semester, so it is code with a fixture suite, not a prompt.

Built for the Grok Bot Student Build Challenge (`#GrokBotForStudents`). The Grok Bot template text that uses this engine lives in [`template/`](template/); the submission material in [`submission/`](submission/).

## What it does

```
        gather                  launch                    review                    merge
 ┌────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐   ┌─────────────────┐
 │ 11 PM routine  │ → │ one reader per course│ → │ vidya plan        │ → │ approved ops →  │
 │ reads course   │   │ saves page / writes  │   │ normalize · parse ·  │   │ Google Calendar │
 │ list + belief  │   │ Reading JSON         │   │ diff · guard · gate  │   │ vidya commit │
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

Every calendar event carries provenance (source URL, read time, the text as written, every assumption made, a confidence score) and a `vidya-key:` marker so it can be found again if the ledger is lost.

## Install

Standard library only. Python 3.10+.

```bash
git clone <this repo> vidya && cd vidya
python3 -m pip install -e .
vidya selftest
```

`selftest` runs the fixture suite (T1–T5) against six synthetic course pages across two nights with five planted changes. It should end with `ALL PASS` in about a second.

## Run a night by hand

```bash
export VIDYA_STATE=~/vidya-state
vidya init --timezone America/New_York
vidya add-course data-structures --name "CS 201 Data Structures" --url https://lms.example.edu/d2l/home/41001 --platform brightspace

# 1. produce one Reading JSON per course (saved page, Canvas API, iCal feed or email)
vidya extract html saved/data-structures.html --course data-structures --url https://lms.example.edu/d2l/home/41001 --out tonight/data-structures.json

# 2. diff against last night's belief, run the review gate, write the run
vidya plan --readings tonight/
#    prints the owner summary and the approved operations

# 3. apply each approved op through the calendar plugin, recording each write immediately
vidya record <run-id> --key "data-structures::midterm 1" --op update --event-id <calendar-event-id>

# 4. advance belief + ledger
vidya commit <run-id>
```

Dry run without a calendar: `vidya plan --readings tonight/ --fake-apply` applies to a JSON fake calendar under the state dir and commits.

`vidya status` shows believed items per course, pending removals, the needs-review bucket, and the ledger. `vidya digest` writes the weekly digest. `vidya graph <run>` exports a run as Graphiti episodes.

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
vidya/            engine (stdlib only)
  dates.py           date parsing, confidence, needs-review, timezone
  resolve.py         items -> events, cross-source dedup, change-statement precedence
  diff.py            belief vs reading; destructive-write guard; partial (email) semantics
  review.py          the gate every op passes before the bot may apply it
  calendar_plan.py   ops with idempotency keys and provenance
  pipeline.py        plan / record / commit, crash recovery, owner summary
  digest.py          weekly digest (due soon, what moved, volatility)
  graph.py           Graphiti episodes (add_memory shape, deterministic uuids)
  extract/           html, canvas (REST), ical, email -> Reading
  fixtures/          synthetic T0 set: six courses, two nights, five planted changes; canvas/ical/email samples
  selftest.py        T1-T5 without pytest
tests/               pytest suite: T1-T6, email/iCal merge rules, digest, graph
template/            the Grok Bot template as text: profile, six skills, two routines, first-run message, scrub checklist
submission/          written description, post draft, T8 claim audit, test log
docs/                ARCHITECTURE.md, GRAPHITI.md
fixtures/            where your real T0 captures go (git-ignored)
```

## For the challenge

- `template/README.md` explains how to assemble the Bot in the Grok Bot app from the text in `template/`; `template/skills/setup-playbook.md` is what a stranger's fresh Bot runs on its first message (T7).
- `submission/DESCRIPTION.md` is requirement 1; `submission/POST_DRAFT.md` the post; `submission/CLAIM_AUDIT.md` is T8; `submission/TEST_LOG.md` records what ran here and what is still yours (real T0 captures, T7, T8, the video).
- Replace `<REPO_URL>` in the skills and `<TEMPLATE_LINK>` in the post before publishing. Nothing in `template/` or `vidya/fixtures/` refers to a real school, course, or person.

## Tests

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest
```

## Capturing your own T0 fixtures

Save each course page as HTML into `fixtures/real/day0/<course-id>.html`, copy the folder to `day1`, hand-edit exactly the changes you want to plant, describe them in `expected.json` (same shape as `vidya/fixtures/expected.json`), add a `courses.json`, then `vidya selftest --fixtures fixtures/real`. `fixtures/real/` is git-ignored.
