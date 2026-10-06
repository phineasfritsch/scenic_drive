/**
 * The /telemetry body WHITELIST (T-0279 R2-R4, P-PRIV-05). The device sends `{"events": [point, ...]}`, each point
 * exactly the Workers Analytics Engine data point Sources/Telemetry's TelemetryDataPoint encodes (T-0265 R2):
 * indexes = [name], blobs = [name, label, cell], doubles = [v1, v2]. Everything is checked against what the Swift
 * encoder can write - the fifteen wire names, each label from its closed enum, the cell an H3 res-5 cell on
 * plan_requested only, each double a whole number in its ruled range - and anything else is refused. The accepted
 * point is REBUILT from the checked fields, so nothing the device sent beside them can reach a write.
 */
import { isResolution5Cell } from "./h3Res5";

/** At most this many points in one request (R2). */
export const MAX_TELEMETRY_EVENTS_PER_REQUEST = 20;

/** A whole-number range [min, max] for one double slot; [0, 0] is an unused slot. */
type Range = readonly [number, number];
const UNUSED: Range = [0, 0];

interface WireRule {
  /** The closed set of blob 2; [""] for an event that carries no label. */
  labels: readonly string[];
  /** Whether blob 3 is an H3 res-5 cell (plan_requested only) or always "". */
  cell: boolean;
  doubles: readonly [Range, Range];
}

const NONE: WireRule = { labels: [""], cell: false, doubles: [UNUSED, UNUSED] };
const PERCENT: Range = [0, 100];

/** The fifteen wire names and what each may carry (R3), from the Swift enums of Sources/Telemetry. */
export const TELEMETRY_WIRE: Readonly<Record<string, WireRule>> = Object.freeze({
  plan_requested: { labels: ["scenic", "loop", "surprise", "road_trip"], cell: true, doubles: [[0, 1440], UNUSED] },
  plan_result: { ...NONE, labels: ["routed", "no_alternative", "quota_exceeded", "failed"] },
  preview_shown: NONE,
  handoff_tapped: { ...NONE, labels: ["apple_maps", "google_maps", "waze"] },
  drive_started: NONE,
  drive_completed: { ...NONE, doubles: [PERCENT, [0, 1000]] },
  drive_abandoned: { ...NONE, doubles: [PERCENT, UNUSED] },
  post_drive_answer: { ...NONE, labels: ["prettier", "not_prettier"] },
  surprise_shown: NONE,
  surprise_not_this: { ...NONE, labels: ["too_far", "been_there", "not_my_thing"] },
  surprise_take_me_there: NONE,
  surprise_arrived: NONE,
  corpus_activated: { ...NONE, doubles: [[0, 2147483647], UNUSED] },
  paywall_shown: NONE,
  paywall_converted: NONE,
});

/** Keys in the Swift encoder's sorted order, so a written point serialises to the device's own bytes. */
export interface TelemetryPoint {
  blobs: [string, string, string];
  doubles: [number, number];
  indexes: [string];
}

export type ParsedTelemetry = { ok: true; points: TelemetryPoint[] } | { ok: false; problem: string };

const refuse = (problem: string): ParsedTelemetry => ({ ok: false, problem });

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Exactly these keys, no more and no fewer. */
function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const own = Object.keys(value).sort();
  return own.length === keys.length && [...keys].sort().every((key, i) => own[i] === key);
}

/** A whole number in [min, max], and never -0 (the Swift encoder writes Ints, never -0). */
function inRange(value: unknown, [min, max]: Range): value is number {
  return typeof value === "number" && Number.isInteger(value) && !Object.is(value, -0) && value >= min && value <= max;
}

function parsePoint(raw: unknown, at: number): TelemetryPoint | string {
  if (!isPlainObject(raw) || !hasExactKeys(raw, ["indexes", "blobs", "doubles"])) {
    return `events[${at}] must have exactly the keys indexes, blobs and doubles`;
  }
  const { indexes, blobs, doubles } = raw;
  if (!Array.isArray(blobs) || blobs.length !== 3 || !blobs.every((b) => typeof b === "string")) {
    return `events[${at}].blobs must be three strings`;
  }
  const [name, label, cell] = blobs as [string, string, string];
  if (!Object.prototype.hasOwnProperty.call(TELEMETRY_WIRE, name)) return `events[${at}] is not a telemetry event`;
  const rule = TELEMETRY_WIRE[name]!;
  if (!Array.isArray(indexes) || indexes.length !== 1 || indexes[0] !== name) {
    return `events[${at}].indexes must be [the event name]`;
  }
  if (!rule.labels.includes(label)) return `events[${at}] label is not one of ${name}'s`;
  if (rule.cell ? !isResolution5Cell(cell) : cell !== "") {
    return rule.cell ? `events[${at}] cell must be an H3 resolution-5 cell` : `events[${at}] carries no cell`;
  }
  if (!Array.isArray(doubles) || doubles.length !== 2) return `events[${at}].doubles must be two numbers`;
  const [v1, v2] = doubles as unknown[];
  if (!inRange(v1, rule.doubles[0]) || !inRange(v2, rule.doubles[1])) {
    return `events[${at}].doubles are outside ${name}'s ranges`;
  }
  return { blobs: [name, label, cell], doubles: [v1, v2], indexes: [name] };
}

/** The whole body against the whitelist: the accepted points, rebuilt, or the first problem. */
export function parseTelemetryBody(raw: unknown): ParsedTelemetry {
  if (!isPlainObject(raw) || !hasExactKeys(raw, ["events"])) return refuse("the body must be exactly {events}");
  const { events } = raw;
  if (!Array.isArray(events) || events.length < 1 || events.length > MAX_TELEMETRY_EVENTS_PER_REQUEST) {
    return refuse(`events must be an array of 1 to ${MAX_TELEMETRY_EVENTS_PER_REQUEST} points`);
  }
  const points: TelemetryPoint[] = [];
  for (let at = 0; at < events.length; at++) {
    const point = parsePoint(events[at], at);
    if (typeof point === "string") return refuse(point);
    points.push(point);
  }
  return { ok: true, points };
}
