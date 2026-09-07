# Written description (requirement 1)

*What the Bot does and the tools it uses. The block under **Challenge paste** is the one to put in the form. Every claim is a test in this repo or a frame you still need to record; see `CLAIM_AUDIT.md`.*

Live bot: https://x.ai/bot/EKch7dX7qsm7wRuU4tTI2
Repo: https://github.com/vinilpolepalli/vidya

---

## Challenge paste

Vidya is a Grok Bot that keeps every deadline in a student's life honest.

Every night, on its own cloud computer, it re-reads the pages you asked it to watch — courses on Canvas, Brightspace, Blackboard, Moodle, Schoology or Google Classroom, plus registrar, aid, housing, clubs — and diffs them against last night's belief. Confirmed changes go onto Google Calendar (classes peacock, deadlines tomato), each with a receipt: the source link, the exact words on the page, every assumption. Ask "why is Midterm 1 on the 16th?" and you get the receipt and every time that date moved.

It never guesses ("TBD", "week of Oct 12" go to review, never the calendar), never deletes on a failed read (a removal needs the item gone on two successful reads on two different days), and never duplicates, even after a crash mid-write. Those decisions are standard-library Python with 79 tests, not a prompt. You get one honest message a night: what moved, from where, and what it refused to touch.

The shape is the point. The supervisor Bot talks to you and holds the plugins. One cheap reader subagent per page writes a JSON reading — titles and date text verbatim. A deterministic engine (extract → normalize → diff → review gate → idempotent plan → two-phase record/commit) decides what changed, what's ambiguous, and what may be written. The Bot applies exactly those operations.

Same rule everywhere else: it prepares, you decide. A syllabus becomes numbered classes on your real session days, taught one concept at a time, every claim labelled course-material or broader context, weak spots back before the exam. Lecture notes into Notion. Assignment plans, never submissions. SimplifyJobs internships filled to Submit and sent only as a batch you approve. Resumes that invent nothing. Projects you drive. Club fit reports. Outreach you send. Calendar edits in plain English. Thursday: home games, Spotify-ranked concerts, tickets walked to Pay and stopped. A ledger on disk means nothing happens twice.

Optional, off by default: a nightly "you good?" Go quiet past a grace period and consented contacts get one email from your mailbox; answer late and they get one all-clear. Maps sharing can put a last-known place and its age in that alert only. It cannot see your phone. A check-in, not tracking.

**Tools.** Grok Bot cloud computer (browser, filesystem, terminal), routines, subagents; Google Calendar (write); Gmail (read instructor email; send only approved safety or outreach from your mailbox); Notion; LMS pages + Canvas REST + iCal; SimplifyJobs; GitHub; Spotify Live Events; school ticket sites (stop at Pay); LinkedIn at human pace, no automation; optional Google Maps sharing (read once, inside a missed-check-in alert); optional Graphiti (Zep) for "how many times has this professor moved a deadline"; stdlib Python engine `vidya` — `vidya selftest` prints ALL PASS in about a second.

Public template — one message and it builds itself, college or high school.

---

## If the form is tight (~120 words)

Vidya watches the pages that run a student's life and keeps the calendar honest. Every night, on its own cloud computer, it re-reads courses, registrar, aid and club pages, diffs them against last night's belief, and writes only confirmed changes to Google Calendar — each event with a receipt. It never guesses, never deletes on a failed read, never duplicates; those rules are standard-library Python with 79 tests, not a prompt. Same contract everywhere else: it prepares, you decide — syllabus-to-semester tutoring, Notion notes, assignment coaching, internship applications to the Submit button, resumes that invent nothing, clubs, outreach, and tickets stopped at Pay. Optional check-in emails consented contacts if you go quiet. Tools: Grok Bot computer, routines, subagents; Calendar, Gmail, Notion; LMS + Canvas REST + iCal; SimplifyJobs; GitHub; Spotify; Maps sharing; `vidya` + `selftest`.

---

## Long catalog (do not paste unless they ask)

Your professor moves the midterm at 11 PM. **Vidya** notices at 11:02, and your calendar is fixed before you wake up.

Every night, on its own cloud computer, Vidya sends one reader per page you asked it to watch: your courses on Canvas, Brightspace, Blackboard, Moodle, Schoology or Google Classroom, plus the registrar's calendar, financial aid, housing, and any club with a deadline. It compares what it finds with what it believed last night and writes only the confirmed changes to Google Calendar: classes in peacock, deadlines in tomato, and a receipt inside every event with the source link, the exact words on the page, and every assumption it had to make. Ask "why is Midterm 1 on the 16th?" and it shows the receipt and every time the date moved.

