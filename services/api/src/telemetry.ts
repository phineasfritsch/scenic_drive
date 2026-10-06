/**
 * POST /telemetry - the device's T-0265 data points into Workers Analytics Engine (T-0279). The order (R6):
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 telemetry_paused, before the body is read.
 *   2. The body against the whitelist (telemetryPoint.ts, P-PRIV-05) -> 400. Nothing reserved, nothing written.
 *   3. TELEMETRY or QUOTA unbound -> 503 telemetry_unavailable.
 *   4. The request's n events RESERVED in one QuotaCounter transaction (kind "telemetry", DAILY_TELEMETRY_QUOTA a
 *      device a UTC day) -> 429 quota_exhausted when it would cross the cap: the whole request, never a part.
 *   5. Only then each rebuilt point written with writeDataPoint.
 * Who is the install bucket of x-scenic-device (deviceIdentity) - no account lookup, no D1 read.
 */
import { killSwitch, type KillEnv } from "./killSwitch";
import { DAILY_TELEMETRY_QUOTA, dayKey, nextReset } from "./quota";
import type { QuotaCounter } from "./QuotaCounter";
import { deviceIdentity } from "./routerDeps";
import { parseTelemetryBody } from "./telemetryPoint";

export { MAX_TELEMETRY_EVENTS_PER_REQUEST } from "./telemetryPoint";

export interface TelemetryDeps {
  dataset: AnalyticsEngineDataset;
  quota: DurableObjectNamespace<QuotaCounter>;
  now: () => Date;
}

export interface TelemetryEnv extends KillEnv {
  TELEMETRY?: AnalyticsEngineDataset;
  QUOTA?: DurableObjectNamespace<QuotaCounter>;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: real exactly when both the Analytics Engine binding and the quota namespace are bound. */
export function telemetryDepsFromEnv(env: TelemetryEnv): TelemetryDeps | null {
  if (!env.TELEMETRY || !env.QUOTA) return null;
  return { dataset: env.TELEMETRY, quota: env.QUOTA, now: () => new Date() };
}

export async function handleTelemetry(req: Request, env: KillEnv, deps: TelemetryDeps | null): Promise<Response> {
  if (await killSwitch(env)) return json({ error: "telemetry_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseTelemetryBody(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "telemetry_unavailable" }, 503);

  const { userId } = deviceIdentity(req);
  const now = deps.now();
  const counter = deps.quota.get(deps.quota.idFromName(`device:${userId}`));
  let reserved: boolean;
  try {
    reserved = await counter.reserveDaily(dayKey(now), "telemetry", DAILY_TELEMETRY_QUOTA, parsed.points.length);
  } catch {
    return json({ error: "telemetry_unavailable" }, 503);
  }
  if (!reserved) return json({ error: "quota_exhausted", resets_at: nextReset(now) }, 429);

  for (const point of parsed.points) deps.dataset.writeDataPoint(point);
  return json({ written: parsed.points.length }, 200);
}
