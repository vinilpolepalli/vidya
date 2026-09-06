# Skill: Cold outreach

Finds the right people for a recruiting or research goal, at human pace, and
drafts messages worth reading. The owner sends. Nobody is contacted twice.

## When to use
- The owner asks ("find me engineers at Figma to talk to", "who at Columbia works on robotics", "help me reach the hiring manager for this posting").
- "Opportunity scout" suggests it for a posting scored 5 at a company on the owner's want-list.

## Required inputs and access
- The goal (company, team, role, or research topic) and the owner's intro paragraph from `profile.md`.
- Browser signed in as the owner on LinkedIn (owner does the login; Vidya never stores the password).
- Gmail for drafts; "Coffee chat scheduler" for the send-and-schedule half.

## Rules of the road (read before every run)
- LinkedIn's terms prohibit automated scraping and bulk actions, and accounts get restricted for it. Vidya therefore browses LinkedIn the way a person does: one search, open at most 10 profiles per run, read them, take notes, never auto-connect, never auto-message, never scrape lists. If LinkedIn shows a warning or a CAPTCHA, stop for the day and tell the owner.
- Prefer sources that welcome it: company team pages, personal sites, GitHub, Google Scholar, conference speaker lists, university directories, alumni platforms the school runs.

## Sequence
1. **Understand the goal.** Restate it in one line with the ideal person described (role, seniority, team, shared background). Confirm with the owner.
2. **Search.** Build a shortlist of up to 10 people: name, role, company, why they match, the public thing of theirs to mention (a talk, a repo, a post, a paper), and the best channel (work email pattern if the company publishes it, personal site contact, LinkedIn message as a last resort). Semantic matching means reading what they actually work on, not keyword hits: drop anyone whose work does not fit the goal even if the title matches.
3. **Dedupe.** Remove anyone in `vidya track list outreach`.
4. **Draft.** For each person, a note under 90 words as in "Coffee chat scheduler": one specific reference to their work, one clear ask, an easy out. No flattery, no "I hope this finds you well", no attachments on a first note.
5. **Hand off.** Save drafts; show the shortlist and drafts. The owner picks; "Coffee chat scheduler" sends the approved ones and tracks them.
6. **Log.** `~/vidya-state/outreach/<date>.md`: goal, shortlist, what was sent, what to try next if nothing comes back in two weeks.

## How to validate
- Every draft names something specific the person actually did, with a link in the log.
- Nobody in the shortlist is already in `vidya track list outreach`.
- No more than 10 profiles opened per run; no automated actions on LinkedIn.

## What to return
The shortlist with reasons and channels, and the drafts.

## What requires approval
- Every message sent.
- Any connection request (the owner clicks it).
- Never scrape, never bulk-message, never use a third-party automation extension, never contact someone who has said no.
