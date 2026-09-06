# Written description (requirement 1)

*What the Bot does and the tools it uses. Paste-ready; trim to taste. Every claim here is either a frame in the video or a test in the repo; see `CLAIM_AUDIT.md`.*

---

**Vidya** is a Grok Bot that watches my course pages every night and keeps my calendar honest.

At 11 PM it reads every course's syllabus, assignments and announcements on its own cloud computer, compares them against what it believed the night before, writes the confirmed changes to Google Calendar (classes in peacock, deadlines in tomato), and sends me one message: what moved, from where, with a link to the source. When a professor moves a midterm at 11 PM, my calendar knows before I wake up.

**How it works.** LLM at the edges, code in the middle. The Bot's model reads pages and applies calendar operations through plugins. Everything between those two points is a small Python engine that runs on the Bot's computer: normalize the items, parse the dates, diff against last night, refuse destructive writes, gate the plan, keep the calendar ledger idempotent. That is the part that could wipe a semester, so it is code with a fixture suite, not a prompt.

**Rules it will not break.**
- A failed or empty page read never deletes anything. Deleting an event needs the item gone on two successful reads on different days.
- Anything ambiguous ("TBD", "week of Oct 12", "next Friday", "before class", sources that disagree) goes to a needs-review bucket. It is never guessed onto the calendar.
- Every event carries provenance: source URL, when it was read, the text as written, every assumption made (like the timezone it had to assume), and a confidence score.
- Read-only outside the calendar. It never sends email, never submits anything, never signs in by itself; when a login or MFA prompt appears it stops and asks me to take over the computer.
- Re-running a night never creates anything twice, even if it crashed halfway through writing.

**Tools.** Grok Bot's persistent cloud computer (browser, filesystem, terminal) and scheduled routines; browser automation to read Brightspace; Canvas's REST API and iCal feeds as no-login alternatives; the Google Calendar plugin for write-back; Gmail read-only so a professor's "moved to Thursday" email is merged into the same timeline; filesystem snapshots for the nightly diff; a Python engine (standard library only) with a fixture suite; Graphiti (Zep's temporal knowledge graph) for history queries like "how many times has this professor moved a deadline".

**Tested, not vibes.** Ships with a fixture suite: six course pages across two nights with five planted changes (a moved date, an added assignment, a removed assignment, a reworded title, a page that failed to load), a known-answer diff test, an idempotency test, a destructive-write guard test, a ten-string adversarial date-parsing set, timezone tests, and a Canvas sandbox test that runs the same loop with no code changes. `vidya selftest` on a clean computer prints `ALL PASS` in about a second.

**Template.** The shared template includes a setup playbook the Bot runs on first message: it installs the engine on its own computer, proves it with the self-test, asks which LMS you use, has you sign in through its browser once, reads your courses, shows you the baseline before writing anything, and schedules the 11 PM routine. Works on Brightspace and Canvas; built to generalize to anything with a course list, an assignments page and an announcements feed.

---

## Shorter variant (if the post needs room)

Vidya is a Grok Bot that reads my course pages every night on its own cloud computer, diffs them against last night, writes confirmed changes to Google Calendar with the source attached, and messages me what moved. A failed read never deletes anything; ambiguous dates go to a review bucket instead of the calendar; re-runs never duplicate. Tools: Grok Bot routines + browser, Google Calendar plugin, Gmail (read-only), Canvas API and iCal feeds, a stdlib Python engine with a fixture suite (known-answer diff, idempotency, destructive-write guard, adversarial dates, timezone, multi-LMS), Graphiti for schedule history.
