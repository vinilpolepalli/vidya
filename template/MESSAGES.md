# Messages to send Vidya, in order

Every block below is one message. On GitHub, hover a block and use the copy
button. Nothing needs filling in: wherever the Bot needs something from you (your
name, your school's LMS, your parents' emails), it asks you in the chat, one
question at a time, and you answer there. Between messages there is a short
note on what the app will ask you to do yourself.

Before message 1: in the Grok Bot app, New → Create new agent → Bot actions →
Edit Profile → Name: `Vidya`. Nothing else.

---

## Message 1: build yourself

```text
You are going to assemble yourself from a public repository and then set yourself up for me. Do every step, in order, and report after each one in a single line. Do not summarize or shorten any text you are told to save verbatim. Whenever you need something from me, ask me one clear question at a time and wait for my answer; do not guess, and do not ask for several things in one message.

1. On your computer: cd ~ && git clone https://github.com/vinilpolepalli/vidya vidya && cd ~/vidya && python3 -m vidya.cli selftest. Expect ALL PASS. If not, stop and show me the output.

2. Read ~/vidya/template/PROFILE.md. Set your own title to the Title line and your description to the quoted Description block, word for word. If you cannot edit your own profile, print both fields exactly as written so I can paste them into Edit Profile, and wait for me to say "done".

3. For each file in ~/vidya/template/skills/ (there are seven: setup-playbook.md, read-course.md, nightly-syllabus-check.md, needs-review-triage.md, weekly-digest.md, safety-checkin.md, package-template.md), save a skill. The skill name is the H1 heading without the "Skill: " prefix (so "Setup playbook", "Read course", "Nightly syllabus check", "Needs-review triage", "Weekly digest", "Safety check-in", "Package template"). The skill instructions are the entire file body below the heading, verbatim. Make sure each skill is enabled for you. When done, list the seven skill names and confirm each is available.

4. Now ask me, one question at a time: (a) which time zone my calendar should use, offering the common US ones as options (America/New_York, America/Chicago, America/Denver, America/Los_Angeles) plus "other"; (b) which LMS my school uses, offering Canvas, Brightspace, Blackboard, Moodle, Google Classroom and "other / not sure" as options. If I pick "not sure", ask me for my school's course website address and work it out from the page. Repeat both answers back to me in one line and wait for me to confirm before continuing.

5. Create two routines from ~/vidya/template/routines/nightly-2300.md and weekly-digest.md. Use the quoted paragraph in each file as the routine instruction, with <owner time zone> replaced by the time zone I confirmed. Nightly syllabus check: every day at 11:00 PM. Weekly digest: every Sunday at 6:00 PM. Do not run them yet. Do not create the safety check-in routine now; it is created only if I turn check-ins on during setup.

6. Report: skills created, routines created with their next run time, and anything you could not do yourself.

7. Then run your Setup playbook skill using the LMS and time zone I confirmed. When you need my course list, first try to read it from my LMS home page yourself and show me what you found as a list I can confirm or correct; only ask me to type courses if the page cannot be read. Stop and ask me whenever you need me to sign in; never type credentials or attempt MFA yourself. When the playbook reaches the optional safety check-in, ask me yes or no and, if yes, run the Safety check-in skill's setup exactly as described in that skill, asking me each question one at a time.
```

You will be asked to: pick a time zone and LMS; take over the Agent Computer
and sign in to your LMS (then hand control back); confirm the course list;
connect the Google Calendar plugin (Settings → Plugins) and name the calendar;
approve the baseline before it writes; answer yes or no to the safety check-in.

If it saved a shortened skill or profile:

```text
You shortened it. Save the file contents exactly as written, no summary, then show me the last section of what you saved so I can see it is complete.
```

If it printed the profile fields instead of setting them: paste them into Edit
Profile yourself, then send:

```text
done
```

---

## Message 2: turn on the safety check-in

Send this if you said no during setup and changed your mind, or if the playbook
never offered it. The Bot interviews you; you never type a list.

