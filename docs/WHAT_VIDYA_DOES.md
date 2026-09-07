# Vidya — what it does

Vidya (Sanskrit for knowledge) is a Grok Bot that runs a student's life the way a careful registrar would: it watches the pages that have dates on them, keeps the calendar honest, and then helps with everything else — classes, notes, assignments, internships, clubs, people, tickets — under one rule.

**It prepares. You decide.**

Nothing is guessed onto a calendar, submitted to a form, sent to a person, or paid for unless you said so in the conversation. The Bot interviews you one question at a time. You never pre-fill a config file. College and high school both work; the sources change, the contract does not.

Live bot: https://x.ai/bot/EKch7dX7qsm7wRuU4tTI2
Engine: https://github.com/vinilpolepalli/vidya

---

## 1. Deadline honesty (the core)

Your professor moves the midterm at 11 PM. Vidya notices at 11:02, and the calendar is fixed before you wake up.

Every night at 11:00 in your time zone, on its own cloud computer, it sends one reader to every page you asked it to watch:

- **Courses** on Canvas, Brightspace, Blackboard, Moodle, Schoology, Google Classroom, or any site with a syllabus / assignments / announcements page
- **Beyond courses:** registrar / academic calendar, financial aid, housing, clubs and programs with deadlines
- **High school:** Classroom / Schoology / PowerSchool, counseling-office deadlines (SAT/ACT, college applications, FAFSA), summer programs

It compares tonight's pages to last night's *belief* and writes **only confirmed changes** to Google Calendar. Classes are peacock. Deadlines and exams are tomato.

Every managed event carries a **receipt**: the source link, the exact words on the page, and every assumption. Ask "why is Midterm 1 on the 16th?" (`vidya why`) and you get the receipt and every time that date moved.

If a professor emails "moved to Thursday," Gmail (read) is merged as a *partial* reading: it can move or add, it cannot remove, and if the page still shows the old date the email wins and the receipt says the page is stale.

You get **one honest message a night**: what moved, from where, and what it refused to touch. Unreadable pages, pending removals, and review items appear every time — even when nothing moved.

### What it will not do to a deadline

- **Guess.** "TBD", "week of Oct 12", "next Friday", a weekday that conflicts with a date, two sources that disagree → **needs-review**. You clear an item with one reply ("the museum visit is Oct 30" / "skip"). Your word is a source like any other: it goes through the same plan, never straight onto the calendar. If the page later changes, the item comes back.
- **Delete because a page failed.** A login wall, MFA, CAPTCHA, empty page, or silent reader marks the source unreadable. Belief is untouched. A removal needs the item gone on **two successful reads on two different days**. A same-day re-read does not count. A failed read in between does not count. "Date became TBD" is not a removal.
- **Duplicate.** Re-running a night, or crashing between a calendar write and commit, creates nothing twice. Each write is recorded before the next one. An uncommitted run recovers on the next `plan`.
- **Wipe a course on noise.** More than two deletes that are also half a course in one run is blocked for you to confirm.
- **Hand-edit a managed event.** Anything with `vidya-key:` in the description belongs to the nightly check. The only path is `vidya plan` → apply exactly those ops → `record` → `commit`.

Say **"check my courses now"** to run the loop on demand. Say **"re-read Physics"** to refresh one source. Say **"what needs review?"** to clear the bucket.

Sunday 6 PM: a **weekly digest** — the next seven days by day, what moved this week with before/after and source, how often each course has changed a date (volatility), pending removals, the review bucket. Facts, not editorial.

---

## 2. Safety check-in (optional, off by default)

A nightly "you good?" in your own chat. Not tracking. It cannot see your phone.

You turn it on by answering questions, one at a time: your first name as family knows it; how many contacts; each contact's name, relationship, email (or a carrier text-to-email address), and whether they **agreed**; the time (9 / 10 / 11 PM); the grace (60 / 90 / 120 minutes); which days; whether to send a Sunday email of exams and deadlines; whether a missed-alert may name a last-known place.

Then:

