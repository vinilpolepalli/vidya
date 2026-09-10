---
description: Use when the student says check my courses now, run the nightly check, or a schedule fires the syllabus watch.
---

# Nightly syllabus check

1. `vidya_run status`. If there is no state, `vidya_run init` then add sources they name.
2. For each watched URL: `fetch_page`. If login_wall or status >= 400, mark unreadable. Do not delete anything.
3. Save or extract readings with `vidya_run extract`.
4. `vidya_run plan` (always `--fake-apply` from the tool). Read approved vs blocked.
5. Report: what moved, needs-review, unreadable, pending removals. Ask before `apply_calendar`.
