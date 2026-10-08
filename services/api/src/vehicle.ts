/**
 * The vehicle a route is planned for (T-0311 R1-R4) - the optional top-level `vehicle` key of /plan, /loop and /trip.
 *
 * Its values are the app's ScenicKit VehicleProfile raw values. Only the profiles routing is built for are accepted;
 * every other value - a profile the app names but cannot plan for yet, an unknown string, or anything that is not a
 * string - is refused by the parser, before any quota or upstream work. An absent key is "standard" (R2): every
 * build that predates the key could only have chosen standard. A non-string is refused, so the key can never carry
 * a coordinate (P-PRIV-05).
 */
export const ENABLED_VEHICLE_PROFILES: readonly string[] = ["standard"];

/** null when the vehicle is absent or an enabled profile; otherwise the refusal detail, naming the route. */
export function vehicleProblem(value: unknown, route: string): string | null {
  if (value === undefined) return null;
  if (typeof value === "string" && ENABLED_VEHICLE_PROFILES.includes(value)) return null;
  const allowed = ENABLED_VEHICLE_PROFILES.map((profile) => JSON.stringify(profile)).join(" or ");
  return `vehicle must be ${allowed}: the only profile ${route} plans for`;
}