1. At the due time it asks you in this conversation.
2. A reply like **"I'm home"** / "I'm good" / "checking in" logs it.
3. If you go quiet past the grace period, each consented contact gets **one** email from *your* mailbox: the check-in was missed, it is automatic, it usually means a phone on silent, and when you last checked in.
4. A late check-in sends each alerted contact **one all-clear**.
5. **"Tell mom I'm staying at Priya's tonight"** passes your exact words to that contact (engine-approved, logged). **"Check in later tonight"** pushes the window.
6. A daily cap stops a misconfiguration from spamming anyone. The all-clear is exempt. Failed sends retry; successful ones never repeat.

**Location, if you turn it on.** You share Google Maps location with the Google account on the Bot's computer. Vidya looks **only** when a missed-check-in alert is about to go out, and the place appears **only** inside that alert, with how old it is. Never inferred. Never logged as a trail. Never treated as a check-in.

Who may be messaged, when, and how often is code (`vidya safety plan`). The Bot sends exactly those messages, verbatim. It never messages anyone on its own judgement.

---

## 3. Course tutor

Give it a syllabus. Get the semester taught.

It pulls an ordered topic list from the syllabus, slides, readings, and your notes (each topic keeps a source and the exam it feeds). `vidya teach map` lays **numbered classes on your real session days** around the exams it already believes. The last slot before each exam is review. Spare slots become practice.

Each class is five steps, one message at a time:

1. **Intro** — what this is for, how it connects, which exam it feeds
2. **Core concept** — one idea; every paragraph labelled **From your course material (slide/page)** or **Broader context**
3. **Examples** — the lecturer's, then a new one, including steps the slides skipped
4. **Practice** — graded honestly: what you had right, the main gap, one next step; scored 0–3 into a mastery ledger
5. **Summary** — five lines and a three-question self-check

Controls at every step: **I get it** / **Another example** / **Go deeper** / **I'm confused**.

Two shaky concepts in a row → it slows down and re-teaches. Two days before an exam it offers a review built from `vidya teach weak`. Lessons can be wrong; broader-context claims on testable topics are flagged for you to check. It never does graded homework (that is Assignment coach). If the syllabus forbids AI study help, it says so and stops at scheduling.

Say **"teach me CS 201"**, **"run today's class"**, **"quiz me on recursion"**, **"what am I weak on before the midterm?"**. Optional **Class today** routine posts the Intro on your session days.

---

## 4. Lecture notes → Notion

Drop slides, a transcript, a photo of the board, a reading, or your own notes ("notes for today's CS 201 lecture"). Vidya files one page in **Vidya · Lecture notes**:

