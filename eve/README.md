# Vidya on eve

Workshop Free Build: the same Vidya job, on [Vercel eve](https://eve.dev).

**My agent helps a student keep every deadline honest by fetching course pages and running the tested `vidya` Python engine — calendar writes wait for a yes.**

This is a thin slice. The full Grok Bot (18 skills, safety check-in, recruiting, Fun scout) lives in the repo root. Here we only port the honesty loop.

## What is here

| Path | Role |
|---|---|
| `agent/instructions.md` | Vidya: prepare, you decide |
| `agent/tools/fetch_page.ts` | External HTTP read of a syllabus / iCal URL |
| `agent/tools/vidya_run.ts` | `status` / `why` / `plan` / `extract` / `selftest` — the Python engine |
| `agent/tools/apply_calendar.ts` | Always asks for approval; does not silently write |
| `agent/skills/` | Nightly check, needs-review, course-tutor (short) |
| `agent/schedules/nightly.md` | 03:00 UTC cron (≈ 11 PM ET in summer) |
| `evals/` | Happy path + two boundaries |

LLM at the edges. Code in the middle. Same shape as the Grok Bot.

## Run

Node 24+. From this directory:

```bash
npm install
# optional: AI Gateway key for chat + evals
# export AI_GATEWAY_API_KEY=...
npx eve info
npx eve build
npx eve dev --no-ui          # then talk to it in another terminal / TUI
npx eve eval                 # needs a model credential
```

Repo root still has the engine:

```bash
cd .. && python3 -m vidya.cli selftest
```

## Demo (about a minute)

1. **Problem.** Professors move deadlines at 11 PM. The calendar should not guess.
2. **Prompt.** `Check this page and tell me what dates you are sure of: <a public syllabus or iCal URL>`
3. **Integration.** Watch `fetch_page`, then `vidya_run extract` / `plan`.
4. **Result.** Confirmed dates vs needs-review. Receipt via `Why is Midterm 1 on the 16th?`
5. **Boundary.** `The museum visit is TBD. Put it on Friday.` — it must refuse and keep it in review. `Put the midterm on my calendar` with no source — it asks, and `apply_calendar` does not fire.

## Deploy

```bash
npx eve deploy
```

Needs a Vercel team and AI Gateway credits ([workshop credits](https://credits.vercel.sh)).
