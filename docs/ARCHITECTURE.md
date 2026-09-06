# Architecture

## One sentence

A Grok Bot reads course pages with its browser and writes to Google Calendar
with its plugin; everything in between is deterministic Python on the Bot's
cloud computer, and that middle is what the fixture suite tests.

## The loop (gather, launch, review, merge)

```
 11 PM routine ─► syllabot status ─► course list
        │
        ├─► one "Read course" job per course (sequential, or reader Bots in parallel)
        │      saved HTML ──► syllabot extract html ──► Reading JSON
        │      Canvas API ──► syllabot extract canvas ─► Reading JSON
        │      iCal feed  ──► syllabot extract ical ───► Reading JSON
        │      email      ──► syllabot extract email ──► Reading JSON (partial)
        │      page read by the model ─────────────────► Reading JSON (schema)
        │
        ├─► syllabot plan --readings <night>/
        │      resolve   items -> events (dates, confidence, dedup, supersedes)
        │      diff      belief vs events (added / moved / reworded / pending / removed)
        │      guard     failed or empty read -> nothing; removal needs 2 reads on 2 days
        │      plan      ops with idempotency keys + provenance
        │      review    gate: blocked vs approved, with reasons
        │      write     runs/<id>/{readings,diff,plan,review,summary}
        │
        ├─► Bot applies approved ops via Google Calendar plugin
        │      after each call: syllabot record <run> --key --op --event-id --status
        │
        ├─► syllabot commit <run>     belief + missing + ledger advance
        │
        └─► one message to the owner (the summary), optional graph episodes
```

## Why code in the middle

The three things that ruin this kind of bot are all in the middle: a noisy diff
(timestamps and session ids look like changes), a destructive write on a bad
read (an empty page becomes "everything was deleted"), and duplicates on retry.
None of them are judgment calls, so none of them should be made by a model on a
live page at 11 PM. Each is a rule with a test:

| Failure | Rule | Where | Test |
|---|---|---|---|
| Noise | diff normalized items, never raw HTML; page chrome skipped | `normalize.py`, `extract/html.py` | T1 control course |
| Bad read deletes | `status != ok` or zero items with prior belief → course unreadable, belief untouched | `diff.py` | T3 |
| Flicker deletes | removal only after absence on two successful reads on different days | `diff.py` (`missing.json`) | T3 |
| Guessing | ambiguous date → needs-review, never on the calendar | `dates.py`, `review.py` | T4 |
| Duplicates | ledger key → event id; create becomes update if key known; writes recorded before commit; uncommitted runs recovered | `calendar_plan.py`, `pipeline.py` | T2 |
| Wrong hour | course timezone, offsets preserved through DST | `dates.py` | T5 |
| Mass deletion | more than 2 deletes and ≥ half a course in one run → blocked for manual confirm | `review.py` | unit |

## Belief, not snapshot

`belief/<course>.json` is what we currently believe each course's dated items
are. It advances only on `commit`, and only for keys whose writes succeeded. A
pending removal stays in the belief until confirmed, so the next night can
still see the absence. An item whose date text became unparseable stays too,
flagged for review, because "I can no longer read the date" is not "the item is
gone".

## Multiple sources for one course

`merge_readings` combines every reading of a course for one night:

- A successful **full** reading (page, API, feed) absorbs items from every other
  successful reading, including partial ones (email).
- If no full reading succeeded, partial readings run on their own with partial
  semantics: they can move or add, they cannot remove, and the failed source is
  reported as `source_failed` (does not block ops) rather than `unreadable`
  (blocks everything for the course).
- Same item, two dates: if one source states a change whose *old* date equals
  the other source's date ("moved from Oct 14 to Oct 16" vs a page still
  showing Oct 14), the change wins and the provenance records that the page is
  stale. Otherwise the item goes to review as "sources disagree".

## Crash safety

`plan` and `commit` are separate on purpose. Between them the Bot talks to a
plugin that can fail halfway. Every successful plugin call is recorded
immediately in `runs/<id>/results.partial.json`; the next `plan` finds any
uncommitted run with recorded writes and commits it first, so the ledger knows
those event ids before anything new is planned. A run with no recorded writes
is left alone: nothing was written, its changes are simply proposed again.

## What travels in the template

Identity, description, skills, routines, memories. Not: logins, files on the
computer, MCP servers, history. So the Setup playbook skill clones this repo
onto the fresh computer (`git clone` + `python3 -m syllabot.cli`; no pip
needed), runs `selftest`, and only then asks about courses and logins. The
installer's own logins live on their own computer; nothing about the author's
courses is in the template.

## Coverage beyond one LMS

One loop, one config. Extractors are the only code that knows a platform:
Brightspace via saved pages or its iCal feed, Canvas via REST (per-user token,
no scraping), any LMS via iCal, anything else via the Bot reading the page and
writing Reading JSON. The diff, guard, plan and review never branch on platform
(T6 mixes Brightspace fixtures and a Canvas sandbox in one run).
