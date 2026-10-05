/** STUB (T-0268 red first). */
import type { LatLon } from "./latLon";

export interface TripRequest { origin: LatLon; destinationPlace: string; days: number; extraBudgetPct: number }
export type ParsedTrip = { ok: true; request: TripRequest } | { ok: false; problem: string };

export function parseTripRequest(_body: unknown): ParsedTrip {
  return { ok: false, problem: "stub" };
}
