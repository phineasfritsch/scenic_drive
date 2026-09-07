import { SELF, env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import worker, { ROUTES } from "../src/index";

const url = (p: string) => `https://scenic-api.test${p}`;

describe("operational routes", () => {
  it("/__version reports the baked git sha and schema version", async () => {
    const r = await SELF.fetch(url("/__version"));
    expect(r.status).toBe(200);
    const body = (await r.json()) as { git_sha: string; built_at: string; schema_version: number };
    expect(body.git_sha).toBe("dev");
    expect(typeof body.built_at).toBe("string");
    expect(body.schema_version).toBe(0);
  });

  it("/__health is ok with a reachable D1", async () => {
    const r = await SELF.fetch(url("/__health"));
    expect(r.status).toBe(200);
    expect(await r.json()).toMatchObject({ ok: true, db: "up" });
  });

  it("unknown paths are 404 and never cached", async () => {
    const r = await SELF.fetch(url("/nope"));
    expect(r.status).toBe(404);
    expect(r.headers.get("cache-control")).toBe("no-store");
  });

  it("every route is enumerable (kill-switch pin will iterate ROUTES, not a hand list)", () => {
    expect(Object.keys(ROUTES).sort()).toEqual(["/__health", "/__ro", "/__version"]);
    expect(typeof worker.fetch).toBe("function");
  });
});

describe("/__ro", () => {
  const post = (sql: string, token?: string) =>
    SELF.fetch(url("/__ro"), {
      method: "POST",
      headers: { "content-type": "application/json", ...(token ? { authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ sql }),
    });

  it("refuses without the token, even for a SELECT", async () => {
    expect((await post("SELECT 1")).status).toBe(401);
  });

  it("refuses when RO_TOKEN is unset on the server (no token means no access, not open access)", async () => {
    // env.RO_TOKEN is undefined in tests unless set below
    expect((await post("SELECT 1", "anything")).status).toBe(401);
  });

  it("with the token: accepts SELECT and refuses writes with a reason", async () => {
    (env as unknown as { RO_TOKEN: string }).RO_TOKEN = "t0k";
    const ok = await post("SELECT 1 AS one", "t0k");
    expect(ok.status).toBe(200);
    expect(await ok.json()).toMatchObject({ rows: [{ one: 1 }] });
    const bad = await post("REPLACE INTO x VALUES (1)", "t0k");
    expect(bad.status).toBe(400);
    expect(((await bad.json()) as { error: string }).error).toMatch(/refused/);
  });
});
