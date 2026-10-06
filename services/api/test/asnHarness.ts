/**
 * Shared /asn test plumbing (T-0267): the SHIPPED migration applied to the test D1, the whole entitlements table
 * read back for equality, and calls through the shipped handlers with production deps whose ONLY replacement is
 * the root fingerprint (R2). Not a test file.
 */
import { env } from "cloudflare:test";
import entitlementsSql from "../migrations/0002_entitlements.sql?raw";
import { asnDepsFromEnv, handleAsn, type AsnDeps } from "../src/asn";
import { ROUTES, type Env } from "../src/index";

export const NOW = Date.UTC(2026, 9, 5, 12, 0, 0);
export const TOKEN = "6f1c2d3e-4a5b-4c6d-8e7f-0123456789ab";

export async function freshTable(): Promise<void> {
  for (const statement of entitlementsSql.split(";").map((s) => s.trim()).filter(Boolean)) {
    await env.DB.prepare(statement).run();
  }
  await env.DB.prepare("DELETE FROM entitlements").run();
}

export async function rows(): Promise<Record<string, unknown>[]> {
  return (await env.DB.prepare("SELECT * FROM entitlements ORDER BY original_transaction_id").all()).results;
}

/** Production deps for this env, with the test chain's root fingerprint in place of the pinned Apple root. */
export function testDeps(rootSha256: string, extra: Partial<Env> = {}): AsnDeps {
  return { ...asnDepsFromEnv({ ...(env as unknown as Env), ...extra }), rootSha256 };
}

export async function answer(response: Response) {
  return { status: response.status, json: (await response.json()) as unknown };
}

export async function postAsn(signedPayload: unknown, deps: AsnDeps) {
  const req = new Request("https://scenic-api.test/asn", { method: "POST", body: JSON.stringify({ signedPayload }) });
  return answer(await handleAsn(req, deps));
}

/** Through the shipped ROUTES table, production deps and all - the pinned Apple root included. */
export async function routeAsn(body: string) {
  const req = new Request("https://scenic-api.test/asn", { method: "POST", body });
  return answer(await ROUTES["/asn"]!(req, env as unknown as Env, new URL(req.url)));
}

export async function getEntitlement(token: string | null, extra: Partial<Env> = {}) {
  const headers: Record<string, string> = token === null ? {} : { "x-scenic-account-token": token };
  const req = new Request("https://scenic-api.test/entitlement", { headers });
  return answer(await ROUTES["/entitlement"]!(req, { ...(env as unknown as Env), ...extra }, new URL(req.url)));
}

export const row = (over: Record<string, unknown>) => ({
  original_transaction_id: "1000", app_account_token: TOKEN, environment: "Production", product_id: "scenic.pro.monthly",
  status: "active", active_until: null, notification_type: "SUBSCRIBED", subtype: null, signed_date: NOW - 60_000, ...over,
});
