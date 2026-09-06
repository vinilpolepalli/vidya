# LinkedIn post draft

*Required: written description, the video (native upload), the shared template link, `#GrokBotForStudents`. Opening two lines are all anyone sees before "More". Native video, captions on. Tag Fiona Whittington and Grok Bot. Repeat the template link in the first comment.*

---

My professor moved a midterm at 11 PM. My calendar already knew by the time I woke up.

I built a Grok Bot for the #GrokBotForStudents Student Build Challenge. It's called Vidya (Sanskrit for knowledge). Every night it sends one reader to every page in my student life that has a date on it (my courses, the registrar, financial aid, clubs), compares what it finds with what it believed last night, and writes only the confirmed changes to Google Calendar, with a receipt inside every event: the source link, the exact words on the page, every assumption it made. I can ask "why is Midterm 1 on the 16th?" and get the receipt and every time it moved.

What it won't do
- Guess. "TBD", "week of Oct 12", "next Friday" go to a review list, never onto the calendar.
- Delete anything after a failed page load. A removal needs the item gone on two successful reads on different days.
- Duplicate. Re-running a night creates nothing twice, even after a crash mid-write.
- Log in for me. When MFA shows up it stops and asks me to take over.

The part my parents liked: a nightly check-in. At 9 PM it asks if I'm good. If I don't answer within 90 minutes, my mom gets one email saying so (and that it usually means my phone died); when I reply, she gets the all-clear. Off by default, only to people I named who agreed. It can't see my phone. A check-in, not tracking.

Then it does the rest of the job with one rule, it prepares and I decide: lecture notes into Notion with sources, coaching on how to approach an assignment (never the submission), a nightly scout of the Simplify internship list with applications filled and submitted only as a batch I approve, a resume tailored per posting where every line traces to my master resume, projects to close skill gaps that I drive, club fit reports, coffee chats and cold outreach drafted for me to send, "block Tuesday mornings for the project" in plain English, and a Thursday list of the fun stuff: home games, concerts by artists I actually listen to (it reads my Spotify), campus events, the parties people are talking about. I pick, it goes on the calendar; a ticket gets walked to the Pay button and no further. A ledger on its computer means nothing happens twice.

The part I'm proudest of is the shape, not the bot. LLM at the edges, code in the middle: one supervisor Bot, one cheap reader subagent per page, and a standard-library Python engine with 75 tests deciding what changed, what's ambiguous, what may be written, who may be messaged. The model applies exactly what the code approved. `selftest` prints ALL PASS in a second on a clean machine.

Under the hood: Grok Bot routines, subagents and cloud computer; Google Calendar, Gmail and Notion plugins; Spotify Live Events and the school's ticket portal in the browser; browser reads of Brightspace, Canvas, Blackboard, Schoology, anything with a course page; Canvas REST + iCal; the SimplifyJobs listings; Graphiti (Zep) for "how many times has this professor moved a deadline".

Template (public; one message and it builds itself; college and high school): <TEMPLATE_LINK>
Code and fixture suite: https://github.com/vinilpolepalli/vidya

What is the one thing your LMS should tell you and doesn't?

#GrokBotForStudents

---

## First comment

Template link again for the people who click here: <TEMPLATE_LINK>
It installs the engine on the bot's own computer and self-tests before it touches your calendar. Repo with the fixture suite: https://github.com/vinilpolepalli/vidya

## Direct sends (after posting)

BTE cohort, Cohort Leadership, science fair circuit. One line each, personal, with the link. No pods.

## Things to fill before posting

- `<TEMPLATE_LINK>` from Publish → Public link
- Repo link is already `https://github.com/vinilpolepalli/vidya`; confirm it opens in a private window
- Replace "Brightspace and Canvas" with what T6 actually showed (see CLAIM_AUDIT.md rule: "tested on Brightspace and Canvas" if the sandbox ran clean; "built to generalize, tested on Brightspace" if it needed code)
- If the graph is running locally rather than wired to the bot, change the Graphiti sentence to: "Graphiti (Zep's temporal graph) runs alongside it today for schedule history; wiring it into the nightly routine is next."
