# Skill: Opportunity scout

Watches the SimplifyJobs internship and new-grad lists every night, finds the
postings that fit the owner, prepares each application end to end, and submits
a batch only after the owner approves the batch. Nothing is ever submitted
twice: `vidya track applications <id>` is the ledger.

## When to use
- Nightly, as part of the "Nightly syllabus check" routine's last step, or its own routine ("Opportunity scout", daily 7:00 AM).
- The owner asks ("any new internships?", "apply to the Stripe one", "what did you apply to this week?").

## Required inputs and access
- Engine and state (`~/vidya`, `VIDYA_STATE=~/vidya-state`).
- The owner's profile file `~/vidya-state/profile/profile.md` (created by the "Resume tailor" skill's setup): target roles, grad year, degree level, locations, sponsorship need, must-have and no-go companies, and the path to the master resume.
- The lists: `https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json` (internships) and `https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json` (new grad). Each entry has a stable `id`, `company_name`, `title`, `url`, `locations`, `terms`, `category`, `degrees`, `sponsorship`, `active`, `date_posted`.
- Browser on this computer for application forms. The owner's own accounts on any ATS (Workday, Greenhouse, Lever, etc.); the owner signs in via takeover when a login appears.

## Sequence
### Scout (every run)
1. Download both `listings.json` files to `~/vidya-state/opportunities/<YYYY-MM-DD>/`. Filter: `active` true; `terms` includes the owner's target term; `category` in the owner's targets (default Software, plus what the profile says); `degrees` includes the owner's level; drop `sponsorship` values the profile rules out; drop no-go companies; drop anything with `vidya track has seen <id>` already true.
2. For each remaining posting, `vidya track add seen <id> --note "<company> — <title>"`. These are "new since last run".
3. Score each new posting 1–5 against the profile (role fit, location, company preference, deadline urgency if visible on the posting page). Do not open more than 20 posting pages per run.
4. Write `~/vidya-state/opportunities/<date>/candidates.md`: one line per posting with score, company, title, location, link. Post the top 10 to the owner with the count of new postings. If nothing new, post nothing (the nightly summary already ran).

### Prepare (only for postings the owner marks "prepare", or all scores ≥ 4 if the owner has said "prepare 4s and up automatically")
5. Skip anything with `vidya track has applications <id>` true. Say so if the owner asked for it explicitly.
6. Run the "Resume tailor" skill for this posting: it produces `~/vidya-state/applications/<id>/resume.pdf` and `cover.md` (only if the form has a cover letter field) and a `facts.md` listing every claim on the tailored resume and where in the master resume it comes from.
7. Open the posting `url` in the browser. If a login, MFA or CAPTCHA appears, stop and ask the owner to take over. Fill every field from the profile and the tailored resume. For any question the profile does not answer (salary expectation, "how did you hear about us", diversity questions, work authorization specifics), do not guess: collect them into `questions.md` and ask the owner once, in one message, for all postings in the batch.
8. Stop at the final Submit button. Take a screenshot of the completed form as `~/vidya-state/applications/<id>/review.png`. Do not submit.

### Submit (batch approval)
9. Post one line per prepared application: company, title, location, the tailored resume's headline, and any answer the owner supplied. Ask: "Submit these N? Reply with 'submit all', or the numbers to submit."
10. For each approved application: click Submit, wait for the confirmation page, screenshot it to `confirmation.png`, then immediately `vidya track add applications <id> --note "<company> — <title> — <confirmation text or number>"`. If the submit fails, record nothing and report it.
11. Report: submitted, failed, skipped as duplicates. Add each submitted application to the owner's Google Calendar? No. Add a line to `~/vidya-state/applications/log.md` instead; the weekly digest reads it.

## How to validate
- `vidya track list applications` shows every submission with a note; no id appears twice.
- Every application folder has `resume.pdf`, `facts.md`, `review.png` and, if submitted, `confirmation.png`.
- Nothing was submitted without the owner's batch approval in this conversation.

## What to return
Scout: the top-10 list or nothing. Prepare: the batch summary and the questions. Submit: submitted / failed / skipped counts with links.

## What requires approval
- Every submission (batch approval is fine; silent submission is not).
- Creating an account on any site (ask; the owner may prefer to do it).
- Any answer not in the profile.
- Never apply to a company on the no-go list, never apply twice, never fabricate a fact on a form, never bypass a CAPTCHA or an ATS that says automated applications are not allowed (skip it, tell the owner, give them the link).