```text
Set up the safety check-in for me using your "Safety check-in" skill. Interview me for everything the skill's setup needs, one question at a time, in this order, and wait for each answer before asking the next:

1. My first name as my family knows me.
2. How many people should be contacts (offer 1, 2 or 3).
3. For each contact, in turn: their name, their relationship to me (offer parent, guardian, sibling, friend), their email address, and whether they have agreed to receive these messages (offer yes / not yet). If I answer "not yet" for anyone, do not add them; tell me to ask them first and move on to the next contact.
4. The nightly check-in time (offer 9:00 PM, 10:00 PM, 11:00 PM, or "other") and how long to wait before contacting anyone (offer 60, 90 or 120 minutes).
5. Which days (offer every day, weekdays only, or "let me pick").
6. Whether to also send my contacts a weekly email of my exams and deadlines on Sundays (offer yes / no), and if yes, which of the contacts.
7. Whether to include a last-known place in a missed-check-in alert (offer yes / no), after explaining in one sentence that the only place you can name is one I tell you or share with you.

Then repeat all my answers back in one short list and ask me to confirm. Only after I confirm, run the exact vidya safety commands from the skill for those answers, show me the output of vidya safety status, and then send one test email through Gmail to my own address (use the address of the Gmail account you are connected to; ask me only if you cannot tell) and tell me when it is sent so I can confirm it arrived. Do not message any contact until I have confirmed the test arrived.
```

You will be asked to: connect Gmail with send permission; answer the questions;
check your inbox for the test email, then send:

```text
Got the test email. The safety setup is confirmed.
```

---

## Message 3: create the safety routine

```text
Create the "Safety check-in" routine from ~/vidya/template/routines/safety-checkin.md. Read my configured check-in time and grace period from vidya safety status and work out the run times yourself: every 30 minutes from the check-in time until the check-in time plus the grace period plus one hour, in my time zone. Use the quoted paragraph in that file as the routine instruction with those times and my time zone filled in. If you can only set one time per routine, create one routine per run time with the same instruction. Do not enable anything yet. Show me the routine(s), their run times, and their next run, and ask me to confirm they look right.
```

---

## Message 4: five-minute live test (you watching)

```text
Run a live test of the safety check-in with me watching, using only my own address so nobody else gets anything. Do it like this and tell me what you are doing at each step:

1. Show me vidya safety status and save my current contacts and check-in settings so you can restore them exactly.
2. Remove every contact, then add one contact with id "me", name "Me", and the address of the Gmail account you are connected to, marked consented.
3. Set the check-in due to two minutes from now and the grace to 2 minutes with vidya safety set-checkin.
4. Run the Safety check-in routine's Test run now, then again two minutes later, then again two minutes after that. Before each run, tell me what vidya safety plan approved. I expect: nothing or a reminder here on the first run, an email to me on the second, and after I reply "I'm good" an all-clear email on the third.
5. After the all-clear, restore my real settings exactly as saved in step 1 (check-in time, grace, days, every contact with the same id, name, relationship and address, and the weekly share if it was on), remove the "me" contact, and show me vidya safety status so I can check it matches.

Ask me to confirm before step 2 and before step 5.
```

When the alert email lands in your inbox:

```text
I'm good
```

After it restores your settings and shows the status, check the contacts match, then:

```text
Confirmed, the settings match. Enable the Nightly syllabus check, Weekly digest and Safety check-in routines, then run a Test run of the Nightly syllabus check now and post the summary. It should report no changes.
```

---

## Message 5: package and publish the template

```text
Run your "Package template" skill. Audit your memories, skills, routines and plugins out loud, one line each. Include the seven skills and the two routines (Nightly syllabus check and Weekly digest), not the Safety check-in routine. Exclude every memory that mentions my courses, my school, my professors, my contacts, my family, my calendar, or me. Then search everything you plan to include for email addresses, phone numbers, course ids, calendar ids, tokens, and my school's website hostname, and tell me each hit and what you did with it. Show me the final inclusion list with one line of justification per item, and do not publish until I say go.
```

Read the list against `SCRUB_CHECKLIST.md`. If it is clean:

```text
Go. Publish as a public template and give me the link. Then open the link yourself in a fresh browser window and confirm the preview loads and shows the seven skills and two routines.
```

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

```text
Add a safety contact
```
