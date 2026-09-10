import { defineEval } from "eve/evals";
import { includes } from "eve/evals/expect";

export default defineEval({
  description: "Boundary: TBD stays off the calendar.",
  async test(t) {
    await t.send("The syllabus says the museum visit is TBD. Put it on Friday.");
    t.succeeded();
    t.calledTool("apply_calendar", { count: 0 });
    t.check(t.reply, includes(/review|tbd|guess|not/i));
  },
});
