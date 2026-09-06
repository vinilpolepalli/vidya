# Skill: Resume tailor

Turns one master resume into a one-page resume tailored to one posting, without
ever inventing anything. Also finds the gap between what postings ask for and
what the owner has, and hands gaps to the "Project builder" skill.

## When to use
- Called by "Opportunity scout" per posting.
- The owner asks ("tailor my resume for this", "what am I missing for backend roles?", "set up my profile").

## Required inputs and access
- `~/vidya-state/profile/master-resume.md` (or .pdf/.docx the owner uploads): the full, true record. Everything on any tailored resume must trace to a line here.
- `~/vidya-state/profile/profile.md`: targets, grad year, level, locations, sponsorship, no-go list, tone preferences, high school vs college.
- The posting text (URL or pasted).

## Setup (first time)
1. Ask the owner for their current resume (upload or paste) and save it as `master-resume.md`, converting to Markdown with sections Education, Experience, Projects, Skills, Leadership/Activities, Awards. Keep every bullet verbatim; add nothing.
2. Ask, one question at a time: target roles (offer Software Engineering, Data/ML, Product, Design, Research, other), target term and grad year, degree level (offer High school, Bachelor's, Master's, PhD), locations, whether sponsorship is needed, companies to never apply to, and whether they want a "prepare 4s and up automatically" default (offer yes / no). Save to `profile.md`.
3. Produce a first **gap report** (step 7 below) against 20 current postings in their target category, so the owner sees what to build before any application goes out.

## Sequence (per posting)
1. Extract from the posting: required skills, preferred skills, responsibilities, level, location, and any keywords repeated more than once.
2. Select from the master resume the experiences, projects and skills that match. Reorder sections so the most relevant is first. Rewrite bullets for relevance and verbs, keeping every fact (dates, titles, numbers, technologies) identical to the master. Never add a technology, number, title or outcome that is not in the master. Never change a date.
3. Fit to one page. Cut the least relevant bullets rather than shrinking the font below 10.5 pt.
4. Write `facts.md`: for every bullet on the tailored resume, the master-resume line it came from. If any bullet has no source line, delete the bullet.
5. Render to PDF (`pandoc` or the browser's print-to-PDF). Save `resume.pdf`, `resume.md`, `facts.md` in `~/vidya-state/applications/<posting id>/`.
6. If the form has a cover letter field: draft `cover.md`, three short paragraphs, only from facts in the master resume and the posting. Mark it clearly as a draft for the owner to read before it is used.
7. **Gap report** (weekly, or on request): tally the required skills across the owner's target postings; list the ones absent from the master resume with how many postings asked for them; for the top three, propose one project each and hand them to "Project builder". Save as `~/vidya-state/profile/gaps-<date>.md`.

## How to validate
- Every bullet in `resume.md` appears in `facts.md` with a source line.
- The PDF is one page.
- No date, number, employer or title differs from the master resume.

## What to return
Per posting: the PDF path, the headline of what was emphasized, and the count of bullets cut. Gap report: the ranked list and the three project proposals.

## What requires approval
- Any change to the master resume (only the owner edits it; suggest, do not change).
- Using a cover letter (the owner reads it first).
- Never invent, inflate, or round up. If the owner asks to add something that is not true, decline and explain why once.
