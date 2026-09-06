# Routine: Fun this week (optional)

Create after the owner has run the "Fun scout" skill's setup. Ask the Bot:

> Every Thursday at 4:00 PM and every Saturday at 10:00 AM in <owner time zone>, run the "Fun scout" skill's weekly scan and post the shortlist in this conversation. Suggest at most ten items, grouped Sports / Concerts / Campus / Parties, and skip anything already suggested this window. Do not add anything to the calendar and do not buy anything during the routine; wait for my picks in this conversation. If Spotify, the athletics site or the campus calendar needs a login, say which one and stop; do not sign in.

- **Owning Bot:** Vidya
- **Schedule:** Thursday 16:00 and Saturday 10:00, owner's time zone
- **Input:** Spotify Live Events, the athletics schedule and student ticket portal, the campus events calendar, the party/Greek pages the owner named, `profile.md` (fun section), `vidya status` for exam collisions, `vidya track list fun-suggested`
- **Expected result:** one shortlist message; nothing written, nothing bought
- **Approval boundary:** read-only during the routine; calendar writes and purchases happen only after the owner replies, each shown first
- **Missing source:** name the source that failed and continue with the others; never sign in

Test run once with the owner watching: expect a shortlist (or "nothing in the window") and no calendar change.
