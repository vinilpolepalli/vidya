# Skill: Project builder

Closes a skill gap with a real project the owner can defend in an interview.
Vidya scopes it, scaffolds it, and pair-programs; the owner drives, commits and
can explain every file. The README says what was AI-assisted.

## When to use
- "Resume tailor" hands over a gap ("12 of 20 postings want Go; you have none").
- The owner asks ("I need a project that shows systems skills", "help me build something for my resume").

## Required inputs and access
- The gap (skill, why it matters, how many postings asked).
- The owner's time budget (offer: one weekend, two weekends, a month) and current level with that skill (offer: never touched it, some tutorials, used it once).
- GitHub account (the owner's; Vidya pushes only to a repo the owner created or approved).
- Terminal on this computer for scaffolding and running tests.

## Sequence
1. **Scope.** Propose three project ideas that (a) exercise the gap skill in a way an interviewer would probe, (b) fit the time budget, (c) are not a tutorial clone (no todo apps, no weather apps). Each: one paragraph, the three hardest parts, what the finished README will claim. Owner picks one.
2. **Plan.** Write `~/vidya-state/projects/<name>/PLAN.md`: milestones sized to sessions of 2–3 hours, with a definition of done per milestone and a test that proves it. Add the milestones to the owner's calendar as proposals through "Calendar concierge" (they approve).
3. **Scaffold.** Create the repo skeleton, tooling, CI, and a failing test for milestone 1. Push to the owner's repo after they confirm the repo name and visibility. Commit message: "scaffold (AI-assisted)".
4. **Pair-program, owner driving.** For each milestone: explain the approach in plain words, let the owner write the core logic, review it, point at bugs rather than fixing them silently, write tests together. Vidya may write boilerplate and tests; the owner writes the parts an interviewer will ask about. Every commit the owner did not write themselves is labelled "(AI-assisted)".
5. **Explain-back.** After each milestone, ask the owner to explain the code back in three sentences. If they cannot, that milestone is not done; go through it again.
6. **README.** Problem, design, the three hard parts and how they were solved, how to run, how to test, and a line: "Built by <owner> with AI pair-programming assistance for scaffolding and tests."
7. **Resume line.** Hand "Resume tailor" one true bullet: what it does, the stack, one number (tests, throughput, size of data, users if any).

## How to validate
- Tests pass on a clean clone.
- The owner can explain every file in `src/` without notes.
- The README's claims match the code.

## What to return
The plan, then per milestone a one-line status; at the end the repo link and the resume bullet.

## What requires approval
- Repo creation and every push.
- Any dependency or service that costs money.
- Never write the whole project while the owner watches; never remove the AI-assisted labels; never suggest presenting Vidya's work as the owner's own.
