# Graphiti as the temporal layer

Graphiti (by Zep; not Graphify, not graphite.dev) gives every fact a validity
window. A syllabus is a set of facts that change: the midterm was Oct 14, now it
is Oct 16. Graphiti stores that as an edge with history instead of overwriting
it, which is what turns "the diff" into "how many times has this professor moved
a deadline" and "which course has the most volatile schedule".

The engine does not need Graphiti. `vidya digest` answers the volatility
question from local run history. Graphiti is the enhancement: cross-course
temporal queries, and a shared graph if several readers write to one place.

## What vidya produces

`vidya graph <run-id> --out episodes.jsonl` writes one JSON object per line:

```json
{"uuid": "…", "name": "moved: Midterm 1 (data-structures)",
 "episode_body": "In the course CS 201 Data Structures (data-structures), the exam 'Midterm 1' was scheduled for 2026-10-14T11:00:00-04:00 and is now scheduled for 2026-10-16T11:00:00-04:00. Observed on 2026-09-06. Source: https://…",
 "source": "text", "source_description": "vidya nightly diff, run 20260906-230412",
 "reference_time": "2026-09-06T23:04:12-04:00", "group_id": "vidya"}
```

- One `text` episode per change (moved / added / removed / reworded).
- One `json` episode per course per night with the full belief snapshot, so the
  graph also has the static picture, not only deltas.
- `uuid` is deterministic (`uuid5` of run id + key + change type). Re-posting a
  run is idempotent.
- `group_id` namespaces one student's graph. One server can hold many students
  without mixing them, which is what makes a shared template viable.

These fields map one-to-one onto Graphiti's `add_memory` MCP tool (and
`graphiti.add_episode` in graphiti-core): `name`, `episode_body`, `source`,
`source_description`, `reference_time`, `group_id`, `uuid`.

## Standing it up (your own instance)

```bash
git clone https://github.com/getzep/graphiti && cd graphiti/mcp_server
cp .env.example .env        # set OPENAI_API_KEY (or another supported provider)
docker compose up           # FalkorDB + Graphiti MCP server, HTTP at http://localhost:8000/mcp/
```

Grok Bot only speaks **remote HTTP MCP**. `localhost` on your laptop is not
reachable from the Bot's cloud computer, so the server has to sit behind a public
HTTPS URL (a small VM, a tunnel such as Cloudflare Tunnel or Tailscale Funnel, or
a container host). Then in Grok Bot: tell the Bot "Add this MCP server:
https://<your-host>/mcp/" (or Settings → Plugins → custom server), and the
nightly skill can post each JSONL line with `add_memory`.

Without hosting: run the MCP server locally with `--transport stdio`, or use
`push_with_graphiti_core` from `vidya/graph.py` (`pip install "vidya[graph]"`)
against a local FalkorDB, ingest the episodes, and query. That is a legitimate
component for the demo as long as the post says the graph runs alongside the
bot today and the hosted wiring is next.

## Two things to settle before the template ships

1. **Whose key.** Graphiti calls an LLM on every ingest for entity extraction.
   If the template points installers at your server with your key, you pay for
   every stranger's syllabi, and the bill scales with how well the post does.
   The setup playbook therefore says: bring your own instance and key, or skip
   the graph. Never ship a server URL or key in the template.
2. **Hosted or not by the 13:00 abort.** If the public HTTPS endpoint is not up
   by then, run stdio or graphiti-core locally, ingest the fixture run, record
   the temporal query, and describe it honestly. Judges can install the
   template; a hidden gap is found in a minute, a stated one costs nothing.

## Queries that fall out of the data model

- History of one item: search facts for `'Midterm 1' data-structures scheduled` →
  two edges with validity windows (Oct 14 valid until Sep 6; Oct 16 valid since).
- Volatility: count `now scheduled for` facts per course.
- Cross-course week view: facts whose scheduled date falls in a window.

`vidya digest` produces the first two from local state as a fallback so the
weekly message never depends on the graph being up.
