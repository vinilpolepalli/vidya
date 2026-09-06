# Routine: Safety check-in (optional)

Create only after the owner has turned safety check-ins on with the "Safety
check-in" skill. Ask the Bot:

> Every day, every 30 minutes from <check-in time> until <check-in time + grace + 1 hour> in <owner time zone>, run the "Safety check-in" skill: run `vidya safety plan` and act only on what it approves. Post an owner reminder in this conversation; send any other approved message through Gmail exactly as written and record it. If the plan approves nothing, post nothing. Never message anyone not on the approved list. If the engine or state directory is missing, post "setup required" once and stop.

With the defaults (9:00 PM due, 90 minutes grace) the window is 9:00 PM to 11:30 PM, i.e. runs at 9:00, 9:30, 10:00, 10:30, 11:00, 11:30. If the app only allows one time per routine, create one routine per run time; the engine is idempotent so extra runs are harmless.

- **Owning Bot:** Vidya
- **Schedule:** daily, every 30 minutes in the evening window, owner's time zone
- **Input:** `~/vidya-state/safety/` (check-ins, sent log, outbox) and the safety section of `config.json`
- **Expected result:** usually nothing; at the due time one reminder to the owner; after the grace period one message per contact; after a late check-in one all-clear per alerted contact
- **Approval boundary:** send only the messages `vidya safety plan` approves, to the addresses it names, verbatim; record each
- **Missing source:** if Gmail is disconnected, record the send as failed and tell the owner once; never fall back to another channel

Test run: set the check-in due to two minutes from now with `vidya safety set-checkin --due HH:MM --grace 2`, run the routine's Test run three times over the next five minutes with the owner watching, confirm reminder then alert then (after the owner replies) all-clear, then restore the real time. Use the owner's own address as the only contact during the test.
