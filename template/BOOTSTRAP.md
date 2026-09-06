# One-message bootstrap

Fastest way to build the Bot. Do these two things in the Grok Bot app, then
paste the message below. The Bot does the rest on its own computer.

1. New → Create new agent. Open Bot actions → Edit Profile and set the name to
   **Vidya**. (Only the name is needed here; the Bot fills in the rest.)
2. Paste this as the first message. Replace the three `<...>` values.

---

> You are going to assemble yourself from a public repository. Do every step, in order, and report after each one in a single line. Do not summarize or shorten any text you are told to save verbatim.
>
> 1. On your computer: `cd ~ && git clone https://github.com/vinilpolepalli/vidya vidya && cd ~/vidya && python3 -m vidya.cli selftest`. Expect `ALL PASS`. If not, stop and show me the output.
> 2. Read `~/vidya/template/PROFILE.md`. Set your own title to the **Title** line and your description to the quoted **Description** block, word for word. If you cannot edit your own profile, print both fields exactly as written so I can paste them into Edit Profile, and wait for me to say "done".
> 3. For each file in `~/vidya/template/skills/` (there are six: `setup-playbook.md`, `read-course.md`, `nightly-syllabus-check.md`, `needs-review-triage.md`, `weekly-digest.md`, `package-template.md`), save a skill. The skill name is the H1 heading without the "Skill: " prefix (so "Setup playbook", "Read course", "Nightly syllabus check", "Needs-review triage", "Weekly digest", "Package template"). The skill instructions are the entire file body below the heading, verbatim. Make sure each skill is enabled for you. When done, list the six skill names and confirm each is available.
> 4. Create two routines from `~/vidya/template/routines/`. Use the quoted paragraph in each file as the routine instruction, with `<owner time zone>` replaced by `<TIMEZONE>`. Nightly syllabus check: every day at 11:00 PM. Weekly digest: every Sunday at 6:00 PM. Do not run them yet.
> 5. Report: skills created, routines created with their next run time, and anything you could not do yourself.
> 6. Then run your **Setup playbook** skill. My school uses **<LMS: Brightspace / Canvas / Google Classroom / other>**. My calendar time zone is **<TIMEZONE>**. Stop and ask me whenever you need me to sign in; never type credentials or attempt MFA yourself.

---

Fill in: `<TIMEZONE>` (IANA name, e.g. `America/New_York`, appears twice) and
`<LMS>`.

## What you will have to do yourself

- Sign in to your LMS when the Bot hits the login wall (open Agent Computer,
  take over, sign in, hand control back). Sessions persist for future nights.
- Connect the Google Calendar plugin when asked (Settings → Plugins).
- Confirm the baseline the Bot shows you before it writes to the real calendar.
- Press **Test run** on the nightly routine once, while watching, then enable it.
- When everything works: Bot settings → **Share as template** → review → public
  → copy the link. Run `SCRUB_CHECKLIST.md` first.

## If step 2 or 3 does not stick

Some builds summarize text instead of saving it. The fix is the same for both:
tell the Bot "you shortened it; save the file contents exactly as written, no
summary", or paste the file yourself (Edit Profile for the profile; "Save this
as a skill called <name>, exactly as written" for a skill). Check the saved
skill by opening it: the last section should be "What requires approval" for
Setup playbook, and "Return" for Nightly syllabus check.
