import { defineEval } from "eve/evals";
import { includes } from "eve/evals/expect";

export default defineEval({
  description: "Happy path: a receipt question hits the vidya engine.",
  async test(t) {
    await t.send("Why is Midterm 1 on the 16th? Use the vidya engine.");
    t.succeeded();
    t.calledTool("vidya_run");
    t.check(t.reply, includes(/midterm|receipt|why|review|engine/i));
  },
});
