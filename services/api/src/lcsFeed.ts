/**
 * The Caltrans Lane Closure System feed for District 7 (T-0276), read into closure polygons.
 *
 * Rulings R1-R5 in queue/.../T-0276: ONLY typeOfClosure "Full" (R1), active now under the union of 10-97 and the
 * scheduled window minus cancelled (10-22) and picked up (10-98) (R2), every field read refused by name per row
 * (R3), buffered on a literal local plane (R4) and capped at CLOSURES_STORED_MAX_POLYGONS (T-0282 N1) in a ruled order (R5). The feed
 * carries no road geometry - only a begin and an end point - so a short closure is one rectangle around its chord
 * and a long one is two gate squares that stop travel THROUGH it without walling off the streets its chord crosses.
 */
import { CLOSURES_STORED_MAX_POLYGONS } from "./closuresStore";
import type { ClosureCollection, ClosurePolygon } from "./customModel";

export const LCS_D7_FEED = "https://cwwp2.dot.ca.gov/data/d7/lcs/lcsStatusD07.json";
export const FULL_CLOSURE = "Full";
/** The D7 box, the measured extent of all 5616 positions plus a margin (R3). Inclusive. */
export const D7_LON_MIN = -119.5;
export const D7_LON_MAX = -117.6;
export const D7_LAT_MIN = 33.7;
export const D7_LAT_MAX = 34.9;
/** The local plane at lat 34.3 (R4): literals, so no trig touches a coordinate. */
export const METERS_PER_DEGREE_LAT = 110946;
export const METERS_PER_DEGREE_LON = 91961;
export const CLOSURE_BUFFER_M = 30;
export const LONG_CLOSURE_M = 500;
/** Cap order after code 10-97 (R5): through roads first, rest areas last, anything unnamed after them. */
export const FACILITY_RANK: readonly string[] = ["Conventional Hwy", "Mainline", "HOV", "Collector", "Connector",
  "HOV Connector", "On Ramp", "Off Ramp", "Rest Area"];

const EPOCH = /^[0-9]{1,10}$/;
const DECIMAL = /^-?[0-9]{1,3}(\.[0-9]{1,8})?$/;

export type LcsRefusal = "row_not_object" | "type_missing" | "index_missing" | "code_not_boolean" | "start_not_epoch"
  | "indefinite_not_boolean" | "end_not_epoch" | "window_inverted" | "facility_missing" | "position_not_decimal"
  | "position_outside_d7";

export type Ring = [number, number][];

export interface ActiveClosure {
  index: string;
  confirmed: boolean;
  facility: string;
  rings: Ring[];
}

export interface LcsParse {
  rows: number;
  full: number;
  active: number;
  refused: { index: string | null; reason: LcsRefusal }[];
  closures: ActiveClosure[];
}

export interface CappedClosures {
  geojson: ClosureCollection;
  kept: number;
  dropped: number;
}

function at(value: unknown, ...path: string[]): unknown {
  let here = value;
  for (const key of path) {
    if (here === null || typeof here !== "object" || Array.isArray(here)) return undefined;
    here = (here as Record<string, unknown>)[key];
  }
  return here;
}

function flag(value: unknown): "true" | "false" | null {
  return value === "true" || value === "false" ? value : null;
}

const epoch = (value: unknown): value is string => typeof value === "string" && EPOCH.test(value);

function position(lon: unknown, lat: unknown): [number, number] | LcsRefusal {
  if (typeof lon !== "string" || !DECIMAL.test(lon) || typeof lat !== "string" || !DECIMAL.test(lat)) {
    return "position_not_decimal";
  }
  const x = Number(lon);
  const y = Number(lat);
  if (!(x >= D7_LON_MIN && x <= D7_LON_MAX) || !(y >= D7_LAT_MIN && y <= D7_LAT_MAX)) return "position_outside_d7";
  return [x, y];
}

/** The closure's rings on the local plane centred on its begin point (R4). */
export function closureRings(begin: [number, number], end: [number, number]): Ring[] {
  const [blon, blat] = begin;
  const b = CLOSURE_BUFFER_M;
  const dx = (end[0] - blon) * METERS_PER_DEGREE_LON;
  const dy = (end[1] - blat) * METERS_PER_DEGREE_LAT;
  const length = Math.sqrt(dx * dx + dy * dy);
  const pt = (x: number, y: number): [number, number] => [blon + x / METERS_PER_DEGREE_LON, blat + y / METERS_PER_DEGREE_LAT];
  const square = (cx: number, cy: number): Ring =>
    [pt(cx - b, cy - b), pt(cx + b, cy - b), pt(cx + b, cy + b), pt(cx - b, cy + b), pt(cx - b, cy - b)];
  if (length === 0) return [square(0, 0)];
  if (length > LONG_CLOSURE_M) return [square(0, 0), square(dx, dy)];
  const ux = dx / length;
  const uy = dy / length;
  const nx = -uy;
  const ny = ux;
  const p0x = -ux * b;
  const p0y = -uy * b;
  const p1x = dx + ux * b;
  const p1y = dy + uy * b;
  const first = pt(p0x - nx * b, p0y - ny * b);
  return [[first, pt(p1x - nx * b, p1y - ny * b), pt(p1x + nx * b, p1y + ny * b), pt(p0x + nx * b, p0y + ny * b), first]];
}

