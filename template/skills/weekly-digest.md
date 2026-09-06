# Skill: Weekly digest

## When to use
Sunday 6 PM routine, or on request ("what's this week look like?").

## Sequence
1. `export SYLLABOT_STATE=~/syllabot-state && cd ~/syllabot && python3 -m syllabot.cli digest --weeks 1`
2. Send the output as one message. It contains: deadlines in the next seven days by day; what moved during the past week with before/after and source; how many times each course has changed a date this term (the volatility table); pending removals; the needs-review bucket.
3. If the Graphiti plugin is connected, you may add one line from a temporal query, e.g. "Midterm 1 has had two dates this term: Oct 14 (until Sep 6), Oct 16 (since Sep 6)." Only include it if the query actually ran.

## Rules
- Do not editorialize about workload. Facts, dates, sources.
- Do not send the digest anywhere but this conversation.
