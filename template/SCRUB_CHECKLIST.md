# Scrub checklist (run before Publish → Public link)

The link is public. Anyone with it sees every included memory, skill and routine.

Search every included field for each pattern and remove or generalize it:

- [ ] Course ids from the LMS: `ou=`, `/courses/<digits>`, `/d2l/home/<digits>`, `context_codes`
- [ ] Course names, section numbers, professor or TA names, email addresses
- [ ] The school's LMS hostname (e.g. `brightspace.<school>.edu`, `<school>.instructure.com`)
- [ ] Calendar ids, event ids, anything from `ledger.json`
- [ ] Tokens and keys: `CANVAS_TOKEN`, iCal feed URLs (they are tokenized), Graphiti server URLs or keys
- [ ] The owner's name, time zone as a personal fact, schedule details
- [ ] Any memory that came from a real conversation about a real course
- [ ] `<REPO_URL>` replaced by the public repository URL in every skill

Things that are fine to include: the six skills as written in `skills/`, the two
routines, the profile text, generic preferences ("list unreadable courses
first").

Prompt to make the Bot do the audit for you (from the plan, section 7):

> Package yourself as a template. First read your memories, skills, routines and plugins and tell me, for each one, whether it is part of this Bot's job or personal/one-off, and why. Then include all instructions for setup and configuration in the template; think through exactly what a user at another school on a different LMS would need to replicate my flow from a fresh computer. Show me the inclusion list with a one-line justification per item before you publish.

If the first pack comes out thin, say so: "the last pack was too thin; write
the actual setup playbook into the template" is the correction that worked.
