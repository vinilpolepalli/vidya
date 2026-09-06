# Routine: Nightly syllabus check

Create this routine by asking the Bot (the six items the docs say to confirm are
all stated):

> Every day at 11:00 PM in <owner time zone>, run the "Nightly syllabus check" skill against the courses in `~/syllabot-state/config.json`. Read every course, run `syllabot plan`, apply only the approved calendar operations through the Google Calendar plugin, record each one, commit, and post the summary in this conversation. Never delete an event unless the plan marks the removal as confirmed. If a course cannot be read (login wall, empty page, silent reader), report it as unreadable and leave its events alone; do not sign in yourself. If the engine or state directory is missing, do not improvise: post "setup required" and stop.

- **Owning Bot:** Syllabus
- **Schedule:** daily 23:00, owner's time zone (the 11 PM time is arbitrary; pick what makes the overnight story land)
- **Input:** `~/syllabot-state/config.json` course list; the LMS pages, feeds or API; optional Gmail
- **Expected result:** one summary message with changes, pending removals, unreadable courses, review items, and applied operations
- **Approval boundary:** create/update events from approved operations only; deletes only for confirmed removals; nothing else is written anywhere
- **Missing source:** report the course as unreadable and continue with the others; never treat a failed read as an empty course

After creating: use **Test run** once while watching. Expect zero changes on a
freshly set-up Bot. Then enable.
