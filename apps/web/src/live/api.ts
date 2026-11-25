import type { LiveFailure, LiveOutcome, LivePlan, Origin } from "./types";

/**
 * Where /plan lives. In dev, Vite proxies /api to the deployed Worker (vite.config.ts), because the Worker
 * sends no CORS headers. A build has no proxy, so live planning is off unless VITE_API_BASE names a host
 * that answers CORS.
 */
export function apiBase(): string | null {
  const configured = import.meta.env.VITE_API_BASE as string | undefined;
  if (configured && configured.length > 0) return configured.replace(/\/$/, "");
  return import.meta.env.DEV ? "/api" : null;
}

const DEVICE_KEY = "scenic.device.v1";

/** The install UUID the API scopes the daily allowance to (routerDeps.ts DEVICE_ID). Random, per browser. */
export function deviceId(): string {
  try {
    const saved = localStorage.getItem(DEVICE_KEY);
    if (saved && /^[0-9a-f-]{36}$/.test(saved)) return saved;
    const fresh = crypto.randomUUID();
    localStorage.setItem(DEVICE_KEY, fresh);
    return fresh;
  } catch {
    return crypto.randomUUID();
  }
}

/** One coordinate, never more than 2 decimals (CLAUDE.md: the server never receives more). */
export function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

export interface PlanAsk {
  origin: Origin;
  placeId: string;
  budgetMinutes: number;
  allBackRoads?: boolean;
}

/** The /plan body. Built here and only here, so the 2-decimal rule cannot be skipped by a caller. */
export function planBody(ask: PlanAsk): Record<string, unknown> {
  const body: Record<string, unknown> = {
    origin: { lat: round2(ask.origin.lat), lon: round2(ask.origin.lon) },
    destination: { place: ask.placeId },
    budget_minutes: Math.max(0, Math.min(180, Math.round(ask.budgetMinutes))),
  };
  if (ask.allBackRoads) body.back_roads = true;
  return body;
}

export function failureOf(status: number, body: Record<string, unknown>): LiveFailure {
  const error = typeof body.error === "string" ? body.error : "";
  const num = (v: unknown) => (typeof v === "number" ? v : null);
  switch (error) {
    case "nothing_pretty":
      return {
        kind: "nothing_pretty",
        moreTimeMinutes: num(body.more_time_minutes),
        backRoadsEtaS: num(body.back_roads_eta_s),
        backRoadsBudgetMinutes: num(body.back_roads_budget_minutes),
      };
    case "quota_exhausted":
      return { kind: "quota_exhausted", resetsAt: typeof body.resets_at === "string" ? body.resets_at : null };
    case "planning_unavailable":
    case "planning_paused":
      return { kind: "offline" };
    case "no_scenic_alternative":
      return { kind: "no_scenic_alternative" };
    case "no_route":
      return { kind: "no_route" };
    case "unknown_place":
      return { kind: "unknown_place" };
    case "region_unsupported":
      return { kind: "region_unsupported" };
    default:
      return { kind: "other", detail: error || `HTTP ${status}` };
  }
}

export async function planLive(ask: PlanAsk, signal?: AbortSignal): Promise<LiveOutcome> {
  const base = apiBase();
  if (base === null) return { ok: false, failure: { kind: "offline" } };
  let response: Response;
  try {
    response = await fetch(`${base}/plan`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-scenic-device": deviceId() },
      body: JSON.stringify(planBody(ask)),
      signal,
    });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    return { ok: false, failure: { kind: "offline" } };
  }
  let body: Record<string, unknown> = {};
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    // An HTML error page from a proxy or tunnel reads as offline, below.
  }
  if (response.ok && Array.isArray((body.route as LivePlan["route"] | undefined)?.coordinates)) {
    return { ok: true, plan: body as unknown as LivePlan };
  }
  if (response.status >= 500 && body.error === undefined) return { ok: false, failure: { kind: "offline" } };
  return { ok: false, failure: failureOf(response.status, body) };
}

/** The anon tier's daily plan allowance, from /config. Null when it can't be read. */
export async function dailyPlanAllowance(): Promise<number | null> {
  const base = apiBase();
  if (base === null) return null;
  try {
    const config = (await (await fetch(`${base}/config`)).json()) as { quota?: { anon?: { plan?: unknown } } };
    const plan = config.quota?.anon?.plan;
    return typeof plan === "number" ? plan : null;
  } catch {
    return null;
  }
}
