# Skill: Fun scout

The good part of the week. Every Thursday Vidya finds what is on: your school's
games, concerts by artists you actually listen to, campus events, and the
parties people are talking about. You pick; it puts them on your calendar,
walks a ticket to the Pay button, and stops. The safety check-in knows which
nights you are out.

## When to use
- The "Fun this week" routine (Thursday 4:00 PM), and again Saturday morning for last-minute additions.
- The owner asks ("what's going on this weekend?", "is there a game Saturday?", "get me a ticket to the Friday show", "who's playing near me next month?").

## Required inputs and access
- `~/vidya-state/profile/profile.md`, section `fun` (collected in setup): home city/campus, radius in miles, kinds of things they like (offer: home games, concerts, comedy, campus events, Greek life / parties, club nights, cultural, free stuff), nights that are off-limits (from Calendar concierge's protected times), max ticket price, monthly fun budget, and whether the owner is in high school (then: school events, games and all-ages shows only; no parties, no 18+/21+ listings).
- Browser signed in as the owner on: **Spotify** (open.spotify.com; the **Live Events** page at open.spotify.com/concerts ranks nearby concerts by the owner's listening), the **school athletics** site and its student ticket portal, the **campus events calendar** (Localist / CampusGroups / Engage / the school's own page), and whatever the owner's campus uses for parties (Instagram pages of chapters and orgs, Partiful, Posh, Eventbrite). The owner signs in via takeover; Vidya never stores passwords.
- Google Calendar (write only through "Calendar concierge" after the owner picks).
- `vidya track` kinds: `fun-suggested`, `fun-added`, `tickets`.

## Setup (first time)
1. Ask the profile questions above one at a time. Ask the owner to sign in to Spotify in the browser and open open.spotify.com/concerts once so the page shows their personalised list; confirm it renders.
2. Ask for the athletics schedule page and the student ticket portal address; confirm which sports they care about.
3. Ask which campus events calendar and which Instagram / Partiful / Posh pages to watch for parties (the owner names them; Vidya does not go looking for parties on its own).
4. Save everything to `profile.md`. Run the weekly scan once now and show the result.

## Sequence (weekly scan)
1. **Window.** Thursday scan covers Thursday to next Wednesday; Saturday scan covers the weekend.
2. **Sports.** Read the athletics schedule for the owner's sports in the window: opponent, home/away, date, time, venue, and whether student tickets are free with ID, claimable, or paid (read the ticket portal). Away games count only if the owner said so.
3. **Concerts.** Open Spotify Live Events; read every concert in the radius and window: artist, venue, date, price if shown, and the "because you listen to" line. Rank by how much the owner listens (top artists first). Then check each concert's ticket page for real price and availability. If Spotify shows nothing, fall back to the venue calendars the owner named.
4. **Campus events.** Read the campus calendar for the window: talks, screenings, cultural nights, free food, club showcases. Keep the ones matching the owner's kinds.
5. **Parties and Greek life.** Only from the pages the owner named, only if the owner is not in high school. Read the public posts: what, when, where, who is invited (open / invite / list), cost, and the RSVP link. Never DM anyone, never request an invite, never RSVP.
6. **Dedupe and filter.** Skip anything in `vidya track list fun-suggested` for this window. Drop anything on a protected night, over the max ticket price, or that collides with an exam within 24 hours (`vidya status`); show those in a separate "you have Friday off-limits / exam Monday" line rather than silently hiding them.
7. **Shortlist.** Save `~/vidya-state/fun/<date>.md` and post at most ten items, grouped Sports / Concerts / Campus / Parties, one line each: what, when, where, price, why it fits ("your #3 artist this year", "home opener, students free"). `vidya track add fun-suggested <key>` for each, key = `<date>:<slug>`. End with: "Reply with the numbers you want on your calendar, and 'ticket' next to any I should buy."

## Sequence (after the owner picks)
8. **Calendar.** For each picked item, hand "Calendar concierge" one operation: title "<event> · <venue>", start/end, location, description with the link and the reason line, colour grape. The concierge shows the list; the owner approves; `vidya track add fun-added <key>`.
9. **Tickets.** For each item marked "ticket": open the official ticket source (student portal for games; the artist's linked ticket page for concerts; no resale sites unless the owner names one). Pick the cheapest option that matches the owner's stated section/quantity, add to cart, fill name and email from the profile, and **stop at the payment step**. Screenshot the cart with the total to `~/vidya-state/fun/tickets/<key>/cart.png`. Post: "Ready to pay: <event>, <qty> × <section>, total $<x> (budget left this month $<y>). Say 'pay' to complete." Only after "pay": complete the purchase using the payment method already saved in the owner's account or take over for the owner to enter it (Vidya never types card numbers it was given in chat), screenshot the confirmation, `vidya track add tickets <key> --note "<event> — $<total> — <confirmation>"`, and attach the confirmation to the calendar event via the concierge.
10. **Tell the safety check-in.** For each picked item, run `vidya safety plan-note <YYYY-MM-DD> "<short title, e.g. Sigma Chi mixer, ends late>"`. That night the check-in reminder mentions the plan and the owner can say "check in later tonight".
11. **Group.** If the owner says "invite Priya and Dev", draft one message with the event link for the owner to send; do not send it.

## How to validate
- Every suggested item has a source link and a real date within the window; nothing suggested twice in a window.
- No calendar event was created without the owner picking it; no purchase without "pay"; every purchase in `vidya track list tickets` with its total.
- Monthly spend (sum of ticket notes this month) stays under the budget; if a purchase would exceed it, say so and do not proceed.

## What to return
Thursday: the shortlist. After picks: the calendar events with links; for tickets, the "ready to pay" line, then the confirmation.

## What requires approval
- Every purchase, individually, with the total shown.
- Every calendar write (via the concierge).
- Never DM, RSVP, request invites, or post on the owner's behalf; never use resale sites the owner did not name; never store payment details; never suggest 18+/21+ or party listings to a high-school owner.
