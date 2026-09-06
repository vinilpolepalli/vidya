# Skill: Setup playbook

## When to use
First message on a fresh computer, or whenever `~/vidya-state/config.json` is missing. Also when the owner says "set up", "start over", or "add a course".

## Required inputs and access
- The owner's LMS name (Brightspace, Canvas, Google Classroom, Moodle, other) and calendar time zone (IANA name, e.g. `America/New_York`).
- Terminal on this computer with `git` and `python3` (3.10+).
- Browser on this computer for LMS sign-in (owner does the login; see step 4).
- Google Calendar plugin, connected by the owner when asked (step 7).

## Sequence
Do the steps in this order. The first successful course read (step 5) comes before anything optional. Report progress after each step in one line.

1. **Install the engine.** In the terminal:
   ```
   cd ~ && git clone https://github.com/vinilpolepalli/vidya vidya && cd ~/vidya
   python3 -m vidya.cli --version
   ```
   No pip install is needed; the engine is standard-library Python. Use `python3 -m vidya.cli` everywhere below (call it `vidya`). If you prefer the short command, `python3 -m pip install -e ~/vidya` also works.

2. **Prove the engine.** `cd ~/vidya && python3 -m vidya.cli selftest`. Expect five `[PASS]` lines and `ALL PASS`. If anything fails, stop and show the owner the output. Do not continue with a failing engine.

3. **Create state.** `export VIDYA_STATE=~/vidya-state` and `vidya init --timezone <tz>`. Remember: every later command needs `VIDYA_STATE` set (or pass `--state ~/vidya-state`).

4. **Course list.** Ask the owner for the courses, or open the LMS home in the browser. If a login page appears: stop, mark nothing, tell the owner "Please take over the computer and sign in to <platform>; I'll continue when you hand control back." Never type credentials, never attempt MFA, never retry a CAPTCHA. Once in, read the course list and confirm it with the owner before saving. For each course:
   `vidya add-course <id> --name "<name>" --url "<course home URL>" --platform <brightspace|canvas|classroom|moodle|other>`
   Use short ids (`data-structures`), never the LMS numeric id alone.
   - **Canvas**: ask whether the owner wants the API path. If yes, they create a token at Account → Settings → New Access Token and paste it into the terminal as `export CANVAS_TOKEN=...` themselves (do not ask them to paste it in chat). Readings then come from `vidya extract canvas --base-url https://<school>.instructure.com --canvas-course <numeric id> --course <id>`.
   - **Any LMS with an iCal feed** (Brightspace: Calendar → Subscribe; Canvas: Calendar → Calendar Feed): prefer the feed for dates. `vidya extract ical "<feed url>" --course <id>`. A tokenized feed needs no login and survives redesigns.

5. **First read.** Run the "Read course" skill for each course (sequentially is fine the first time). Then:
   ```
   vidya plan --readings ~/vidya-state/readings/first/ --fake-apply
   vidya status
   ```
   Show the owner the summary: every item found, and the needs-review list. Ask them to correct titles or dates that are wrong before continuing. This is the baseline.

6. **Dry run (optional but offered).** The `--fake-apply` above already wrote to a fake calendar under the state dir. Show `~/vidya-state/fake_calendar.json` (count and three examples) so the owner sees exactly what would be created. If they want changes, fix and rerun step 5.

7. **Real calendar.** Ask the owner to connect the Google Calendar plugin (Settings → Plugins) and name the target calendar. Then reset the fake baseline so the real one can be written: `rm ~/vidya-state/fake_calendar.json ~/vidya-state/ledger.json && rm -rf ~/vidya-state/belief/*`, run `vidya plan --readings ~/vidya-state/readings/first/` **without** `--fake-apply`, and apply the approved operations through the plugin exactly as the "Nightly syllabus check" skill describes (create → record → commit). Colors: peacock (7) for classes, tomato (11) for deadlines; skip color if the plugin cannot set it.

8. **Routines.** Create the "Nightly syllabus check" routine (11:00 PM, owner's time zone) and the "Weekly digest" routine (Sunday 6:00 PM). Run a **Test run** of the nightly routine now while the owner is watching. It should report zero changes.

9. **Optional: email.** If the owner connects Gmail (read-only), the nightly skill will look for instructor emails that move a date. Explain: I will never send mail.

10. **Optional: temporal graph.** Graphiti is not required. If the owner runs their own Graphiti MCP server (their own LLM key), add it as a plugin and the nightly skill will post episodes. See `docs/GRAPHITI.md` in the repo. Do not point at anyone else's server.

## How to validate
- `selftest` said ALL PASS.
- `vidya status` lists every course with a believed item count > 0 (or the owner has confirmed a course genuinely has no dated items).
- The owner's calendar shows the baseline events with source links in descriptions.
- The Test run of the nightly routine reported zero changes.

## What to return
One message: courses configured, items believed per course, review items, where the events went, when the routine runs, and what is optional and not yet connected.

## What requires approval
- Signing in anywhere (owner does it via takeover).
- Writing to the real calendar for the first time (owner confirms after the dry run).
- Deleting anything (never during setup).
