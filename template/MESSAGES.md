# Messages to send Vidya, in order

Every block below is one message. On GitHub, hover a block and use the copy
button. Fill in anything in `<angle brackets>` before sending. Between messages
there is a short note on what the app will ask you to do yourself.

Before message 1: in the Grok Bot app, New → Create new agent → Bot actions →
Edit Profile → Name: `Vidya`. Nothing else.

---

## Message 1: build yourself

Change `Canvas` and `America/New_York` if yours differ.

```text
You are going to assemble yourself from a public repository. Do every step, in order, and report after each one in a single line. Do not summarize or shorten any text you are told to save verbatim.

1. On your computer: cd ~ && git clone https://github.com/vinilpolepalli/vidya vidya && cd ~/vidya && python3 -m vidya.cli selftest. Expect ALL PASS. If not, stop and show me the output.

2. Read ~/vidya/template/PROFILE.md. Set your own title to the Title line and your description to the quoted Description block, word for word. If you cannot edit your own profile, print both fields exactly as written so I can paste them into Edit Profile, and wait for me to say "done".

3. For each file in ~/vidya/template/skills/ (there are seven: setup-playbook.md, read-course.md, nightly-syllabus-check.md, needs-review-triage.md, weekly-digest.md, safety-checkin.md, package-template.md), save a skill. The skill name is the H1 heading without the "Skill: " prefix (so "Setup playbook", "Read course", "Nightly syllabus check", "Needs-review triage", "Weekly digest", "Safety check-in", "Package template"). The skill instructions are the entire file body below the heading, verbatim. Make sure each skill is enabled for you. When done, list the seven skill names and confirm each is available.

4. Create two routines from ~/vidya/template/routines/nightly-2300.md and weekly-digest.md. Use the quoted paragraph in each file as the routine instruction, with <owner time zone> replaced by America/New_York. Nightly syllabus check: every day at 11:00 PM. Weekly digest: every Sunday at 6:00 PM. Do not run them yet. Do not create the safety check-in routine now; it is created only if I turn check-ins on during setup.

5. Report: skills created, routines created with their next run time, and anything you could not do yourself.

6. Then run your Setup playbook skill. My school uses Canvas. My calendar time zone is America/New_York. Stop and ask me whenever you need me to sign in; never type credentials or attempt MFA yourself.
```

You will be asked to: take over the Agent Computer and sign in to your LMS
(then hand control back); connect the Google Calendar plugin (Settings →
Plugins) and name the calendar; approve the baseline before it writes.

If it saved a shortened skill or profile:

```text
You shortened it. Save the file contents exactly as written, no summary, then show me the last section of what you saved.
```

If it printed the profile fields instead of setting them: paste them into Edit
Profile yourself, then send:

```text
done
```

---

## Message 2: turn on the safety check-in

Send when the playbook offers it (or any time after setup). Only list people
who have actually agreed to receive these emails.

```text
Yes, set up the safety check-in. Run the "Safety check-in" skill's setup with these answers so you don't have to ask:

- My first name as my contacts know me: <Vinil>
- Contacts who have agreed to receive messages:
  - id mom, name <Mom's name>, relationship parent, address <mom@email.com>
  - id dad, name <Dad's name>, relationship parent, address <dad@email.com>
- Check-in due 9:00 PM, grace 90 minutes, days mon,tue,wed,thu,fri,sat,sun
- Weekly schedule share: no for now. Location in alerts: no.

Run the exact vidya safety commands from the skill, then show me vidya safety status. Then send one test email to my own address <my@email.com> through Gmail and tell me when it is sent so I can confirm it arrived. Do not message any contact until I have confirmed the test.
```

You will be asked to: connect Gmail with send permission. Check your inbox,
then send:

```text
Got the test email. The safety setup is confirmed.
```

Optional, if you want a parent to get the Sunday exams-and-deadlines email:

```text
Turn on the weekly schedule share to mom, Sundays at 6:00 PM, and show me vidya safety status.
```

---

## Message 3: create the safety routine

```text
Create a routine called "Safety check-in": every day at 9:00 PM, 9:30 PM, 10:00 PM, 10:30 PM, 11:00 PM and 11:30 PM America/New_York, run the "Safety check-in" skill: run vidya safety plan and act only on what it approves. Post an owner reminder in this conversation; send any other approved message through Gmail exactly as written and record it with vidya safety record. If the plan approves nothing, post nothing. Never message anyone not on the approved list. If the engine or state directory is missing, post "setup required" once and stop. If you can only set one time per routine, create one routine per time. Show me the routines and their next run.
```

---

## Message 4: five-minute live test (you watching)

Pick a time two minutes from now for `<HH:MM>`.

```text
Temporarily set my check-in for a test: run vidya safety set-checkin --due <HH:MM> --grace 2. Temporarily make my own address the only contact: vidya safety remove-contact mom, vidya safety remove-contact dad, then vidya safety add-contact me --name Me --address <my@email.com> --consented. Then run the Safety check-in routine's Test run now, again in 2 minutes, and again in 4 minutes. I expect: a reminder here, then an email to me, then after I reply "I'm good" an all-clear email. Tell me before each run what vidya safety plan approved.
```

When the reminder appears in chat, wait for the alert email, then send:

```text
I'm good
```

After the all-clear email arrives:

```text
Test passed. Restore the real settings: vidya safety set-checkin --due 21:00 --grace 90, vidya safety remove-contact me, then re-add mom and dad with exactly the details from before, and show me vidya safety status.
```

Then in the app: View conversation details → Routines → enable Nightly
syllabus check, Weekly digest and Safety check-in. Press Test run on the
nightly check once; it should report zero changes.

```text
Run a Test run of the Nightly syllabus check routine now and post the summary. It should report no changes.
```

---

## Message 5: package and publish the template

```text
Run your "Package template" skill. Audit your memories, skills, routines and plugins out loud. Include the seven skills and the two routines (Nightly syllabus check and Weekly digest, not the Safety check-in routine). Exclude every memory about my courses, my contacts, my school, my family, or me. Show me the inclusion list with one line of justification per item before publishing, and do not publish until I say go.
```

Read the list against `SCRUB_CHECKLIST.md`. If it is clean:

```text
Go. Publish as a public template and give me the link.
```

Open the link in a private browser window to confirm it loads.

---

## Everyday messages

```text
I'm home
```

```text
Tell mom I'm staying at Priya's tonight
```

```text
What needs review?
```

```text
Re-read Physics
```

```text
Check my courses now
```

```text
Turn off the check-in for this weekend
```

```text
Turn the safety check-in off
```
