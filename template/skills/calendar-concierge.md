# Skill: Calendar concierge

Natural-language changes to the owner's own calendar: "move my gym block to 7",
"block Tuesday and Thursday mornings for the project", "put a study session
before every exam this month". Vidya interprets, shows the exact operations,
and applies them only after a yes. It never edits the events the nightly check
manages.

## When to use
- Any request that changes the calendar and is not a course deadline ("move", "block", "add", "cancel", "reschedule", "find me time").
- Other skills asking for time: "Assignment coach" work sessions, "Project builder" milestones, "Coffee chat scheduler" slots.

## Required inputs and access
- Google Calendar plugin (read all calendars; write to the owner's personal calendar only).
- `VIDYA_STATE=~/vidya-state` for `vidya status` (exam and deadline dates) and the owner's working hours in `profile.md` (collect once: earliest start, latest end, protected times like sleep, practice, work shifts).

## Sequence
1. **Interpret.** Turn the request into a list of concrete operations: create / move / delete, title, start, end, recurrence, calendar. Resolve relative language against today in the owner's time zone ("next Thursday" is the coming one; "this weekend" is the nearest Saturday and Sunday). If anything is ambiguous, ask one question; do not guess.
2. **Check.** For each operation: does it collide with an existing event? Does it fall outside working hours or inside protected time? Is it within 24 hours of an exam or deadline (from `vidya status`)? Note each issue next to the operation.
3. **Protect the managed events.** Any event whose description contains `vidya-key:` belongs to the nightly check. Never move, edit or delete it here. If the owner asks to change a deadline, explain that the page is the source of truth and offer "Needs-review triage" if the page is wrong.
4. **Show, then apply.** Post the operation list with the issues ("moves Gym to Tue 7:00–8:00 PM; overlaps Study: CS 201 by 30 min"). Wait for a yes, a change, or a no. Apply exactly the approved list through the plugin, then post what was done with links.
5. **Study sessions before exams.** When asked, for each exam in the window: propose N sessions of the requested length in the days before, avoiding collisions and protected time, titled "Study: <exam> (<course>)", with the exam's `vidya why` receipt link in the description. These are the owner's events, not managed ones, so they carry no `vidya-key:`.

## How to validate
- Every applied operation was in the shown list.
- No event with `vidya-key:` was touched.
- No new event lands in protected time without the owner explicitly overriding.

## What to return
The operation list before; the applied list with links after.

## What requires approval
- Every operation that writes (approval of the list is enough; no silent changes).
- Deleting anything with attendees.
- Never touch managed events, never accept invitations on the owner's behalf, never write to a calendar the owner did not name.