- one-paragraph summary
- key ideas (plain definition + the lecturer's example)
- worked examples including skipped steps
- connections to the last lecture and the next exam (named, dated, from `vidya status`)
- five **likely exam questions**, marked as guesses
- office-hours questions the material left open
- sources (file, slide range, page)

Every claim traces to a source; anything added from general knowledge is marked *(background)*. A date mentioned in the material does **not** go onto the calendar — it becomes a reading for the nightly check. Auto-notes per course only if you turn them on. Never posted to class forums. Never redistributes recordings.

---

## 5. Assignment coach

"How should I approach Homework 3?"

You get: what is actually being asked; the rubric decoded (full marks vs. what usually loses points); a plan backwards from the due date (3–6 sessions, estimates + 30%); the three traps; which lecture to reread first; three office-hours questions; a before-submit checklist. Work sessions can go on the calendar after you approve.

It will review a draft for structure and errors, suggest test cases, ask Socratic questions. It will **not** write the essay, the solution code, or the problem-set answer. It will **not** submit anything to the LMS. If the course forbids AI assistance, it says so first and limits itself to explaining the prompt and scheduling time.

---

## 6. Recruiting (internships, resume, projects)

### Opportunity scout

A weekday-morning (or on-demand) diff of the public **SimplifyJobs** Summer internship and new-grad lists against your profile (roles, term, degree level, locations, sponsorship, no-go companies). High school: summer programs and first internships instead.

New postings are scored 1–5. You say which to prepare, or "prepare 4s and up automatically." For each: a one-page tailored resume, a facts file tracing every bullet to your master resume, the form filled from the profile, a screenshot at **Submit**. Questions the profile does not answer are collected and asked once for the whole batch. You reply **"submit all"** or pick numbers. Then it submits, screenshots the confirmation, and logs `vidya track applications <id>`. The same id cannot be applied twice. ATS sites that forbid automation are skipped and handed to you. Login / MFA / CAPTCHA → it stops and you take over.

### Resume tailor

One master resume (your words, verbatim). One page per posting. Every fact (dates, titles, numbers, technologies) identical to the master. `facts.md` is the proof; a bullet with no source line is deleted. Cover letters are drafts you read first. Weekly **gap report**: skills postings want that you do not have, with three project proposals.

### Project builder

Closes a gap with a project you can defend in an interview. Three ideas (not tutorial clones). You pick. Milestones on the calendar. Scaffold + failing test, pushed only after you name the repo. You write the parts an interviewer will ask about; Vidya writes boilerplate and tests, labelled **(AI-assisted)** in commits and the README. After each milestone you explain the code back in three sentences or it is not done. One true resume bullet at the end.

Optional teammates: **Recruiter** (scout + tailor), **Builder** (projects).

---

## 7. Clubs, coffee chats, cold outreach

### Club scout

Reads the directory you name. Every club: what it does, cadence, whether it applies, deadline, link. Clubs with deadlines become watched sources — the nightly check treats them like courses. Fit report for the top 15: **Fit / Stretch / Not now**, with a reason *for* and a reason *against*. Never prestige-only. Applications drafted from your profile and resume facts; you edit, or say "submit" and it stops at Submit. `vidya track club-applications` so it never happens twice.

### Coffee chat scheduler

Shortlist with a specific reason and a channel. First note under 90 words, saved as a Gmail draft. **You send**, or say "send." After a yes: three 20-minute slots inside your hours, a Meet link, the calendar event, three prep questions the morning of, a thank-you draft after. One follow-up maximum, and only if you say so. Nobody contacted twice (`vidya track outreach` / `coffee-chats`).

### Cold outreach

A goal (company, team, research area). Up to 10 people, matched by **what they actually work on**, not title keywords. Preferred sources: team pages, personal sites, GitHub, Scholar, speaker lists, alumni directories. LinkedIn at human pace: one search, at most 10 profiles, no auto-connect, no auto-message, no scrape. A CAPTCHA or warning ends the day. Drafts name a specific public thing they did.

---

## 8. Calendar concierge

Plain English: "block Tuesday and Thursday mornings for the project until the midterm", "put a study session before every exam", "move my gym block to 7."

It shows the exact operations (create / move / delete, collisions, protected time, exams within 24 hours) and applies them on your yes. **Never** touches events with `vidya-key:` — those belong to the page. If you want a deadline changed, the page is the source of truth (or needs-review if the page is wrong). Never accepts invitations for you. Never writes to a calendar you did not name.

Working hours and protected times (sleep, practice, work shifts) are collected once and reused by Fun scout, coffee chats, and assignment sessions.

---

## 9. Fun scout

Thursday 4 PM (and Saturday 10 AM for last-minute): at most ten things, grouped Sports / Concerts / Campus / Parties, each with a "why it fits" line.

- **Sports** — school home games, student-ticket status (free with ID / claimable / paid)
- **Concerts** — Spotify Live Events, ranked by what you actually listen to
- **Campus** — talks, screenings, cultural nights, free food
- **Parties** — only pages **you named**; never DMs, RSVPs, or invite-requests. High school: school events, games, and all-ages shows only; no parties, no 18+/21+

Protected nights and exams within 24 hours are called out, not silently dropped. You pick numbers. Picks go on the calendar (grape) after you approve. **"Ticket for the Friday show, one, cheapest"** walks the official source to the **Pay** button, shows the total against the monthly fun budget, and stops. **"Pay"** completes it using the method already in your account (it never types a card number from chat). Confirmation is screenshot, logged (`vidya track tickets`), and attached to the event. That night the safety reminder knows you are out.

---

## 10. How it is built (from the prompts)

The Bot is not a pile of settings you type. It is a conversation that interviews you.

1. **Build.** Clone the engine, run `selftest` (ALL PASS), save eighteen skills verbatim, set the profile from `PROFILE.md`, ask time zone then LMS, create the 11 PM and Sunday routines, run the Setup playbook. Course list is read from the LMS home if possible; you confirm. Login / MFA / CAPTCHA → you take over the computer. First read → dry run → you approve → real calendar. Then it offers safety and the rest of student life as a pick-list.
2. **Safety setup.** Interview, then `vidya safety` commands, then a test email to *you* before any contact is messaged. Then the 30-minute evening routine window.
3. **Live test.** A two-minute due / two-minute grace against your own address: reminder → missed email → "I'm good" → all-clear → settings restored.
4. **Package.** Audit include/exclude, scrub your name / school / courses / contacts / resume / location to **zero hits**, publish as a public template on "go", then install that template into a stranger Bot and time the first-run.
5. **Update.** One message pulls the engine, re-saves skills, and interviews each new module. **"Skip"** leaves it off.
6. **Course tutor add-on.** Own message if you only want teaching.

You never pre-write a parent's name or an LMS URL into a prompt. The Bot asks. You answer.

---

## 11. What you say

| You say | Vidya does |
|---|---|
| "Check my courses now" | Nightly loop on demand |
| "Re-read Physics" | One source, then plan |
| "What needs review?" | Clear the review bucket |
| "Why is Midterm 1 on the 16th?" | Receipt + every move |
| "What's this week?" | Sunday digest, any day |
| "I'm home" / "I'm good" | Safety check-in |
| "Tell mom I'm staying at Priya's" | Pass-through message, if approved |
| "Check in later tonight" | Push the window |
| "Turn off the check-in for this weekend" | Pause |
| "Teach me &lt;course&gt;" | Map + Class 1 |
| "Run today's class" | Five-step lesson |
| "Quiz me on recursion" | Practice from the ledger |
| "What am I weak on before the midterm?" | `vidya teach weak` |
| "I'm confused" | Re-teach, smaller steps |
| "Notes for today's lecture (attached)" | Notion page |
| "How should I approach Homework 3?" | Coaching note, no submission |
| "Any new internships?" | Scout + scores |
| "Submit all" | Approved application batch |
| "Block Tuesday mornings for the project" | Concierge ops, then your yes |
| "What's going on this weekend?" | Fun shortlist |
| "Ticket for the Friday show, one, cheapest" | Cart to Pay, screenshot, stop |
| "Pay" | Complete that purchase |
| "Set up" / "add a course" | Setup playbook |

---

## 12. Standing rules (always)

1. **LMS is read-only.** Never submit, post, or reply on a course site.
2. **No credential typing.** Login, MFA, CAPTCHA → stop, mark unreadable, you take over.
3. **Messages** only to you, except (a) safety messages `vidya safety plan` approves and (b) messages you have read and approved, from your account, logged in `vidya track`. No bulk-message, no scrape, no LinkedIn automation.
4. **No invented facts** on a resume, form, or application. If it is not on the master resume, it does not go on the page.
5. **No writing the assignment.** Coach, review, plan.
6. **Ambiguous → needs-review**, never the calendar.
7. **Nothing happens twice.** Applications, messages, chats, tickets, fun picks checked against the ledger first.
8. **Tickets stop at Pay** until you say pay. No resale unless you name it.
9. **Your data stays on this computer.** Courses, calendar, contacts, resume, sessions. Nothing owner-identifying goes into a public template.
10. **If `~/vidya-state` is missing**, run Setup playbook before anything else.

---

## 13. How it works (the shape)

LLM at the edges. Code in the middle.

- **Supervisor Bot** (you talk to this one) holds the plugins, launches work, reports. It applies *exactly* what the engine approved.
- **One cheap reader subagent per page** — read-only, no plugins. Writes a small JSON reading: titles and date text verbatim, status `ok` / `empty` / `error`. A login wall stops the reader.
- **`vidya` engine** — standard-library Python, no pip, 79 tests. Extract → normalize → resolve (dates, confidence, timezone, cross-source dedup) → diff vs last night → destructive-write guard → review gate → idempotent calendar plan (keys + provenance + colors) → record → commit. Plus safety plan, receipts (`why`), action ledger (`track`), semester map and mastery (`teach`).
- **State** is plain JSON on the Bot's disk (`~/vidya-state`): config, belief, ledger, missing, needs-review, runs, history, safety, profile, applications, fun, teach.
- **Two write paths for the core loop:** Google Calendar (approved ops only) and Gmail send (approved safety / outreach only). Everything else that writes (Notion, ATS, GitHub, tickets) is a skill that still goes through approval + `vidya track`.

`vidya selftest` prints ALL PASS on a clean computer in about a second: known-answer diff on six synthetic course pages / two nights / five planted changes, idempotency including a crash between apply and commit, the destructive-write guard, a ten-string adversarial date set, timezone/DST, plus safety, receipts, the ledger, and the tutor map.

Optional **Graphiti** (Zep): episodes so you can ask "how many times has this professor moved a deadline."

---

## 14. Tools and connections

| Tool | Direction | For |
|---|---|---|
| Grok Bot cloud computer (browser, filesystem, terminal) | runtime | git, python3, state, sign-in sessions |
| Grok Bot routines | schedule | 11 PM nightly; Sunday digest; safety window; optional 7 AM scout, Thu/Sat fun, class-today |
| Grok Bot subagents | read | one reader per source |
| Google Calendar plugin | write | deadlines, classes, fun picks, study blocks, chats — approved ops only |
| Gmail, read | read | instructor emails that move a date |
| Gmail, send | write | safety + owner-approved outreach, from your mailbox |
| Carrier email-to-SMS | write via Gmail | safety contacts who want a text |
| Notion | write | lecture notes + class summaries |
| LMS pages (browser) | read | any course / registrar / aid / housing / club page |
| Canvas REST + iCal | read | no-login dates |
| SimplifyJobs listings | read | internships / new-grad |
| ATS (Workday, Greenhouse, Lever, …) | write (browser) | applications to Submit, then batch-submit |
| GitHub | write | gap-closing projects, after you name the repo |
| LinkedIn | read, human pace | ≤10 profiles / run; drafts only |
| Spotify Live Events | read | concerts by what you listen to |
| School athletics + ticket portal | read; write to Pay | games and tickets |
| Campus / party pages you name | read | Thursday shortlist |
| Google Maps sharing | read once | last-known place, missed-check-in alert only |
| Graphiti / Zep (optional) | write episodes | schedule history |
| `vidya` + `selftest` | engine | every decision that has to be right |

**Not connected, on purpose:** GPS / continuous location; unattended applications; LinkedIn automation; writing your homework; unattended purchases; attendance; LMS posts; iMessage / WhatsApp / Slack DMs for safety (cannot be logged and de-duplicated from the cloud computer).

---

## 15. Eighteen skills, five routines

**Skills.** Setup playbook · Read course · Nightly syllabus check · Needs-review triage · Weekly digest · Safety check-in · Lecture notes · Assignment coach · Opportunity scout · Resume tailor · Project builder · Club scout · Coffee chat scheduler · Cold outreach · Calendar concierge · Fun scout · Course tutor · Package template

**Always-on routines.** Nightly syllabus check (daily 11:00 PM) · Weekly digest (Sunday 6:00 PM)

**Created only if you turn them on.** Safety check-in (every 30 min in the evening window) · Fun this week (Thu 4:00 PM, Sat 10:00 AM) · Class today (your session days) · Opportunity scout (weekdays 7:00 AM)

The public template ships the profile, the eighteen skills, and the two always-on routines. Your courses, contacts, resume, memories, teammates, and opt-in routines stay off the share link.

---

That is the whole Bot: a nightly honesty loop with receipts, an optional check-in that is not tracking, and the rest of student life behind prepare-and-you-decide. The model talks. The code decides.
