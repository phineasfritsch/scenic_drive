/** STUB (T-0268 red first). */
import type { PlanDeps, PlanEnv } from "./plan";
import { planDepsFromEnv } from "./plan";
import type { RouterEnv } from "./routerDeps";

export const TRIP_UPSTREAM_COST = 12;
export const MIN_TRIP_DAYS = 1;
export const MAX_TRIP_DAYS = 5;
export const MAX_EXTRA_BUDGET_PCT = 40;
export const MAX_DRIVE_MS_PER_DAY = 21_600_000;
export const MAX_METERS_PER_DAY = 482_803;

export type TripDeps = PlanDeps;

export function tripDepsFromEnv(env: PlanEnv & RouterEnv & { DB?: D1Database }): TripDeps | null {
  return planDepsFromEnv(env);
}

export async function handleTrip(_req: Request, _env: PlanEnv, _deps: TripDeps | null): Promise<Response> {
  return new Response(JSON.stringify({ error: "not_implemented" }), { status: 501 });
}
