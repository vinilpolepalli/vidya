# Skill: Needs-review triage

The needs-review bucket holds items the engine refused to guess: TBD dates,
"week of", relative weekdays, dates with no day, items two sources disagree on,
email mentions that could be one of several items. Nothing in the bucket is on
the calendar.

## When to use
When the owner asks ("what needs review?", "the museum visit is Oct 30"), or in
the morning after a nightly run that added review items.

## Sequence
1. `vidya status` lists the bucket: course, title, the text as written, the reason, and a candidate date when the engine had one.
2. Present it as a short list with one question per item, e.g. "Modern History — Museum visit — 'The museum visit date is TBD' — what date should I use, or skip?"
3. For each answer:
   - **Owner gives a date**: write a partial Reading in `~/vidya-state/readings/owner/<date>/<course>.json` with `"partial": true`, `"source_url": "owner:<today>"`, and one item whose `title` is the exact believed title and whose `date_text` is the owner's answer. Run `vidya plan --readings <that folder>`, apply approved ops as in the nightly skill, `commit`, then `vidya resolve-review "<key>" --note "owner: <answer>"` so it stops appearing while the page text is unchanged.
   - **Owner says skip**: `vidya resolve-review "<key>" --note "owner: skip"`.
   - **Owner corrects a title match** ("that email was about Midterm 2"): same as a date answer, using the title they named.
4. Confirm what was written and what was skipped.

## Rules
- The owner's word is a source like any other: it goes through `plan` and the review gate, never straight into the calendar.
- If the page later changes the text of a resolved item, it comes back to the bucket automatically. Say so when it happens.
- Never resolve an item by guessing. If the owner is unsure, leave it.