It never guesses. "TBD", "week of Oct 12", "next Friday" go to a review list you clear with one reply. A page that fails to load never deletes anything; a removal needs the item gone on two successful reads on different days. Re-running a night never creates anything twice, even after a crash mid-write. The decisions that could wipe a semester are Python with 79 tests, not a prompt. You get one honest message a night: what moved, from where, and what it refused to touch.

**Safety check-in (optional, off by default).** A nightly "you good?" in your own chat. A quick reply logs it. Go quiet past your grace period and the people you named, who agreed, get one email from your own mailbox saying the check-in was missed and that this usually means a phone on silent; answer late and they get one all-clear. If you share your location with it through Google Maps, the alert can say where you last were and how long ago, and that is the only time it ever looks. Who may be messaged, when and how often is code with tests; the Bot sends exactly what `vidya safety plan` approves. It cannot see your phone. A check-in, not tracking.

**The rest of student life, same rule: it prepares, you decide.**
- **Course tutor**: give it the syllabus and it teaches the semester. The engine lays numbered classes on your real session days around the exams it already believes, with a review before each; the model teaches each class one concept at a time (intro, core concept, examples, practice, summary) with every claim labelled "from your course material" or "broader context", grades your answers like they count (what you had right, the main gap, one next step), and brings weak concepts back before the exam. Controls at every step: I get it, another example, go deeper, I'm confused.
- **Lecture notes** into your Notion from slides, transcripts and readings, with sources listed, connections to the next exam, and five likely exam questions marked as guesses.
- **Assignment coach**: the rubric decoded, a plan backwards from the due date, the traps, office-hours questions. It never writes the submission.
- **Opportunity scout**: a nightly diff of the SimplifyJobs Summer 2027 internship and new-grad lists against your profile; applications tailored, filled and screenshotted at the Submit button; you approve a batch, it submits, and a ledger makes double-applying impossible. High school owners get summer programs and first internships instead.
- **Resume tailor**: one page per posting, every bullet traced to a line in your master resume in a facts file; a weekly gap report of what postings want that you don't have.
- **Project builder**: closes a gap with a project you drive and can explain in an interview; scaffolding and tests labelled AI-assisted in the commits and the README.
- **Club scout**: the directory, a fit / stretch / not-now report with a reason against each, deadlines watched like any course, applications drafted.
- **Coffee chats and cold outreach**: shortlists by what people actually work on, notes under 90 words that you send; after a yes, slots, a Meet link, the event and prep questions. LinkedIn at human pace, never automated, nobody contacted twice.
- **Calendar concierge**: "block Tuesday mornings for the project", "put a study session before every exam"; it shows the exact operations and applies them on your yes. It never touches the events the nightly check manages.
- **Fun scout**: every Thursday, the good part of the week: your school's home games with student-ticket status, concerts near you ranked by what you actually play on Spotify, campus events, and the parties on the pages you named. You pick, it goes on your calendar; say "ticket" and it walks the cheapest matching seat to the Pay button, shows the total against your monthly budget, and stops until you say pay. That night, the safety check-in knows you're out.

**How it works.** LLM at the edges, code in the middle. The supervisor Bot talks to you and holds the plugins; one cheap reader subagent per source reads a page and writes a small JSON reading; a standard-library Python engine does everything that has to be right (dates, diff, guard, review gate, idempotent plan, receipts, safety rules, the action ledger); the supervisor applies exactly what the engine approved and records each write. See `docs/SYSTEM_MAP.md`.

**Tools.** Grok Bot's persistent cloud computer (browser, filesystem, terminal), routines, and subagents; the Google Calendar plugin (write) and Gmail (read for professor emails, send only for approved messages); Notion; Canvas's REST API and iCal feeds as no-login sources; the SimplifyJobs listings; GitHub for projects; a stdlib Python engine with a fixture suite; Graphiti (Zep) for "how many times has this professor moved a deadline".

**Tested, not vibes.** Six synthetic course pages across two nights with five planted changes; a known-answer diff, idempotency (including a crash between apply and commit), the destructive-write guard, a ten-string adversarial date set, timezone rules, a Canvas run through the same loop with no code change, the safety rules (reminder first, one alert per contact, one all-clear, caps, opt-in location, plans mentioned in the reminder), receipts, and the dedupe ledger. `vidya selftest` prints ALL PASS on a clean computer in about a second.

**Template.** One message and the Bot builds itself: it clones the engine to its own computer, runs the tests, saves its eighteen skills, and interviews you for the rest, asking one question at a time and stopping whenever you need to sign in. Works for college and high school; nothing in it is specific to a school.
