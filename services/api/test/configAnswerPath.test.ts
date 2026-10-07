/**
 * T-0288 rv3 B1 (part 2): a CONTENT PIN over every src file on the GET /config answer path, the T-0273 pattern
 * (whole-file sha256, CRLF normalized). index.ts is the dispatcher (default.fetch, ROUTES' /config entry, the Env it
 * hands on); config.ts computes the body; killSwitch.ts is its planning_paused source; quota.ts is the quota display's
 * source (dailyQuota, DAILY_PLAN_QUOTA). Those three import nothing else from src. Any edit to any of them - an unpause
 * gated on the request by ANY spelling, a new import, a reformatting - fails `the /config answer path is exactly the
 * approved bytes` by name; approving it means changing ANSWER_PATH in the same diff, which the reviewer sees.
 *
 * The rest of src runs only when index.ts imports it, at module load, with no request in hand: it can reach a /config
 * answer only by changing shared runtime state the answer path uses - an intrinsic (String.prototype.endsWith,
 * JSON.stringify, URL, Request.prototype's url getter, Object.prototype.hasOwnProperty) or a global. The second test
 * closes that by behaviour, spelling-independent: it snapshots every global and every own property of every global and
 * of its prototype (descriptor identity: value, getter, setter, flags; and each object's [[Prototype]]), loads the
 * shipped worker, and requires the snapshot unchanged.
 */
import { describe, expect, it } from "vitest";
import { changed, snapshot } from "./intrinsicsSnapshot";

const FILES = import.meta.glob(["../src/index.ts", "../src/config.ts", "../src/killSwitch.ts", "../src/quota.ts"],
  { query: "?raw", import: "default", eager: true }) as Record<string, string>;

const ANSWER_PATH: Record<string, string> = {
  "../src/config.ts": "d10ed3d7229dc875ae9e8f45ec19d3e9715f2bf71a3e50f8cc077825078bea71",
  "../src/index.ts": "fe1d4e74961a6b977cfde631eca532aa62ca2241a938897c756d61e2506b1ab1",
  "../src/killSwitch.ts": "434d34cb4c3770a3a5eedb019ab61b0f801777ae6c4ef742b565001490eec7a4",
  "../src/quota.ts": "779793e26a0e7928b379813c4691ba0861600d35a95a3336acb23aa879a72174",
};

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text.replace(/\r\n/g, "\n")));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

describe("the GET /config answer path (T-0288 rv3 B1)", () => {
  it("the /config answer path is exactly the approved bytes", async () => {
    const got: Record<string, string> = {};
    for (const [file, text] of Object.entries(FILES)) got[file] = await sha256(text);
    expect(got).toEqual(ANSWER_PATH);
  });

  it("loading the shipped worker leaves every global, intrinsic and prototype the /config answer runs on untouched", async () => {
    const before = snapshot();
    const worker = (await import("../src/index")).default;
    const after = snapshot();
    expect(typeof worker.fetch).toBe("function");
    expect(before.size).toBeGreaterThan(1000);
    expect(changed(before, after)).toEqual([]);
  });

  it("the snapshot sees an intrinsic patch however it is spelled (meta: the comparison is not vacuous)", () => {
    const before = snapshot();
    const target = String["proto" + "type" as "prototype"];
    const original = target.endsWith;
    target.endsWith = function (this: string, s: string) { return original.call(this, s); };
    try {
      expect(changed(before, snapshot())).toEqual(["globalThis.String.prototype.endsWith"]);
    } finally {
      target.endsWith = original;
    }
    expect(changed(before, snapshot())).toEqual([]);
  });
});
