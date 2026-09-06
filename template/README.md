# Grok Bot template: Vidya

Everything that goes into the shared Bot template, as text files, so it can be
reviewed, scrubbed and versioned before it is pasted into the Grok Bot app.

A template carries: identity, description, skills, routines, selected memories.
It does **not** carry: browser logins, scripts on the computer, custom MCP
servers, conversation history. So every file here assumes a fresh Bot on a fresh
cloud computer that has to bootstrap from the first message alone. The engine
itself is not in the template; the Setup playbook skill clones it from the
public repository (`https://github.com/vinilpolepalli/vidya`) and proves it
with `selftest` before anything else happens.

Vidya is Sanskrit for knowledge; the name is the only thing about the Bot that
is not literal.

| File | Goes where in the app | Purpose |
|---|---|---|
| `PROFILE.md` | Bot actions → Edit Profile | name, label, title, description (the standing rules) |
| `skills/setup-playbook.md` | Skill | first-run bootstrap: clone engine, self-test, courses, plugins, first read |
| `skills/read-course.md` | Skill | the narrow per-course reader job (what a fan-out subagent runs) |
| `skills/nightly-syllabus-check.md` | Skill | the supervisor loop: gather, launch, review, merge, report |
| `skills/needs-review-triage.md` | Skill | how the owner resolves the needs-review bucket |
| `skills/weekly-digest.md` | Skill | the Sunday digest |
| `skills/package-template.md` | Skill | how the Bot audits and packages itself (section 7 of the plan) |
| `routines/nightly-2300.md` | Routine | 11 PM every day, owner-local time |
| `routines/weekly-digest.md` | Routine | Sunday 6 PM |
| `FIRST_RUN.md` | The installer's first message | what to send the Bot after adding the template |
| `BOOTSTRAP.md` | Your first message when building the Bot | one paste: the Bot clones the repo and assembles itself from these files |
| `SCRUB_CHECKLIST.md` | Before Publish → Public link | what must not be in the template |

## Assembling the template in the app

**Fast path:** create a new agent, name it Vidya, and paste the message in
`BOOTSTRAP.md`. The Bot clones this repository onto its own computer and
creates its profile text, the six skills and the two routines from the files
here, then runs the Setup playbook. You only sign in, connect Google Calendar,
and confirm. The manual steps below are the same thing done by hand.

1. Create a new agent (New → Create new agent). Open **Edit Profile** and paste
   the four fields from `PROFILE.md`. The Label field is optional and separate
   from the name; use it for positioning ("Deadline watch").
2. Create each skill from `skills/*.md`. Use the heading as the skill name
   ("Setup playbook", "Read course", "Nightly syllabus check", "Needs-review
   triage", "Weekly digest", "Package template") and paste the body as the
   instructions. The easiest way is to send the Bot the file contents with
   "Save this as a skill called <name>, exactly as written." Then confirm each
   skill is enabled for this Bot (Settings → Plugins → Yours) and appears when
   you type `/`. Skills are the only way instructions travel with a template,
   so the setup playbook has to be a skill, not a chat message.
3. Create the two routines from `routines/*.md` by sending the quoted
   paragraph to the Bot. Confirm owner, schedule, time zone, inputs, expected
   result, approval boundary, and missing-source behavior (the six things the
   docs say to confirm). Use **Test run** once before enabling.
4. Message the Bot with `FIRST_RUN.md` and go through the playbook yourself
   once on your own courses. Fix the playbook, not the bot, wherever you had to
   intervene (T7).
5. Run `skills/package-template.md`: ask the Bot to package itself and justify
   every inclusion. Then `SCRUB_CHECKLIST.md`.
6. Bot settings → **Share as template**. Review the draft it prepares (it
   should list the profile, the six skills and the two routines, and no
   memories about your courses), publish it as **public**, and copy the link.
   Team-only links cannot be opened by judges. Open the link in a private
   window to confirm it renders.

## What the installer experiences

Add to Grok Bot → fresh Bot named Vidya → they send the first message in
`FIRST_RUN.md` → the Bot clones the engine onto its computer, runs the fixture
suite, asks which LMS and which courses, asks them to sign in through the
computer when a login wall appears, reads each course once, shows the first
belief, connects Google Calendar, and schedules the 11 PM routine. Ten minutes
is the budget; the playbook's steps are ordered so the first course read
happens before anything optional.

## Before publishing

The skills clone the public repository `https://github.com/vinilpolepalli/vidya`.
If you fork it, change that URL in `skills/setup-playbook.md`. The bot's
computer needs `git` and `python3` (present on the standard cloud computer); no
pip install is required because the engine has no dependencies.
