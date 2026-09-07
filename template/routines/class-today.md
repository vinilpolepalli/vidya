# Routine: Class today (optional, per course)

Create after "Course tutor" has mapped a course. Ask the Bot:

> On <session days> at <time> in <owner time zone>, run the "Course tutor" skill for <course>: open the semester map, post the Intro step of today's class in this conversation, and wait for me. If there is no class today, post nothing. Two days before any exam for this course, post the weak-concept list and offer a review class instead. Never write to the calendar or Notion during the routine; that happens only in the conversation after I reply.

- **Owning Bot:** Vidya
- **Schedule:** the course's session days, owner's time zone (e.g. Mon/Wed 7:00 PM)
- **Input:** `~/vidya-state/teach/<course>/plan.json`, the material folder, `vidya teach weak <course>`, `vidya status` for exam dates
- **Expected result:** the Intro of today's class, or nothing; before an exam, the weak list and an offer
- **Approval boundary:** read-only during the routine; teaching and grading happen in the conversation
- **Missing source:** if the plan or material is missing, post "run Course tutor setup for <course>" once and stop

Test run once: expect the Intro of the next class, and no calendar or Notion change.
