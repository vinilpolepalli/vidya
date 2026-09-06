# Real fixtures (T0)

This folder is for **your** captures. `fixtures/real/` is git-ignored; nothing
in it should ever reach the template or the repo.

The synthetic set the tests use lives in `vidya/fixtures/`.

## Capture procedure (about twenty minutes)

1. Sign in to your LMS in a normal browser. For each of your courses, save the
   page(s) that hold dated items (syllabus/schedule, assignments, announcements)
   as "Webpage, HTML only" into `fixtures/real/day0/<course-id>.html`
   (one file per course; if you save several pages per course, name them
   `<course-id>-syllabus.html`, `<course-id>-assignments.html`, … and list the
   course once in `courses.json`).
2. `cp -r fixtures/real/day0 fixtures/real/day1`.
3. Hand-edit exactly five planted changes in `day1`, writing each one down:
   one due date moved, one assignment added, one assignment removed, one title
   reworded, one file replaced with an empty file.
4. Write `fixtures/real/courses.json`:
   ```json
   [{"id": "data-structures", "name": "CS 201", "url": "https://<lms>/d2l/home/12345", "timezone": "America/New_York"}]
   ```
5. Write `fixtures/real/expected.json` in the same shape as
   `vidya/fixtures/expected.json` (`changes`, `pending_removals`,
   `unreadable`, and `read_at` for both days).
6. Run:
   ```bash
   vidya selftest --fixtures fixtures/real
   ```
   T1 must list exactly your five changes. Extra entries are noise the
   extractor let through (fix `extract/html.py` skip rules or fall back to the
   bot writing Reading JSON); missing entries are bugs.

If the heuristic extractor cannot find items on your real pages, run
`vidya extract html <file> --course <id>` and inspect the output; the bot's
"Read course" skill has the same fallback (read the page, write the JSON).
