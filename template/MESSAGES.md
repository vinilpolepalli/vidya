# Messages to send Vidya, in order

Every block below is one message. On GitHub, hover a block and use the copy
button. Order: 1 build, 2 safety setup (if not done during build), 3 safety
routine, 4 live test, 5 publish, 6 system map for the demo, 7 the big update
for a Vidya that already exists, then everyday phrases. Nothing needs filling in: wherever the Bot needs something from you (your
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

3. For each file in ~/vidya/template/skills/ (there are sixteen: setup-playbook.md, read-course.md, nightly-syllabus-check.md, needs-review-triage.md, weekly-digest.md, safety-checkin.md, lecture-notes.md, assignment-coach.md, opportunity-scout.md, resume-tailor.md, project-builder.md, club-scout.md, coffee-chat-scheduler.md, cold-outreach.md, calendar-concierge.md, package-template.md), save a skill. The skill name is the H1 heading without the "Skill: " prefix (so "Setup playbook", "Read course", "Nightly syllabus check", "Needs-review triage", "Weekly digest", "Safety check-in", "Lecture notes", "Assignment coach", "Opportunity scout", "Resume tailor", "Project builder", "Club scout", "Coffee chat scheduler", "Cold outreach", "Calendar concierge", "Package template"). The skill instructions are the entire file body below the heading, verbatim. Make sure each skill is enabled for you. When done, list the sixteen skill names and confirm each is available.

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
Run your "Package template" skill. Audit your memories, skills, routines and plugins out loud, one line each. Include the sixteen skills and the two routines (Nightly syllabus check and Weekly digest), not the Safety check-in routine or any recruiting routine. Exclude every memory that mentions my courses, my school, my professors, my contacts, my family, my calendar, or me. Then search everything you plan to include for email addresses, phone numbers, course ids, calendar ids, tokens, and my school's website hostname, and tell me each hit and what you did with it. Show me the final inclusion list with one line of justification per item, and do not publish until I say go.
```

Read the list against `SCRUB_CHECKLIST.md`. If it is clean:

```text
Go. Publish as a public template and give me the link. Then open the link yourself in a fresh browser window and confirm the preview loads and shows the sixteen skills and two routines.
```

---

## Message 6: draw the system map (for the demo)

Produces an image of the whole architecture with live numbers, plus a trace of
how last night's run actually fanned out. Run it after at least one nightly run.

```text
I want a picture of how you work, for a demo. Do this on your computer and show me the results here.

1. Read ~/vidya/docs/SYSTEM_MAP.md. It contains a Mermaid diagram of the whole system: me, your routines, you as the supervisor, one reader subagent per course, the read-only sources, the Reading JSON handoff, the vidya engine stages (extract, normalize, resolve, diff with the destructive-write guard, review gate, calendar plan, record and commit, digest, graph, safety plan), the state on disk, the two write paths (Google Calendar and Gmail send), Graphiti, and my safety contacts.

2. Before rendering, fill in the live numbers so the picture is about my setup, not a generic one: replace "course 1 / course 2 / course N" with the short ids of my actual courses (one reader box per course, read them from vidya status); put the real count of believed items under each course; put the number of skills and routines you actually have; put "N contacts" in the safety contacts box (the number only, never a name or address); and put the test count from running python3 -m pytest -q in the engine box. If safety check-ins are off, grey out the safety routine, the safety plan stage, the Gmail send box and the contacts box rather than removing them.

3. Render the diagram to a PNG at least 2400 pixels wide with readable text. Try, in order: npx -y @mermaid-js/mermaid-cli -i map.mmd -o map.png -w 2400 -b white; if that is unavailable, open https://mermaid.live in your browser, paste the diagram, and export PNG; if both fail, render the diagram as HTML with the Mermaid CDN script and screenshot it at full size. Save the result as ~/vidya-state/system-map.png and post the image here.

4. Then make a second, smaller picture: a trace of your most recent nightly run as a sequence diagram. Read the run from vidya show and the readings folder for that night, and draw: the routine firing, you launching one reader per course (name them by course id, note which ran in parallel and which were sequential, and roughly how long each took if you can tell from the read_at timestamps), each reader handing back a Reading JSON with its status (ok, empty, error), the engine's plan with the counts it printed (changes, pending removals, unreadable, needs review, approved and blocked operations), each calendar operation you applied and recorded, the commit, and the summary you posted to me. Render it the same way to ~/vidya-state/last-run-trace.png and post it here.

5. Under the two images, write a narration I can read aloud in about 45 seconds: one sentence on what is an LLM (blue), one on what is code (dark), one on the only two places anything is written (red), one on what stops a reader (a login wall) and what happens then, and one on why the safety module uses the same shape. Use the real numbers from step 2. Do not add anything the pictures do not show.
```

If the image is too small to read when posted, send:

```text
Re-render both images at 3600 pixels wide and post them again. Also save the Mermaid source you used as ~/vidya-state/system-map.mmd and ~/vidya-state/last-run-trace.mmd and paste the source of the trace here so I can keep it.
```

---

## Message 7: the big update (for a Vidya that already exists)

One message. Vidya pulls the new engine, installs the nine new skills, re-saves
the ones that changed, then interviews you for each new module one question at
a time. Skip anything by answering "skip". Nothing in it needs editing.

```text
Update yourself from the repository and then set up everything new for me. Do every step in order, report after each in one line, never summarize text you are told to save verbatim, and whenever you need something from me ask one clear question at a time and wait. If I answer "skip" to any module, leave it off and move on.

1. Engine. On your computer: cd ~/vidya && git pull && python3 -m vidya.cli selftest && python3 -m vidya.cli --version. Expect ALL PASS. Then run vidya status with VIDYA_STATE=~/vidya-state and confirm my courses and state are intact. If anything fails, stop and show me.

2. Skills. Re-save these existing skills from ~/vidya/template/skills/ because their text changed: "Setup playbook" (setup-playbook.md), "Safety check-in" (safety-checkin.md), "Package template" (package-template.md). Then save these nine new skills, name = the H1 heading without "Skill: ", instructions = the entire body verbatim: "Lecture notes" (lecture-notes.md), "Assignment coach" (assignment-coach.md), "Opportunity scout" (opportunity-scout.md), "Resume tailor" (resume-tailor.md), "Project builder" (project-builder.md), "Club scout" (club-scout.md), "Coffee chat scheduler" (coffee-chat-scheduler.md), "Cold outreach" (cold-outreach.md), "Calendar concierge" (calendar-concierge.md). Enable all of them for yourself. List all sixteen skill names and confirm each is available.

3. Profile. Read ~/vidya/template/PROFILE.md and replace your title and description with the Title line and the quoted Description block, word for word. If you cannot edit your own profile, print both so I can paste them, and wait for "done".

4. Receipts. Run vidya why on one of my items (pick the next upcoming exam from vidya status) and show me the output, so I can see the receipt format.

5. Sources beyond courses. Ask me, one at a time, whether to watch each of these, and for each yes ask for the page address: my school's registrar or academic calendar (add/drop, withdrawal, grade deadlines); financial aid; housing; any club or program with an application deadline (offer to add several). For each, run vidya add-source <short-id> --name "<name>" --url "<url>" --kind <registrar|aid|housing|club|program>, then read it once with the "Read course" skill and show me what dated items you found before it joins the nightly check. If I am in high school, offer instead: the counseling office deadlines page (SAT/ACT, college applications, FAFSA), summer programs, and my school's Classroom/Schoology/PowerSchool pages.

6. Location in safety alerts. If my safety check-in is on, ask me yes or no: should a missed-check-in alert include where I last was, using Google Maps location sharing? Explain in two sentences that I share my location from my phone with the Google account your browser uses, that you look only when an alert is about to go out, and that the place appears only inside that alert with how old it is. If yes: walk me through turning on sharing on my phone, wait for me to say "shared", confirm you can see it at google.com/maps in your browser, run vidya safety set-checkin --include-location, do one practice read with vidya safety location "<place>" --seen <time> --source google-maps-sharing, and show me vidya safety status. If my safety check-in is off, ask whether I want to set it up now and, if yes, run the "Safety check-in" skill's setup interview.

7. Lecture notes. Ask whether I want lecture notes in Notion (yes / skip). If yes: ask me to connect the Notion plugin, create the "Vidya · Lecture notes" database exactly as the skill describes, then ask me to send you one lecture's material (slides, transcript, or my notes) and produce the first page so I can see the format. Ask which courses, if any, should get notes automatically when new slides appear.

8. Assignment coach. Ask whether I want coaching offered automatically when a new assignment appears (yes / skip / only when I ask). Then ask me to name one current assignment and produce the coaching note for it so I can see the format.

9. Resume and opportunities. Ask whether I want the recruiting modules (yes / skip). If yes, run the "Resume tailor" skill's setup: ask me to upload or paste my current resume, save it as the master resume, then interview me one question at a time for my profile (target roles, term and graduation year, degree level including high school, locations, sponsorship, companies to never apply to, and whether to prepare applications scored 4 and up automatically). Then produce my first gap report against 20 current postings. Then run the "Opportunity scout" skill once now: download the Simplify lists, show me the new postings that fit with scores, and prepare (do not submit) the top three so I can see a filled application stopped at the Submit button. Ask me whether to create a daily 7:00 AM "Opportunity scout" routine.

10. Project builder. If the gap report found gaps, ask whether I want to start a project for the top gap now (yes / later). If yes, run the "Project builder" skill's scope step and stop after I pick an idea.

11. Clubs. Ask whether I want the club scout (yes / skip). If yes: ask for my school's club directory address and my time budget in hours per week, build the directory, add every club with a deadline as a source, and show me the fit report for the top 15.

12. Coffee chats and outreach. Ask whether I want these (yes / skip). If yes: ask for a two-sentence intro paragraph about me and one goal (a company, a team, a research area), then run "Cold outreach" once: a shortlist of up to 10 people with reasons and channels and drafted notes, and stop. Send nothing.

13. Calendar concierge. Ask me for my working hours (earliest start, latest end) and protected times (sleep, practice, work shifts, anything I never want booked over), save them to the profile, then ask me for one calendar change in plain English and show me the operation list before applying it.

14. Finish. Show me: skills (16), routines with next runs, sources watched with kinds, safety status, which modules are on and which I skipped, and everything that still needs me (sign-ins, plugin connections, approvals). Then re-run step 4 of your "Package template" skill only as a dry run: list what would go into the shared template and confirm nothing about my courses, contacts, resume, school or me is in it.
```

If it stalls on any module, send the module number to resume:

```text
Continue from step <N>. Skip nothing else.
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

```text
Why is Midterm 1 on the 16th?
```

```text
Any new internships?
```

```text
Submit all
```

```text
Block Tuesday and Thursday mornings for the project until the midterm
```

```text
Notes for today's CS 201 lecture (attached)
```

```text
How should I approach Homework 3?
```
