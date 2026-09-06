# Skill: Safety check-in

Optional. Off until the owner turns it on. A nightly "are you good?" with a
dead-man's switch: if the owner does not check in by the deadline, the people
they named get one message; if they check in late, those people get one
all-clear. The owner can also ask me to pass a message to a contact.

I cannot see the owner's phone or location. Anything about where they are comes
only from the owner (a note, or a place they choose to share) and is never
inferred.

## When to use
- The "Safety check-in" routine (runs every 30 minutes in the evening window).
- The owner says anything that sounds like a check-in ("I'm home", "all good",
  "checking in", "back at the dorm"), at any time.
- The owner asks to message a contact ("tell mom I landed", "let dad know I'm
  staying at Priya's").
- The owner asks to set it up, add or remove a contact, change the time, or turn
  it off.

## Required inputs and access
- Engine at `~/vidya`, state at `~/vidya-state` (`export VIDYA_STATE=~/vidya-state`).
- Gmail plugin connected, **send** permission, only for this skill. Messages go
  from the owner's own mailbox to addresses the owner added.
- Contacts the owner has told me have agreed to receive messages.

## Setup (first time, when the owner asks)
1. Ask, in one message: their first name as contacts know it; each contact's name, relationship, and email (or a carrier text-to-email address if their carrier still offers one, e.g. `number@vtext.com`); whether each contact has agreed to receive these; the nightly check-in time and how long to wait before contacting anyone (default 9:00 PM, 90 minutes); which days.
2. For each contact that has agreed: `vidya safety add-contact <id> --name "<name>" --address <address> --relationship <parent|guardian|sibling|friend> --consented`. Refuse to add anyone the owner has not confirmed agreed.
3. `vidya safety set-checkin --due <HH:MM> --grace <minutes> --days <mon,...>`. Then `vidya safety enable --owner-name "<first name>"`.
4. Optional: `vidya safety set-share --contacts <ids> --day sun --time 18:00` sends chosen contacts one email a week with the next seven days of exams and deadlines. Only if the owner asks.
5. Optional: `vidya safety set-checkin --include-location`. Only if the owner asks, and explain: the only place I can name is one the owner tells me or shares with me; it appears only inside a missed-check-in alert. If the owner wants it automatic, walk them through **Google Maps location sharing**: on their phone, Google Maps → profile → Location sharing → share with the Google account this computer's browser is signed into, "until you turn this off". Then, only when an alert is about to go out (step 3 below approves a `missed_checkin`), open https://www.google.com/maps and the Location sharing panel in the browser, read the owner's last place and how long ago it was updated, and record it before sending: `vidya safety location "<place as shown>" --seen <ISO time it was updated> --source google-maps-sharing`. Then run `vidya safety plan` again so the alert body includes it. Never look at the location at any other time, never record it as a check-in, never put it anywhere but the alert.
6. Show `vidya safety status` and read it back. Send one test message to the owner's own address and confirm it arrived, so the Gmail path is proven before a real night.

## Sequence (every routine run, and whenever the owner speaks)
1. If the owner just said something that counts as a check-in: `vidya safety checkin --note "<their words, short>"`. Tell them it is logged in one line. If an alert already went out tonight, the plan below will produce the all-clear.
2. If the owner asked to pass a message: `vidya safety say <contact-id> "<exact text>"`. Do not rewrite it.
3. `vidya safety plan`. It prints notes and, if anything may be sent, the approved messages as JSON with `key`, `kind`, `to_address`, `subject`, `body`. If it approves a `missed_checkin` and location in alerts is on, do the Maps read from setup step 5 first, then run `plan` again and use that output.
4. For each approved message, in order:
   - `kind: owner_reminder` → post `body` in this conversation (the owner's phone gets the notification). Do not email it.
   - any other kind → send one email through Gmail: to `to_address`, subject `subject`, body `body`, verbatim. No additions, no signature beyond what is in the body.
   - Immediately after: `vidya safety record <key>` (or `--status failed --error "<message>"`). Failed sends are retried on the next run; successful ones never repeat.
5. If the plan printed `blocked:` lines, mention them to the owner once.

## How to validate
- `vidya safety plan` run twice in a row approves nothing the second time.
- `vidya safety status` shows the sent log with today's keys.
- The owner received the reminder at the due time in this conversation.

## What to return
- On a routine run with nothing to send: nothing (do not post "nothing to send" every 30 minutes).
- When a reminder was posted: just the reminder.
- When contacts were messaged: one line to the owner, "I couldn't reach you by <time>, so I let <names> know. Reply with anything and I'll send them an all-clear."
- When an all-clear went out: "Logged. I told <names> you're okay."

## What requires approval
- Adding a contact (the owner must confirm the person agreed).
- Turning on location in alerts or the weekly schedule share.
- Anything outside the approved list. I never message a contact on my own judgement, never add a contact myself, never send from any account but the owner's, never message anyone but the owner and the listed contacts, and never send when `vidya safety plan` approves nothing.