function refusal(closure: unknown, index: string | null): LcsRefusal | null {
  const codes = ["1097", "1098", "1022"].map((n) => flag(at(closure, `code${n}`, `isCode${n}`)));
  const start = at(closure, "closureTimestamp", "closureStartEpoch");
  const indefinite = flag(at(closure, "closureTimestamp", "isClosureEndIndefinite"));
  const end = at(closure, "closureTimestamp", "closureEndEpoch");
  const facility = at(closure, "facility");
  if (index === null || index === "") return "index_missing";
  if (codes.includes(null)) return "code_not_boolean";
  if (!epoch(start)) return "start_not_epoch";
  if (indefinite === null) return "indefinite_not_boolean";
  if (indefinite === "false" && !epoch(end)) return "end_not_epoch";
  if (indefinite === "false" && Number(end) < Number(start)) return "window_inverted";
  if (typeof facility !== "string" || facility === "") return "facility_missing";
  return null;
}

const rank = (facility: string) => (FACILITY_RANK.includes(facility) ? FACILITY_RANK.indexOf(facility) : FACILITY_RANK.length);

function order(a: ActiveClosure, b: ActiveClosure): number {
  if (a.confirmed !== b.confirmed) return a.confirmed ? -1 : 1;
  const byRank = rank(a.facility) - rank(b.facility);
  if (byRank !== 0) return byRank;
  return a.index < b.index ? -1 : a.index > b.index ? 1 : 0;
}

/** Every row of the feed's `data`, at `nowS` (epoch seconds): the active Full closures in cap order (R1-R5). */
export function parseLcsFeed(data: unknown[], nowS: number): LcsParse {
  const out: LcsParse = { rows: data.length, full: 0, active: 0, refused: [], closures: [] };
  for (const row of data) {
    const lcs = at(row, "lcs");
    if (lcs === null || typeof lcs !== "object" || Array.isArray(lcs)) {
      out.refused.push({ index: null, reason: "row_not_object" });
      continue;
    }
    const rawIndex = at(lcs, "index");
    const index = typeof rawIndex === "string" ? rawIndex : null;
    const kind = at(lcs, "closure", "typeOfClosure");
    if (typeof kind !== "string") {
      out.refused.push({ index, reason: "type_missing" });
      continue;
    }
    if (kind !== FULL_CLOSURE) continue;
    out.full += 1;
    const closure = at(lcs, "closure");
    const reason = refusal(closure, index);
    if (reason !== null) {
      out.refused.push({ index, reason });
      continue;
    }
    const begin = position(at(lcs, "location", "begin", "beginLongitude"), at(lcs, "location", "begin", "beginLatitude"));
    const end = position(at(lcs, "location", "end", "endLongitude"), at(lcs, "location", "end", "endLatitude"));
    if (typeof begin === "string" || typeof end === "string") {
      out.refused.push({ index, reason: typeof begin === "string" ? begin : (end as LcsRefusal) });
      continue;
    }
    const [placed, pickedUp, cancelled] = ["1097", "1098", "1022"].map((n) => at(closure, `code${n}`, `isCode${n}`) === "true");
    const start = Number(at(closure, "closureTimestamp", "closureStartEpoch"));
    const indefinite = at(closure, "closureTimestamp", "isClosureEndIndefinite") === "true";
    const live = placed || (start <= nowS && (indefinite || nowS <= Number(at(closure, "closureTimestamp", "closureEndEpoch"))));
    if (cancelled || pickedUp || !live) continue;
    out.active += 1;
    out.closures.push({ index: index!, confirmed: placed!, facility: at(closure, "facility") as string, rings: closureRings(begin, end) });
  }
  out.closures.sort(order);
  return out;
}

/** Greedy fill in cap order: a closure's rings stay whole; one that does not fit is dropped and counted (R5). */
export function capClosures(closures: ActiveClosure[], cap = CLOSURES_STORED_MAX_POLYGONS): CappedClosures {
  const features: ClosurePolygon[] = [];
  let kept = 0;
  let dropped = 0;
  for (const closure of closures) {
    if (features.length + closure.rings.length > cap) {
      dropped += 1;
      continue;
    }
    kept += 1;
    for (const ring of closure.rings) {
      features.push({ type: "Feature", properties: { lcs_index: closure.index }, geometry: { type: "Polygon", coordinates: [ring] } });
    }
  }
  return { geojson: { type: "FeatureCollection", features }, kept, dropped };
}
