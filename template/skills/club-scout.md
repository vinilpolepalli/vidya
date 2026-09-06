# Skill: Club scout

Finds the clubs, teams and programs worth the owner's time, says which are a
fit and which are not and why, tracks their application deadlines like any
other deadline, drafts the applications, and sets up coffee chats with members.

## When to use
- Start of term, or when the owner asks ("which clubs should I join?", "is the consulting club worth it?", "apply to the robotics team").
- Weekly during recruiting season (September, January) if the owner turned on the "Club scout" routine.

## Required inputs and access
- The school's club directory (URL from the owner, or found in the browser) and each club's page or Instagram/LinkedIn if that is where they post.
- `~/vidya-state/profile/profile.md` (interests, time budget in hours per week, goals: friends, career, competition, service) — collect in setup if missing.
- The owner's calendar (read) for time-budget checks.

## Sequence
1. **Inventory.** Build `~/vidya-state/clubs/directory.md`: every club with one line of what it does, meeting cadence, application required (yes/no), deadline, and the source link. Add each club with an application deadline as a source: `vidya add-source club-<slug> --name "<club>" --url <page> --kind club`, so the nightly check watches the deadline like a course.
2. **Fit report.** For each club the owner shortlists (or the top 15 by relevance), score on: goal match, time cost vs budget, selectivity (from the page), how much the owner's existing skills apply, and what they would get out of it in a year. Verdict per club: **Fit**, **Stretch**, or **Not now**, with two sentences of reasoning and one concrete reason against. Never rate a club on prestige alone. Save `fit-report-<date>.md` and post it.
3. **Coffee chats.** For clubs rated Fit or Stretch that recruit selectively, find one or two current members (club page, LinkedIn at human pace) and run the "Coffee chat scheduler" skill: it drafts the note, the owner sends.
4. **Applications.** For each club the owner says yes to: read the application questions, draft answers from the owner's profile and resume facts only, save `~/vidya-state/clubs/<slug>/application.md`, and show them. The owner edits and submits, or says "submit" and Vidya fills the form and stops at Submit for a final look. `vidya track add club-applications <slug>` after submission so it never happens twice.
5. **Follow-through.** Interview dates and info sessions found on club pages go into the nightly check as items (they are dates on a watched page). Remind the owner the day before through the nightly summary.

## How to validate
- Every club in the fit report has a source link and a deadline (or "rolling").
- `vidya status` lists the clubs with deadlines as sources.
- No application was submitted without the owner's word.

## What to return
The fit report; later, drafted applications and the coffee-chat drafts.

## What requires approval
- Each application submission and each outreach message.
- Never message a club or member without the owner's approval; never submit; never rate a club by prestige alone.
