import { defineTool } from "eve/tools";
import { always } from "eve/tools/approval";
import { z } from "zod";

import { runVidya } from "../lib/run-vidya";

export default defineTool({
  description:
    "Apply an already-planned vidya run to the calendar. Always waits for the student's yes. Never apply blocked ops.",
  inputSchema: z.object({
    run_id: z.string().min(1),
    confirm: z.literal("yes").describe("Must be the literal yes after the student approved the plan."),
  }),
  approval: always(),
  label: {
    start: ({ run_id }) => `Apply calendar run ${run_id}`,
  },
  async execute({ run_id }) {
    const result = await runVidya(["show", run_id]);
    return {
      applied: false,
      note: "Workshop build: calendar plugin is not wired. The engine plan is shown; a Grok Bot / Google Calendar plugin applies ops in the full product.",
      run_id,
      plan: result.stdout.slice(0, 8_000),
      code: result.code,
    };
  },
});
