/**
 * T-0279: the shared Swift fixture and a ROUTES['/telemetry'] driver over an env whose Analytics Engine binding
 * records every writeDataPoint and whose QUOTA is the in-memory QuotaCounter namespace. Not a test file.
 */
import fixtureRaw from "../../../Tests/Fixtures/t0279/datapoints.jsonl?raw";
import { ROUTES, type Env } from "../src/index";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";

export const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
export const NOW = new Date("2026-10-06T12:00:00Z");

export interface Point {
  indexes: string[];
  blobs: string[];
  doubles: number[];
}

/** One data point per line, exactly as the Swift encoder wrote it (TelemetryWireFixtureTests). */
export const FIXTURE_LINES: string[] = fixtureRaw.split("\n").filter((line) => line.length > 0);
export const FIXTURE: Point[] = FIXTURE_LINES.map((line) => JSON.parse(line) as Point);

export interface TelemetryRig {
  env: Env;
  quota: FakeQuota;
  /** Every argument writeDataPoint received, in order, as it was at the call. */
  writes: unknown[];
  /** The quota state at the moment of each write. */
  quotaAtWrite: Record<string, Record<string, unknown>>[];
}

export function telemetryRig(extra: Record<string, unknown> = {}): TelemetryRig {
  const quota = fakeQuotaNamespace();
  const writes: unknown[] = [];
  const quotaAtWrite: Record<string, Record<string, unknown>>[] = [];
  const dataset = {
    writeDataPoint(point: unknown) {
      quotaAtWrite.push(quota.state());
      writes.push(structuredClone(point));
    },
  } as unknown as AnalyticsEngineDataset;
  const env = { GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, TELEMETRY: dataset, ...extra } as unknown as Env;
  return { env, quota, writes, quotaAtWrite };
}

/** POST a body (an object, or a raw string sent as is) through the shipped ROUTES entry. */
export async function post(env: Env, body: unknown, init: { method?: string; device?: string } = {}) {
  const method = init.method ?? "POST";
  const req = new Request("https://scenic-api.test/telemetry", {
    method,
    headers: { "content-type": "application/json", "x-scenic-device": init.device ?? DEVICE },
    body: method === "GET" ? undefined : typeof body === "string" ? body : JSON.stringify(body),
  });
  const response = await ROUTES["/telemetry"]!(req, env, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

/** The daily record the quota holds for DEVICE after `events` telemetry events today. */
export function dailyTelemetry(events: number) {
  return { [`device:${DEVICE}`]: { daily: { day: "2026-10-06", plan: 0, loop: 0, telemetry: events } } };
}
