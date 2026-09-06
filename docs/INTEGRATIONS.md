# Integrations

What Vidya connects to, what each connection is allowed to do, and what it is
not. Every write path goes through the engine; the Bot's model never decides on
its own to write anywhere.

| Integration | Direction | Used for | Set up by | Required? |
|---|---|---|---|---|
| **Any LMS course page** (Brightspace, Canvas, Blackboard, Moodle, Google Classroom, anything with a syllabus/assignments/announcements page) | read | nightly reads via the Bot's browser; saved page → `vidya extract html`, or the Bot writes Reading JSON itself | owner signs in once through the Bot's browser (takeover); session persists | yes, at least one |
| **Canvas REST API** | read | no-login reads: assignments, announcements, calendar events | owner creates a token (Account → Settings) and exports `CANVAS_TOKEN` in the Bot's terminal | optional |
| **iCal feed** (Brightspace Calendar → Subscribe, Canvas Calendar Feed, most others) | read | no-login dates; survives LMS redesigns | owner pastes the feed URL into `vidya add-course` / `vidya extract ical` | optional, recommended |
| **Google Calendar plugin** | write | create/update/delete events from the approved plan; classes peacock, deadlines tomato; provenance in description | owner connects the plugin, names the calendar | yes |
| **Gmail plugin, read** | read | instructor emails that move a date are merged as a partial reading (can move/add, never remove) | owner connects Gmail | optional |
| **Gmail plugin, send** | write | safety check-in messages only: missed-check-in notice, all-clear, owner-requested message, weekly schedule share; from the owner's mailbox to contacts the owner added | owner turns on `vidya safety` and adds consented contacts | optional, off by default |
| **Carrier text gateway** (e.g. `number@vtext.com`) | write (via Gmail) | lets a safety contact receive the message as a text where the carrier still supports email-to-SMS | address entered as the contact's address | optional |
| **Google Maps location sharing** | read (browser) | last-known place and its age, read only when a missed-check-in alert is about to go out, shown only inside that alert | owner shares location from their phone with the account the Bot's browser uses, and turns on `--include-location` | optional, off by default |
| **Notion plugin** | write | lecture notes database ("Vidya · Lecture notes"), one page per lecture with sources | owner connects Notion | optional |
| **SimplifyJobs listings** (`Summer2027-Internships`, `New-Grad-Positions`, `listings.json`) | read | nightly diff of new postings against the owner's profile; stable ids feed the dedupe ledger | nothing; public | optional |
| **ATS sites** (Workday, Greenhouse, Lever, …) | write (browser) | applications filled from the profile and tailored resume, stopped at Submit, submitted as an owner-approved batch, logged in `vidya track applications` | owner's own accounts; sign-in via takeover | optional |
| **GitHub** | write | repos for gap-closing projects, pushed only after the owner names the repo | owner's account; sign-in via takeover | optional |
| **LinkedIn** (browser, human pace) | read | shortlists for outreach: at most 10 profiles per run, no automation, no scraping, no bulk actions | owner signs in via takeover | optional |
| **Gmail plugin, send (approved messages)** | write | outreach, coffee-chat and club messages the owner has read and approved, logged in `vidya track outreach` | owner approves each message or a batch they read | optional |
| **Graphiti** (Zep temporal graph) | write | run episodes for "how many times has this professor moved a deadline" | owner runs their own server and key; `vidya graph` exports episodes | optional |
| **Grok Bot routines** | schedule | 11 PM nightly check, Sunday digest, evening safety window | owner confirms schedule and time zone | yes |
| **Grok Bot cloud computer** | runtime | git, python3, browser, filesystem for state | nothing; present by default | yes |

## Not integrated, on purpose

- **GPS / continuous location.** The Bot runs on a cloud computer and cannot
  see the owner's phone. The only location path is the one above: Google Maps
  sharing the owner turns on, read once, when an alert is about to go out,
  shown only inside that alert with its age. Nothing is inferred and nothing is
  logged as a trail.
- **Unattended job applications.** Applications are prepared to the Submit
  button and submitted as a batch the owner approved in the conversation. ATS
  sites that forbid automated applications are skipped and handed to the owner.
- **LinkedIn automation.** No scraping, no auto-connect, no auto-message, no
  third-party extensions; at most ten profiles opened per run.
- **Writing the owner's assignments.** Coaching, review and planning only.
- **Attendance.** Same reason: no sensor, no claim.
- **Auto-submitting anything to the LMS.** Read-only. The Bot never posts,
  submits, or replies on a course site.
- **Messaging apps (iMessage, WhatsApp, Slack DMs) for safety contacts.** Not
  available from the cloud computer in a way the engine can log and de-duplicate.
  Email (and carrier text gateways where they exist) is the channel because the
  Gmail plugin is first-party and every send can be recorded.
- **Sending on the Bot's own judgement.** Every outbound message comes from
  `vidya safety plan` with an idempotency key, or it does not go.

## Safety check-in, in one paragraph

Off until the owner runs `vidya safety enable`. The owner names contacts who
agreed, a nightly time and a grace period. At the time, the Bot asks the owner
in their own conversation. If nothing comes back by time + grace, each contact
gets one plain email saying the check-in was missed, that it is automatic and
usually means a phone on silent, and what the last check-in was. If the owner
checks in later, each alerted contact gets one all-clear. A daily cap stops a
misconfiguration from spamming anyone; the all-clear is exempt. Failed sends
retry; successful ones never repeat. Tests: `tests/test_safety.py`.

## The action ledger

Skills that act in the world (applications, outreach, coffee chats, club
applications) check `vidya track has <kind> <key>` before acting and
`vidya track add` right after. A routine can run twice, a Bot can be restarted
mid-task, and nothing is submitted or sent twice. `vidya track list` is the
audit trail the weekly digest and the owner read.

## Adding another LMS

Nothing in the engine branches on platform. A new LMS needs, at most, a new
extractor in `vidya/extract/` that turns its page or API into a Reading JSON;
the "Read course" skill already covers the zero-code path (the Bot reads the
page and writes the JSON by hand, titles and date text verbatim).
