import { spawn } from "node:child_process";
import { resolve } from "node:path";

export function engineRoot(): string {
  return process.env.VIDYA_ENGINE_ROOT ?? resolve(import.meta.dirname, "../../..");
}

export function stateRoot(): string {
  return process.env.VIDYA_STATE ?? resolve(engineRoot(), "eve/.vidya-state");
}

export function runVidya(args: string[], opts?: { input?: string }): Promise<{
  code: number;
  stdout: string;
  stderr: string;
}> {
  return new Promise((done, reject) => {
    const child = spawn("python3", ["-m", "vidya.cli", "--state", stateRoot(), ...args], {
      cwd: engineRoot(),
      env: { ...process.env, VIDYA_STATE: stateRoot() },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
    });
    if (opts?.input) child.stdin.end(opts.input);
    else child.stdin.end();
    child.on("error", reject);
    child.on("close", (code) => {
      done({ code: code ?? 1, stdout: stdout.trim(), stderr: stderr.trim() });
    });
  });
}
