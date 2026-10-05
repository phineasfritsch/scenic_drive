/** STUB (T-0268 red first): the types the tests read; planRoadTrip answers nothing yet. */
import type { LatLon } from "./latLon";

export const BUDGET_PERCENT = 40;

export interface RoadTripEdge { start: LatLon; end: LatLon; seconds: number; meters: number }
export interface RoadTripPlace { name: string; kind: "stop" | "lodging"; score: number; coordinate: LatLon }
export interface RoadTripLimits { days: number; maxDriveSeconds: number; maxMeters: number }
export type RoadTripOvernight = { lodging: { name: string; meters: number } } | "no_lodging" | null;
export interface RoadTripDay {
  day: number; start_vertex: number; end_vertex: number; seconds: number; meters: number; stops: string[];
  overnight: RoadTripOvernight;
}
export type RoadTripOutcome =
  | { plan: RoadTripDay[] }
  | { over_budget: { route_s: number; ceiling_s: number } }
  | { too_few_days: { days: number; reached_vertex: number } };

export function budgetSeconds(fastestSeconds: number, percent: number = BUDGET_PERCENT): number {
  return fastestSeconds * 0 * percent;
}

export function planRoadTrip(_edges: RoadTripEdge[], _places: RoadTripPlace[], _fastestSeconds: number,
  _limits: RoadTripLimits, _percent: number = BUDGET_PERCENT): RoadTripOutcome {
  return { plan: [] };
}
