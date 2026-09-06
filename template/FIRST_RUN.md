# First message after adding the template

Send this to the Bot as the first message. Nothing else is needed.

> Run your Setup playbook skill. My school uses <Brightspace / Canvas / Google Classroom / other>. My calendar time zone is <America/New_York>. Stop and ask me whenever you need me to sign in.

What happens next, in order (about ten minutes):

1. The Bot clones the engine onto its computer and runs `selftest`. You will see
   `ALL PASS` with five lines (T1–T5). If you do not, stop; nothing else will work.
2. It asks for your course list, or opens your LMS in its browser and reads the
   list itself. It will hit a login wall. Open **Agent Computer**, take over, sign
   in (password, MFA, CAPTCHA), give control back. The session persists on the
   computer for future nights.
3. It reads each course once and shows you the first belief: every dated item it
   found, plus a needs-review list of things it refused to guess. Correct anything
   wrong now; this is the baseline every later diff compares against.
4. It asks you to connect the **Google Calendar** plugin (Settings → Plugins) and
   which calendar to write to. It then creates the baseline events. Check your
   calendar: deadlines are tomato, classes are peacock, every description has a
   source link.
5. It schedules the nightly routine for 11 PM in your time zone and the Sunday
   digest. Optional: connect Gmail read-only so professor emails that move a date
   are merged in.

If you want to see the loop before touching your real calendar, say
"dry run" in step 4: the Bot applies to a built-in fake calendar first and shows
you what it would have written.
