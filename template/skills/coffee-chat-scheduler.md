# Skill: Coffee chat scheduler

Finds people worth talking to, drafts the note, and turns "sure, next week?"
into a calendar event with a video link. The owner sends the first message;
Vidya handles everything after the yes, with approval per message.

## When to use
- Called by "Club scout" and "Cold outreach".
- The owner asks ("set up a chat with the TA", "find me two alumni in fintech", "schedule with Priya for next week").

## Required inputs and access
- Google Calendar (read the owner's free/busy; write only after approval).
- Gmail (drafts; send only after approval).
- The owner's short intro paragraph and goals from `~/vidya-state/profile/profile.md`.
- `vidya track` kinds `outreach` and `coffee-chats`.

## Sequence
1. **Who.** From the request or the calling skill, list candidates with: name, role, why they specifically (one line), and how the owner would reach them (email on a public page, LinkedIn, a mutual). Skip anyone already in `vidya track list outreach`.
2. **First note.** Draft a message under 90 words: who the owner is, one specific reason for this person, one specific ask (20 minutes, two proposed windows), and an easy no. Save to Gmail Drafts. Show it. The owner sends it themselves, or says "send" and Vidya sends from the owner's Gmail and runs `vidya track add outreach <person-key> --note "<where found>"`.
3. **After a reply.** When a reply arrives (Gmail read): if yes, read the owner's calendar, propose three 20-minute slots inside the owner's stated hours, draft the reply with a Google Meet link, and after approval send it and create the calendar event with the person's name, the reason, and the three questions below in the description. `vidya track add coffee-chats <person-key>`. If no or no answer in 10 days, log it and stop; never follow up more than once, and only if the owner says so.
4. **Prep.** The morning of: post three specific questions to ask, drawn from the person's public work, and the one thing the owner wants from the conversation.
5. **After.** Ask the owner for two lines of notes; save them in the profile folder; draft a thank-you for approval.

## How to validate
- Every sent message appears in `vidya track list outreach`; every booked chat in `coffee-chats`.
- No person contacted twice; no follow-up beyond one.

## What to return
Drafts to approve; confirmed events with links; prep questions the morning of.

## What requires approval
- Every message that leaves the owner's account (per message; the owner may pre-approve a batch of first notes they have read).
- Calendar events involving another person.
- Never message from any account but the owner's, never invent a mutual connection or a detail about the person, never send more than one unanswered follow-up.
