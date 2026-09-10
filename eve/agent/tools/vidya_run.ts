import { defineTool } from "eve/tools";
import { z } from "zod";

import { runVidya } from "../lib/run-vidya";

export default defineTool({
  description:
    "Run the deterministic vidya engine: status, why (receipt), plan, extract, selftest, init, digest. Calendar writes are NOT applied here.",
  inputSchema: z.object({
    command: z.enum([
      "status",
      "why",
      "plan",
      "extract",
      "selftest",
      "init",
      "digest",
      "add-source",
    ]),
    query: z.string().optional().describe("For why: the item title or key."),
    readings: z.string().optional().describe("For plan: folder of Reading JSON files."),
    extract_kind: z.enum(["html", "ical", "email"]).optional(),
    file: z.string().optional().describe("For extract: path to a saved page or feed."),
    course: z.string().optional(),
    url: z.string().optional(),
    name: z.string().optional(),
    kind: z.string().optional(),
    timezone: z.string().optional(),
  }),
  label: {
    start: ({ command, query }) => (query ? `vidya ${command} ${query}` : `vidya ${command}`),
  },
  async execute(input) {
    if (input.command === "plan" && !input.readings) {
      return { command: input.command, code: 2, stdout: "", stderr: "plan needs readings: a folder of Reading JSON" };
    }
    if (input.command === "extract" && (!input.file || !input.course)) {
      return { command: input.command, code: 2, stdout: "", stderr: "extract needs file and course" };
    }
    if (input.command === "why" && !input.query) {
      return { command: input.command, code: 2, stdout: "", stderr: "why needs query (title or key)" };
    }
    const args: string[] = [];
    switch (input.command) {
      case "status":
        args.push("status");
        break;
      case "why":
        args.push("why", input.query ?? "");
        break;
      case "plan":
        args.push("plan");
        if (input.readings) args.push("--readings", input.readings);
        args.push("--fake-apply");
        break;
      case "extract":
        args.push("extract", input.extract_kind ?? "html");
        if (input.file) args.push(input.file);
        if (input.course) args.push("--course", input.course);
        if (input.url) args.push("--url", input.url);
        break;
      case "selftest":
        args.push("selftest");
        break;
      case "init":
        args.push("init", "--timezone", input.timezone ?? "America/New_York");
        break;
      case "digest":
        args.push("digest", "--weeks", "1");
        break;
      case "add-source":
        args.push(
          "add-source",
          input.course ?? "course",
          "--name",
          input.name ?? input.course ?? "course",
        );
        if (input.url) args.push("--url", input.url);
        if (input.kind) args.push("--kind", input.kind);
        break;
    }
    const result = await runVidya(args);
    return {
      command: input.command,
      args,
      code: result.code,
      stdout: result.stdout.slice(0, 12_000),
      stderr: result.stderr.slice(0, 2_000),
    };
  },
});
