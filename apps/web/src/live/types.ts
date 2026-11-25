/** Live planning against services/api /plan (planRequest.ts, scenicPlanner.ts ScenicPlanResult). */

export interface LivePlace {
  /** The corpus place id, as a string: 64-bit, so a JS number would round it. */
  id: string;
  name: string;
  cls: string;
  /** [lon, lat] */
  at: [number, number];
}

export interface Origin {
  name: string;
  /** Already at 2 decimals: the server never receives more (CLAUDE.md product invariant). */
  lat: number;
  lon: number;
}

export interface LiveHazard {
  kind: string;
  value: string;
  from_index: number;
  to_index: number;
}

export interface LivePlan {
  route: { coordinates: [number, number][]; distance_m: number };
  eta_s: number;
  fastest_eta_s: number;
  ceiling_s: number;
  budget_s: number;
  lambda: number;
  eta_is_estimate: true;
  hazards: LiveHazard[];
  waypoints: { lat: number; lon: number }[];
  apple_maps_url: string;
}

export type LiveFailure =
  | { kind: "nothing_pretty"; moreTimeMinutes: number | null; backRoadsEtaS: number | null; backRoadsBudgetMinutes: number | null }
  | { kind: "quota_exhausted"; resetsAt: string | null }
  | { kind: "offline" }
  | { kind: "no_scenic_alternative" }
  | { kind: "no_route" }
  | { kind: "unknown_place" }
  | { kind: "region_unsupported" }
  | { kind: "other"; detail: string };

export type LiveOutcome = { ok: true; plan: LivePlan } | { ok: false; failure: LiveFailure };
