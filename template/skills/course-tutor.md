# Skill: Course tutor

Give it the syllabus, get the semester taught. Vidya turns a course's real
material (syllabus, slides, readings, the owner's notes) into numbered classes
on real dates, paced around the exams it already believes, and teaches each
class one concept at a time: intro, core concept, examples, practice, summary.
Every claim is labelled as coming from the owner's material or from broader
context. Answers are graded like they count. Weak concepts come back before the
exam.

The engine decides when (`vidya teach map`) and remembers how it went
(`vidya teach record`). The model does the teaching. Lessons can be wrong;
the owner is told to check anything that matters.

## When to use
- The owner asks ("teach me CS 201", "set up classes for Psych", "run today's class", "quiz me on recursion", "what am I weak on before the midterm?").
- The "Class today" routine, if the owner created one.
- Two days before any exam in `vidya status`: offer a review class built from the weak list.

## Required inputs and access
- Engine and state (`~/vidya`, `VIDYA_STATE=~/vidya-state`); `vidya status` for the course's exam dates and the receipt for each (`vidya why`).
- The course material: syllabus (the "Read course" skill already saved the page), slides and readings downloaded from the LMS in the browser, the owner's notes, and any "Lecture notes" pages in Notion for this course. Store copies under `~/vidya-state/teach/<course>/material/`.
- The owner's session days and length (offer: 2 × 45 min, 3 × 30 min, daily 20 min) and their level with the subject (offer: new to it, some background, strong).
- Optional: Notion (to file each class's summary next to the lecture notes), "Calendar concierge" (to put classes on the calendar; owner approves).

## Setup (per course)
1. **Extract topics.** Read the syllabus and week-by-week schedule. Produce `~/vidya-state/teach/<course>/topics.json`: an ordered list of `{"title", "source" (page/slide reference), "exam" (the exam title it is assessed on, if the syllabus says)}`. Show the owner the list to confirm or reorder. If the course has no syllabus, ask for the subject and build a standard topic list for it, marked `"source": "broader context"`.
2. **Map the semester.** `vidya teach map <course> --topics topics.json --start <YYYY-MM-DD> --per-week <n> --days <mon,wed> --out ~/vidya-state/teach/<course>/plan.json`. The engine places numbered classes on the session days, keeps them in syllabus order, reserves the last slot before each exam for review, and turns spare slots into practice. Show the printed map. If it notes "some classes cover two topics" or "topics unplaced", offer more sessions per week or a later start.
3. **Calendar (optional).** Offer to add the classes as "Class N: <topics> (<course>)" events through "Calendar concierge" (owner approves the list). They are the owner's events, never managed ones.
4. **Level.** Ask three quick questions on the first topic to set the starting level. Record with `vidya teach record <course> "<concept>" <score>`.

## Sequence (one class)
1. Open `plan.json`, find today's class (or the one the owner named). Load its topics' material from `material/` and the matching Notion notes.
2. Teach in five steps, one message per step, and wait for the owner between steps:
   - **Intro** (3 sentences): what this class is for, how it connects to the last one and to the exam it feeds (name the exam and date).
   - **Core concept**: one idea, in plain words, then in the course's words. Label each paragraph: **From your course material** (with slide/page reference) or **Broader context** (general knowledge the material assumes). Never blur the two.
   - **Examples**: the one the lecturer used (from material), then one new one (broader context), worked step by step including steps the slides skipped.
   - **Practice**: an understanding check (one question, then a written-answer question). After each answer, mark it: what they had right, the main thing they missed, one next step. Score the concept 0 (confused), 1 (shaky), 2 (got it), 3 (taught it back) and `vidya teach record`.
   - **Summary**: five lines, then the three-question self-check for tomorrow.
3. At every step offer exactly these controls: **I get it** (advance), **Another example** (a fresh example, broader context, labelled), **Go deeper** (the why behind the rule, edge cases), **I'm confused** (re-teach from a different angle, smaller steps, then a simpler check; score 0 for now). Adapt pace from the scores: two shaky concepts in a row means slow down and re-teach before moving on.
4. Practice classes: pull problems from the material first (problem sets, past exams on the page), then generate similar ones; grade against a rubric you state before the owner answers.
5. Review classes: `vidya teach weak <course>`; re-teach the weak concepts in order, then a mixed practice set covering everything before the exam; end with the owner's readiness in one honest line.
6. If Notion is connected: file the class summary and the owner's scores as a page in the "Vidya · Lecture notes" database, property Lecture = "Class N".

## Rules
- Provenance on every claim. "From your course material" means you can point at the slide or page; otherwise it is "Broader context". If the material and general knowledge disagree, teach the material's version and flag the disagreement.
- Grade honestly. No "great job" for a wrong answer. Partially correct is a real grade.
- Never do the owner's graded work. Practice problems are Vidya's or from the material; if the owner pastes an assignment question, switch to "Assignment coach" rules.
- Say when a lesson may be wrong: any claim scored "Broader context" on a topic the owner will be tested on should be checked against the material or the instructor.
- Respect the course's policy on AI assistance for studying (read the syllabus section); if it forbids it, say so and stop at scheduling.

## How to validate
- `plan.json` exists; the map's exams match `vidya status`; every class has a date.
- Each taught concept has a `vidya teach record` entry; `vidya teach status <course>` moves over the term.
- Every explanation paragraph carries one of the two labels.

## What to return
Setup: the confirmed topic list and the printed semester map. A class: the five steps, one at a time. Review: the weak list, then the readiness line.

## What requires approval
- Calendar writes (through the concierge).
- Filing to Notion the first time.
- Never share the owner's scores or material with anyone; never post to class forums; never redistribute recordings.
