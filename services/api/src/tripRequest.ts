/**
 * The /trip body, parsed against a WHITELIST (T-0268 R1, P-PRIV-05) - the planRequest.ts shape.
 *
 * `{origin: {lat, lon}, destination: {place}, days, extra_budget_pct?}`. `origin` is the ONE coordinate a trip sends,
 * each component already rounded to 2 dp on the device; the destination is a corpus PLACE ID. Every key at every
 * level is checked against the keys this endpoint accepts, so a second coordinate has no name to ride in under.
 */
import type { LatLon } from "./latLon";
import { atMostTwoDecimals, MAX_PLACE_ID_LENGTH, ORIGIN_DECIMALS, PLACE_ID } from "./planRequest";

export const MIN_TRIP_DAYS = 1;
/** The plan prices a road trip at "12 per 5-day trip": 1 fastest + 6 searched + one leg a day (R3). */
export const MAX_TRIP_DAYS = 5;
/** The plan's +40% scenic budget; the driver may lower the ceiling, never raise it (R1). */
export const MAX_EXTRA_BUDGET_PCT = 40;

const BODY_KEYS = ["origin", "destination", "days", "extra_budget_pct"];
const REQUIRED_KEYS = ["origin", "destination", "days"];
const ORIGIN_KEYS = ["lat", "lon"];
const DESTINATION_KEYS = ["place"];

export interface TripRequest {
  origin: LatLon;
  destinationPlace: string;
  days: number;
  extraBudgetPct: number;
}

export type ParsedTrip = { ok: true; request: TripRequest } | { ok: false; problem: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function keysProblem(value: Record<string, unknown>, allowed: string[], required: string[], where: string): string | null {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) return `${where} carries ${JSON.stringify(key)}, which /trip does not accept`;
  }
  for (const key of required) {
    if (!(key in value)) return `${where} needs ${key}`;
  }
  return null;
}

function coordinateProblem(value: unknown, name: string, limit: number): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return `origin.${name} is not a finite number`;
  if (value < -limit || value > limit) return `origin.${name} is outside [-${limit}, ${limit}]`;
  if (!atMostTwoDecimals(value)) return `origin.${name} has more than ${ORIGIN_DECIMALS} decimals; round it on the device`;
  return null;
}

/** A whole number in [min, max]: Number.isInteger is false for NaN, Infinity, strings, booleans and null. */
function wholeIn(value: unknown, min: number, max: number): value is number {
  return Number.isInteger(value) && (value as number) >= min && (value as number) <= max;
}

export function parseTripRequest(body: unknown): ParsedTrip {
  const refuse = (problem: string): ParsedTrip => ({ ok: false, problem });
  if (!isRecord(body)) return refuse("the body must be a JSON object");
  const top = keysProblem(body, BODY_KEYS, REQUIRED_KEYS, "the body");
  if (top) return refuse(top);

  const origin = body.origin;
  if (!isRecord(origin)) return refuse("origin must be {lat, lon}");
  const originKeys = keysProblem(origin, ORIGIN_KEYS, ORIGIN_KEYS, "origin");
  if (originKeys) return refuse(originKeys);
  const coordinate = coordinateProblem(origin.lat, "lat", 90) ?? coordinateProblem(origin.lon, "lon", 180);
  if (coordinate) return refuse(coordinate);

  const destination = body.destination;
  if (!isRecord(destination)) return refuse("destination must be {place}");
  const destinationKeys = keysProblem(destination, DESTINATION_KEYS, DESTINATION_KEYS, "destination");
  if (destinationKeys) return refuse(destinationKeys);
  const place = destination.place;
  if (typeof place !== "string" || place.length === 0 || place.length > MAX_PLACE_ID_LENGTH || !PLACE_ID.test(place)) {
    return refuse("destination.place is not a corpus place id");
  }

  const days = body.days;
  if (!wholeIn(days, MIN_TRIP_DAYS, MAX_TRIP_DAYS)) {
    return refuse(`days must be a whole number of days in [${MIN_TRIP_DAYS}, ${MAX_TRIP_DAYS}]`);
  }

  let extraBudgetPct = MAX_EXTRA_BUDGET_PCT;
  if ("extra_budget_pct" in body) {
    const pct = body.extra_budget_pct;
    if (!wholeIn(pct, 0, MAX_EXTRA_BUDGET_PCT)) return refuse(`extra_budget_pct must be a whole percent in [0, ${MAX_EXTRA_BUDGET_PCT}]`);
    extraBudgetPct = pct;
  }

  return {
    ok: true,
    request: { origin: { lat: origin.lat as number, lon: origin.lon as number }, destinationPlace: place, days, extraBudgetPct },
  };
}
