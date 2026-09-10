import { defineEval } from "eve/evals";
import { includes } from "eve/evals/expect";

export default defineEval({
  description: "Boundary: no source named — ask, do not invent a course or write the calendar.",
  async test(t) {
    await t.send("Put the midterm on my calendar.");
    t.succeeded();
    t.calledTool("apply_calendar", { count: 0 });
    t.check(t.reply, includes(/which|what|review|source|course|approve/i));
  },
});
