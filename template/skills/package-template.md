# Skill: Package template

How this Bot packages itself for sharing. A template is a blueprint, not a
clone: it must let a stranger at another school replicate the flow, and it must
contain nothing about the owner.

## Sequence
1. **Audit out loud.** Read your memories, skills, routines and plugins and say what each one is:
   - Memories: keep only durable, generic working preferences (e.g. "summaries list unreadable courses first"). Leave out every course name, URL, professor, calendar id, and anything about the owner's schedule.
   - Skills: keep all sixteen as written in the repository (Setup playbook, Read course, Nightly syllabus check, Needs-review triage, Weekly digest, Safety check-in, Lecture notes, Assignment coach, Opportunity scout, Resume tailor, Project builder, Club scout, Coffee chat scheduler, Cold outreach, Calendar concierge, Package template). Leave out one-off skills.
   - Routines: keep Nightly syllabus check and Weekly digest with their schedule text; the installer will confirm time zone. Leave out the Safety check-in routine (it is created per owner, after they opt in) and any routine that mentions a real contact.
   - Plugins: keep Google Calendar. Gmail and Graphiti are optional and named as such in the playbook. Leave out anything else.
2. **Check the playbook is complete.** Re-read `Setup playbook` and ask: could a person on Canvas at another university get to a first course read in ten minutes with only this text? If any step assumes something on this computer (a clone, a state dir, a login), the playbook must create or ask for it.
3. **Scrub.** Search every field you are about to include for: course ids, `ou=`, `courses/<number>`, calendar ids, tokens, `CANVAS_TOKEN`, email addresses, phone numbers, names of professors, names of safety contacts or family, the owner's name, internal URLs. Remove or generalize each hit. Confirm the clone URL in Setup playbook is the public repository (`https://github.com/vinilpolepalli/vidya`).
4. **Justify every inclusion** in one line each and show the list to the owner before publishing.
5. Publish as a **Public link**. Say clearly to the owner that the link exposes everything included.

## Rules
- Never include anything that identifies the owner, their school, or their courses.
- Never include state files, readings, or the fake calendar.
- Never include a plugin that requires the owner's own paid key unless the playbook tells the installer to bring their own.
