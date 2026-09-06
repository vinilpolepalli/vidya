# Skill: Lecture notes

Turns whatever the owner has from a lecture (slides, a recording transcript,
a photo of the board, their own scrappy notes, the assigned reading) into
detailed structured notes in Notion, linked to the course and the calendar.

## When to use
- The owner drops material in chat ("notes for today's CS 201 lecture", a PDF, a transcript, a link to slides on the LMS).
- The "Read course" skill finds new slides or lecture recordings on a course page (it lists them; this skill processes them only when the owner says so, or if the owner turned on "auto-notes" for that course).

## Required inputs and access
- Notion plugin connected; a database the owner chose (Vidya creates "Vidya · Lecture notes" on first use, with properties Course, Date, Lecture, Source, Status, Exam-relevant).
- The material. Slides and PDFs via download from the LMS in the browser; recordings only if a transcript is available or the owner pastes one (Vidya does not transcribe audio itself).
- `vidya status` for course ids and the next exam date per course.

## Sequence
1. Identify course and date. If unclear, ask.
2. Read everything provided. Write notes with this structure, in the owner's language and at the level of the course:
   - **One-paragraph summary** (what this lecture was for).
   - **Key ideas**, each with a definition in plain words and the one example the lecturer used.
   - **Worked examples** step by step, including the steps the slides skipped.
   - **Connections**: what earlier lecture this builds on, what upcoming assignment or exam it feeds (from `vidya status`: name the exam and its date).
   - **Likely exam questions**: five, with short model answers, marked as Vidya's guesses.
   - **Open questions** the material left unanswered, phrased as things to ask in office hours.
   - **Sources**: every file, slide range and page number used.
3. Create one Notion page in the database with the properties filled, the notes as the body, and a callout at the top saying these are AI-generated from the listed sources.
4. If the lecture material mentions a date (an assignment moved, a review session), do not put it on the calendar; write it as a Reading JSON item and hand it to the nightly check, which will treat it like any other source.
5. Reply with the Notion link and the five likely exam questions.

## How to validate
- Every claim in the notes traces to a source in the Sources section; anything Vidya added from general knowledge is marked "(background)".
- The Notion page has Course, Date and Source properties set.

## What to return
The link and the five questions. Nothing else.

## What requires approval
- Turning on auto-notes for a course.
- Sharing any Notion page with anyone (Vidya never shares pages; the owner does).
- Never upload course material anywhere but the owner's own Notion; never post notes to shared class forums; respect a course's policy if the syllabus says recordings may not be redistributed (notes are fine, copies of recordings are not).
