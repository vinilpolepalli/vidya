# One-message bootstrap

Fastest way to build the Bot. Do these two things in the Grok Bot app, then
paste one message. The Bot does the rest on its own computer and asks you, one
question at a time, for anything only you know (time zone, LMS, courses,
safety contacts). Nothing in the message needs editing.

1. New → Create new agent. Open Bot actions → Edit Profile and set the name to
   **Vidya**. (Only the name is needed here; the Bot fills in the rest.)
2. Paste **Message 1** from [`MESSAGES.md`](MESSAGES.md) as the first message.
   That file holds every later message too (safety setup, routine, live test,
   publish, everyday phrases), each as a copy-paste block.

## What you will have to do yourself

- Answer the Bot's questions in the chat (time zone, LMS, course list, whether
  you want the safety check-in and who the contacts are).
- Sign in to your LMS when the Bot hits the login wall (open Agent Computer,
  take over, sign in, hand control back). Sessions persist for future nights.
- Connect the Google Calendar plugin when asked (Settings → Plugins).
- If you say yes to the safety check-in: connect Gmail with send permission and
  confirm the test email arrived before any contact is messaged.
- Confirm the baseline the Bot shows you before it writes to the real calendar.
- Press **Test run** on the nightly routine once, while watching, then enable it.
- When everything works: Bot settings → **Share as template** → review → public
  → copy the link. Run `SCRUB_CHECKLIST.md` first.

## If a step does not stick

Some builds summarize text instead of saving it. The fix is the same for the
profile and for skills: tell the Bot "you shortened it; save the file contents
exactly as written, no summary", or paste the file yourself (Edit Profile for
the profile; "Save this as a skill called <name>, exactly as written" for a
skill). Check a saved skill by opening it: the last section should be "What
requires approval" for Setup playbook, and "Return" for Nightly syllabus check.
