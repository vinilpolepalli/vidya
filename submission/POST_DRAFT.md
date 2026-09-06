# LinkedIn post draft

*Required: written description, the video (native upload), the shared template link, `#GrokBotForStudents`. Opening two lines are all anyone sees before "More". Native video, captions on. Tag Fiona Whittington and Grok Bot. Repeat the template link in the first comment.*

---

My professor moved a midterm at 11 PM. My calendar already knew by the time I woke up.

I built a Grok Bot for the #GrokBotForStudents Student Build Challenge. It's called Syllabus, and it does one job: every night it reads my course pages on its own cloud computer, compares them with last night, writes what changed to Google Calendar, and messages me what moved and where it saw it.

What it does
- Reads syllabus, assignments and announcements for every course at 11 PM (Grok Bot routine + browser; Canvas API or iCal feed where they exist)
- Diffs against last night's snapshot on its filesystem
- Writes confirmed changes to Google Calendar: classes in peacock, deadlines in tomato, source link in every event
- Merges professor emails that move a date (Gmail, read-only)
- Sends one summary, including what it refused to guess

What it won't do
- Delete anything after a failed or empty page load. A deletion needs the item gone on two successful reads on different days.
- Guess. "TBD", "week of Oct 12", "next Friday" go to a needs-review bucket, never onto the calendar.
- Duplicate. Re-running a night creates nothing twice, even after a crash mid-write.
- Log in for me. When MFA shows up it stops and asks me to take over.

The part I'm proudest of isn't the bot, it's the tests. LLM at the edges, code in the middle: the model reads pages and applies calendar ops; the diff, the date parsing, the destructive-write guard and the ledger are plain Python on the bot's computer, with a fixture suite: six course pages across two nights with five planted changes, a known-answer diff, an idempotency test, a destructive-write guard, an adversarial date set, timezone checks, and a Canvas sandbox run through the same loop with zero code changes. `selftest` prints ALL PASS in a second on a clean machine.

Under the hood: Grok Bot routines and cloud computer, Google Calendar and Gmail plugins, browser automation, Canvas REST + iCal, a stdlib Python engine, and Graphiti (Zep's temporal graph) so I can ask "how many times has this professor moved a deadline" and get an answer with history.

Template (public, setup playbook included, works on Brightspace and Canvas): <TEMPLATE_LINK>
Code and fixture suite: <REPO_URL>

What is the one thing your LMS should tell you and doesn't?

#GrokBotForStudents

---

## First comment

Template link again for the people who click here: <TEMPLATE_LINK>
It installs the engine on the bot's own computer and self-tests before it touches your calendar. Repo with the fixture suite: <REPO_URL>

## Direct sends (after posting)

BTE cohort, Cohort Leadership, science fair circuit. One line each, personal, with the link. No pods.

## Things to fill before posting

- `<TEMPLATE_LINK>` from Publish → Public link
- `<REPO_URL>` once the repository is public
- Replace "Brightspace and Canvas" with what T6 actually showed (see CLAIM_AUDIT.md rule: "tested on Brightspace and Canvas" if the sandbox ran clean; "built to generalize, tested on Brightspace" if it needed code)
- If the graph is running locally rather than wired to the bot, change the Graphiti sentence to: "Graphiti (Zep's temporal graph) runs alongside it today for schedule history; wiring it into the nightly routine is next."
