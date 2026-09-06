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
| **Graphiti** (Zep temporal graph) | write | run episodes for "how many times has this professor moved a deadline" | owner runs their own server and key; `vidya graph` exports episodes | optional |
| **Grok Bot routines** | schedule | 11 PM nightly check, Sunday digest, evening safety window | owner confirms schedule and time zone | yes |
| **Grok Bot cloud computer** | runtime | git, python3, browser, filesystem for state | nothing; present by default | yes |

## Not integrated, on purpose

- **Location / GPS.** The Bot runs on a cloud computer and cannot see the
  owner's phone. If the owner wants a place named in a missed-check-in alert,
  they tell the Bot ("checking in from the library") or share a location page
  the Bot's browser can read, and turn on `--include-location`. Nothing is
  inferred, and the place appears only inside an alert.
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

## Adding another LMS

Nothing in the engine branches on platform. A new LMS needs, at most, a new
extractor in `vidya/extract/` that turns its page or API into a Reading JSON;
the "Read course" skill already covers the zero-code path (the Bot reads the
page and writes the JSON by hand, titles and date text verbatim).
