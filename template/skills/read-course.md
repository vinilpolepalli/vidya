# Skill: Read course

The narrow job. One course, one Reading JSON file, nothing else. This is what a
fan-out reader runs; a cheap model tier is fine for it because the hard parts
(dates, diff, guard) happen in the engine afterwards.

## When to use
Called by the nightly check for each course, or by the owner ("re-read Physics").

## Inputs
- Course id, name and URL from `~/syllabot-state/config.json`.
- Output folder, e.g. `~/syllabot-state/readings/<YYYY-MM-DD>/`.
- `SYLLABOT_STATE=~/syllabot-state`; run commands from `~/syllabot`.

## Sequence
1. Note the read time as ISO 8601 with offset, e.g. `2026-09-06T23:02:11-04:00`.
2. Get the content, in this order of preference:
   - **Feed or API** if configured for the course: `syllabot extract ical "<url>" --course <id> --read-at <ts> --out <folder>/<id>.json` or `syllabot extract canvas ... --out <folder>/<id>.json`. Done; go to step 5.
   - **Saved page**: open the course home in the browser. Visit the pages that hold dated items (syllabus/schedule, assignments, announcements). For each, save the page as HTML into `<folder>/<id>-<page>.html` (browser Save Page, "Webpage, HTML only"). Then `syllabot extract html <file> --course <id> --url "<page url>" --read-at <ts> --out <folder>/<id>-<page>.json` for each file. Several JSON files for one course are fine; the engine merges them.
   - **Read it yourself** if the page cannot be saved or the extractor finds nothing: read the page and write `<folder>/<id>.json` by hand in the Reading schema below. Copy titles and date text exactly as written; do not compute dates yourself.
3. If a login page, MFA prompt or CAPTCHA appears: write a Reading with `"status": "error"` and `"error": "login required"`, items empty. Do not attempt to sign in. Tell the supervisor.
4. If the page loads but has no course content (blank, maintenance page): `"status": "empty"`.
5. `syllabot validate <folder>/<id>*.json`. Fix schema problems; leave review items alone (they are the engine's job).

## Reading schema
```json
{
  "course_id": "<id>",
  "source_url": "<page url>",
  "read_at": "2026-09-06T23:02:11-04:00",
  "status": "ok",
  "timezone": "America/New_York",
  "items": [
    {"title": "Midterm 1", "kind": "exam", "date_text": "Oct 16, 11:00 AM", "url": "<item url or empty>", "section": "syllabus"},
    {"title": "Homework 2", "kind": "assignment", "date_text": "Due Oct 3 by 11:59 PM", "section": "assignments"},
    {"title": "Office hours", "kind": "announcement", "date_text": "Wednesdays 3-4 PM", "posted_at": "2026-09-03", "section": "announcements"}
  ]
}
```
`kind` is one of `assignment | exam | class | announcement | other`. `posted_at` is the date an announcement was posted (the engine needs it to resolve "next Friday"). `status` is `ok | empty | error`.

## Rules
- Titles verbatim. Date text verbatim. Never resolve a date yourself; never drop an item because its date looks odd (TBD is a valid `date_text`).
- Never write anything to the LMS. Read-only.
- Never sign in. Never bypass a CAPTCHA.
- Ignore page chrome: navigation, footers, "last visited", "posted 3 hours ago".

## Return
The path(s) of the Reading JSON file(s) and the item count, or the status and error if the read failed.
