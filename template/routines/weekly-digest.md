# Routine: Weekly digest

> Every Sunday at 6:00 PM in <owner time zone>, run the "Weekly digest" skill and post the result in this conversation. Do not write to the calendar during this routine.

- **Owning Bot:** Syllabus
- **Schedule:** weekly, Sunday 18:00, owner's time zone
- **Input:** `~/syllabot-state` (belief, history, needs-review)
- **Expected result:** one message: next seven days of deadlines, what moved this week with sources, volatility per course, pending removals, review bucket
- **Approval boundary:** read-only
- **Missing source:** if the state directory is missing, post "setup required" and stop
