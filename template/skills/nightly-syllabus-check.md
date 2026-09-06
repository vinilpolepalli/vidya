# Skill: Nightly syllabus check

The supervisor loop: gather, launch, review, merge, report. Runs as the 11 PM
routine or on demand ("check my courses now").

## Inputs
- `~/syllabot` (engine) and `~/syllabot-state` (state). `export SYLLABOT_STATE=~/syllabot-state`; run from `~/syllabot`.
- Google Calendar plugin connected.
- Optional: Gmail plugin (read-only), Graphiti plugin.

## Sequence

### Gather
1. `syllabot status`. Note the course list, pending removals, and any `uncommitted runs` line (the engine will recover those itself on the next `plan`).
2. Folder for tonight: `~/syllabot-state/readings/<YYYY-MM-DD>/`.

### Launch
3. Produce a Reading for every course with the "Read course" skill.
   - Default: sequentially, one course at a time.
   - Parallel: if reader Bots exist (one per course, each with the "Read course" skill), message each one with its course id, URL and the output folder, and wait for all of them to report the file path. Do not wait more than 15 minutes for any reader; treat a silent reader as `status: error`.
4. Optional email pass (only if Gmail is connected): search for messages since yesterday from course instructors or TAs whose text contains a date or a change word (moved, rescheduled, extended, postponed, now due). For each, write `<folder>/<course>-email-<n>.eml` containing the headers `From:`, `Subject:`, `Date:` and the body, then `syllabot extract email <file> --course <id> --read-at <ts> --out <folder>/<course>-email-<n>.json`. The engine treats email as partial: it can move or add, never remove.

### Review
5. `syllabot plan --readings <folder>`. Read the printed summary. It lists changes, pending removals, unreadable courses, review items, and the approved and blocked calendar operations. The run id is printed at the end.
6. Sanity read before applying: does each change name a source? Does any change look like page noise? If the summary itself looks wrong (for example forty changes in one course), stop and message the owner instead of applying.

### Merge
7. Apply **only** the approved operations, in order, through the Google Calendar plugin:
   - `create`: new event with `summary`, `start`, `end`, `description`, color `color_id` (11 tomato, 7 peacock). All-day ops give date-only `start`/`end` where `end` is already exclusive; timed ops give RFC 3339 with offset. Then `syllabot record <run> --key "<key>" --op create --event-id "<new id>" --status ok`.
   - `update`: update event `event_id` with the same fields. Then `syllabot record <run> --key "<key>" --op update --event-id "<event_id>" --status ok`.
   - `delete`: delete event `event_id`. Then `syllabot record <run> --key "<key>" --op delete --event-id "<event_id>" --status ok`.
   - If a plugin call fails: `syllabot record <run> --key "<key>" --op <op> --status failed --error "<message>"` and continue with the next op.
   Record immediately after each call, before the next one. This is what makes a crash mid-way safe.
8. `syllabot commit <run>`.
9. Optional graph: `syllabot graph <run> --out <folder>/episodes.jsonl` and post each line as an episode to the Graphiti plugin (`add_memory` with the given `name`, `episode_body`, `group_id`).

### Report
10. One message to the owner: the summary from step 5, then which operations were applied and which failed. Always include the three honest sections even when empty: unreadable courses (and why: login wall, empty page, silent reader), pending removals (with the "will remove if still gone tomorrow" wording), needs review (with the reason). If a course was unreadable because of a login wall, ask the owner to take over the computer and sign in; do not retry by yourself.

## Rules
- Never apply a blocked operation. Never create, edit or delete an event outside the approved list.
- Never delete anything the plan did not mark as a confirmed removal.
- Never send email.
- If `plan` shows the same course unreadable three nights in a row, say so prominently.

## Return
The owner message from step 10. If nothing changed, still send it: "No changes in N courses. 1 item needs review. All courses read."
