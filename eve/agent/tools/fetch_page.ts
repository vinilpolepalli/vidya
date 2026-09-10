import { defineTool } from "eve/tools";
import { z } from "zod";

export default defineTool({
  description:
    "Fetch a live course, registrar, or iCal URL over HTTP. Read-only. Use this before vidya_run extract. Never send credentials.",
  inputSchema: z.object({
    url: z.string().url(),
  }),
  label: {
    start: ({ url }) => `Fetch ${url}`,
  },
  async execute({ url }) {
    const response = await fetch(url, {
      redirect: "follow",
      signal: AbortSignal.timeout(15_000),
      headers: { "user-agent": "vidya-eve/0.1 (read-only syllabus watcher)" },
    });
    const text = await response.text();
    return {
      url: response.url,
      status: response.status,
      content_type: response.headers.get("content-type"),
      bytes: text.length,
      excerpt: text.slice(0, 6_000),
      login_wall: /password|sign in|log in|captcha|mfa|two-factor/i.test(text.slice(0, 4_000)),
    };
  },
});
