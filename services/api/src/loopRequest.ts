/**
 * The /loop body, parsed against a WHITELIST (T-0252 R1, P-PRIV-05) - the planRequest.ts shape.
 *
 * `{start: {lat, lon}, minutes}`. `start` is the ONE coordinate a loop sends, each component already rounded to
 * 2 dp on the device; every key at every level is checked against the keys this endpoint accepts, so a second
 * coordinate has no name to ride in under.
 */
import type { LatLon } from "./latLon";
import { atMostTwoDecimals, ORIGIN_DECIMALS } from "./planRequest";
import { vehicleProblem } from "./vehicle";

export const MIN_LOOP_MINUTES = 10;
export const MAX_LOOP_MINUTES = 180;

const BODY_KEYS = ["start", "minutes", "vehicle"];
const REQUIRED_KEYS = ["start", "minutes"];
const START_KEYS = ["lat", "lon"];

export interface LoopRequest {
  start: LatLon;
  minutes: number;
}

export type ParsedLoop = { ok: true; request: LoopRequest } | { ok: false; problem: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function keysProblem(value: Record<string, unknown>, allowed: string[], required: string[], where: string): string | null {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) return `${where} carries ${JSON.stringify(key)}, which /loop does not accept`;
  }
  for (const key of required) {
    if (!(key in value)) return `${where} needs ${key}`;
  }
  return null;
}

function coordinateProblem(value: unknown, name: string, limit: number): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return `start.${name} is not a finite number`;
  if (value < -limit || value > limit) return `start.${name} is outside [-${limit}, ${limit}]`;
  if (!atMostTwoDecimals(value)) return `start.${name} has more than ${ORIGIN_DECIMALS} decimals; round it on the device`;
  return null;
}

export function parseLoopRequest(body: unknown): ParsedLoop {
  const refuse = (problem: string): ParsedLoop => ({ ok: false, problem });
  if (!isRecord(body)) return refuse("the body must be a JSON object");
  const top = keysProblem(body, BODY_KEYS, REQUIRED_KEYS, "the body");
  if (top) return refuse(top);

  const start = body.start;
  if (!isRecord(start)) return refuse("start must be {lat, lon}");
  const startKeys = keysProblem(start, START_KEYS, START_KEYS, "start");
  if (startKeys) return refuse(startKeys);
  const coordinate = coordinateProblem(start.lat, "lat", 90) ?? coordinateProblem(start.lon, "lon", 180);
  if (coordinate) return refuse(coordinate);

  const minutes = body.minutes;
  if (typeof minutes !== "number" || !Number.isFinite(minutes) || minutes < MIN_LOOP_MINUTES || minutes > MAX_LOOP_MINUTES) {
    return refuse(`minutes must be a number of minutes in [${MIN_LOOP_MINUTES}, ${MAX_LOOP_MINUTES}]`);
  }

  const vehicle = vehicleProblem(body.vehicle, "/loop");
  if (vehicle) return refuse(vehicle);

  return { ok: true, request: { start: { lat: start.lat as number, lon: start.lon as number }, minutes } };
}
