/**
 * The /plan body, parsed against a WHITELIST (T-0248 R1/R2, P-PRIV-05).
 *
 * The server never receives more than one coordinate per user action and never more than 2 decimals. The one
 * coordinate is `origin`, rounded to 2 dp on the device; the destination is a corpus PLACE ID. Holding that
 * by refusing known spellings of a second coordinate would be a blacklist, and the next spelling would get
 * through - so every key at every level is checked against the keys this endpoint accepts, and anything else
 * is refused. A coordinate cannot ride in under a name nobody thought of, because there is no such name.
 */
import type { LatLon } from "./latLon";
import { vehicleProblem } from "./vehicle";

export const ORIGIN_DECIMALS = 2;
export const MAX_BUDGET_MINUTES = 180;
export const MAX_PLACE_ID_LENGTH = 128;
export const PLACE_ID = /^[A-Za-z0-9:._-]+$/;
const INSTANT = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d{1,3})?)?Z$/;

const BODY_KEYS = ["origin", "destination", "budget_minutes", "departs_at", "vehicle"];
const ORIGIN_KEYS = ["lat", "lon"];
const DESTINATION_KEYS = ["place"];

export interface PlanRequest {
  origin: LatLon;
  destinationPlace: string;
  budgetMinutes: number;
  departsAt: string | null;
}

export type Parsed = { ok: true; request: PlanRequest } | { ok: false; problem: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Exactly these keys, each present unless optional: the whitelist the module comment describes. */
function keysProblem(value: Record<string, unknown>, allowed: string[], required: string[], where: string): string | null {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) return `${where} carries ${JSON.stringify(key)}, which /plan does not accept`;
  }
  for (const key of required) {
    if (!(key in value)) return `${where} needs ${key}`;
  }
  return null;
}

/** A number already at ORIGIN_DECIMALS places: what toFixed(2) gives back must be the number itself. */
export function atMostTwoDecimals(value: number): boolean {
  return Number(value.toFixed(ORIGIN_DECIMALS)) === value;
}

function coordinateProblem(value: unknown, name: string, limit: number): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return `origin.${name} is not a finite number`;
  if (value < -limit || value > limit) return `origin.${name} is outside [-${limit}, ${limit}]`;
  if (!atMostTwoDecimals(value)) return `origin.${name} has more than ${ORIGIN_DECIMALS} decimals; round it on the device`;
  return null;
}

function instantProblem(value: unknown): string | null {
  if (typeof value !== "string") return "departs_at is not an ISO-8601 UTC string";
  const match = INSTANT.exec(value);
  if (!match) return "departs_at is not an ISO-8601 UTC instant like 2026-10-05T16:30:00Z";
  const [, y, mo, d, h, mi, s] = match;
  const date = new Date(Date.UTC(Number(y), Number(mo) - 1, Number(d), Number(h), Number(mi), Number(s ?? 0)));
  const same = date.getUTCFullYear() === Number(y) && date.getUTCMonth() === Number(mo) - 1 &&
    date.getUTCDate() === Number(d) && date.getUTCHours() === Number(h) && date.getUTCMinutes() === Number(mi);
  return same ? null : "departs_at is not a real instant";
}

export function parsePlanRequest(body: unknown): Parsed {
  const refuse = (problem: string): Parsed => ({ ok: false, problem });
  if (!isRecord(body)) return refuse("the body must be a JSON object");
  const top = keysProblem(body, BODY_KEYS, ["origin", "destination", "budget_minutes"], "the body");
  if (top) return refuse(top);

  const origin = body.origin;
  if (!isRecord(origin)) return refuse("origin must be {lat, lon}");
  const originKeys = keysProblem(origin, ORIGIN_KEYS, ORIGIN_KEYS, "origin");
  if (originKeys) return refuse(originKeys);
  const lat = coordinateProblem(origin.lat, "lat", 90) ?? coordinateProblem(origin.lon, "lon", 180);
  if (lat) return refuse(lat);

  const destination = body.destination;
  if (!isRecord(destination)) return refuse("destination must be {place}");
  const destinationKeys = keysProblem(destination, DESTINATION_KEYS, DESTINATION_KEYS, "destination");
  if (destinationKeys) return refuse(destinationKeys);
  const place = destination.place;
  if (typeof place !== "string" || place.length === 0 || place.length > MAX_PLACE_ID_LENGTH || !PLACE_ID.test(place)) {
    return refuse("destination.place is not a corpus place id");
  }

  const minutes = body.budget_minutes;
  if (typeof minutes !== "number" || !Number.isFinite(minutes) || minutes < 0 || minutes > MAX_BUDGET_MINUTES) {
    return refuse(`budget_minutes must be a number of minutes in [0, ${MAX_BUDGET_MINUTES}]`);
  }

  let departsAt: string | null = null;
  if (body.departs_at !== undefined) {
    const problem = instantProblem(body.departs_at);
    if (problem) return refuse(problem);
    departsAt = body.departs_at as string;
  }

  const vehicle = vehicleProblem(body.vehicle, "/plan");
  if (vehicle) return refuse(vehicle);

  return {
    ok: true,
    request: { origin: { lat: origin.lat as number, lon: origin.lon as number }, destinationPlace: place,
      budgetMinutes: minutes, departsAt },
  };
}
