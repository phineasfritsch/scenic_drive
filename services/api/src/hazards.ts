/**
 * Hazards on the chosen route, REPORTED from the router's own path details and never invented (T-0248 R8).
 *
 * The safety gates themselves (unpaved with positive evidence, private/no access, track) live in
 * car_scenic_base.json and keep those edges off the route; what can still be on it - a compacted shoulder the
 * gate list does not name, a destination-only stretch - is told to the driver here. A value on the whitelist
 * below is not a hazard; `missing` (the router has nothing to say) is not evidence of one. Everything else is.
 */
import type { RoutePath } from "./routePath";

export const PAVED_SURFACES: readonly string[] = ["asphalt", "concrete", "paved", "missing"];
export const OPEN_ACCESS: readonly string[] = ["yes", "missing"];
/** The details the Worker adds to every request AFTER the custom-model gate (plan :120). */
export const HAZARD_DETAILS = ["surface", "road_access"] as const;

export interface Hazard {
  kind: (typeof HAZARD_DETAILS)[number];
  value: string;
  from_index: number;
  to_index: number;
}

export function hazardsOf(path: RoutePath): Hazard[] {
  const hazards: Hazard[] = [];
  for (const kind of HAZARD_DETAILS) {
    const fine = kind === "surface" ? PAVED_SURFACES : OPEN_ACCESS;
    for (const run of path.details[kind] ?? []) {
      if (typeof run.value !== "string") continue;
      const value = run.value.toLowerCase();
      if (!fine.includes(value)) hazards.push({ kind, value, from_index: run.from, to_index: run.to });
    }
  }
  return hazards;
}
