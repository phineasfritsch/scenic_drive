/**
 * T-0330 R2: every /plan 200 says whether it CONTINUED the drive - `continued: true` exactly when the body is
 * planReroute's answer from a recalled plan_token, false on every fresh plan /plan falls back to. Every row drives
 * `handlePlan` (what ROUTES["/plan"] runs) and its whole answer EQUALS a body recomputed here from the committed
 * builders - planReroute for a continued row, planScenic for a fresh one - through the same closures picker and
 * reservation, plus the minted token and the ruled marker.
 */
import { describe, expect, it } from "vitest";
import { closurePicker } from "../src/closuresNearest";
import { withClosuresHazard } from "../src/closuresStore";
import type { LatLon } from "../src/latLon";
import { handlePlan } from "../src/plan";
import { kvPlanTokens, type PlanTokenKv } from "../src/planToken";
import { planReroute } from "../src/reroutePlanner";
import { planScenic } from "../src/scenicPlanner";
import { guardedPlan } from "../src/upstream";
import { curveRouter, harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY, type Recording } from "./planHarness";

const TOKEN = "0f1e2d3c-4b5a-4968-8776-655443322110";
const MINTED = "00000000-0000-4000-8000-000000000001";
const PINS = [{ lat: 34.03, lon: -118.52 }, { lat: 34.04, lon: -118.56 }, { lat: 34.06, lon: -118.58 }];
const RECORD = { device: "device-1", place: "la:topanga", pins: PINS, lambda: 7.75 };
const FAST_MS = 1_200_000;
const MINUTES = 20;
const CEILING_MS = FAST_MS + MINUTES * 60_000;
const curve = (atFour: number) =>
  curveRouter(FAST_MS, (l) => (l === 4 ? atFour : FAST_MS + l * 100_000), [1, 2, 3, 4, 5], [1, 10, 11, 12, 13, 14]);

type Store = "bound" | "unbound" | "throws";
interface Row {
  label: string;
  router: () => Recording;
  store: Store;
  record: Record<string, unknown> | null;
  minutes: number;
  firstPin: number | null;
}

function kv(row: Row): PlanTokenKv | null {
  if (row.store === "unbound") return null;
  const rows: Record<string, string> = row.record ? { [`plan:device-1:${TOKEN}`]: JSON.stringify(row.record) } : {};
  return {
    async get(key) {
      if (row.store === "throws") throw new Error("kv down");
      return rows[key] ?? null;
    },
    async put() {},
  };
}

function rig(row: Row) {
  const h = harness(row.router());
  const store = kv(row);
  (h.deps as { plans?: unknown }).plans = store === null ? null : kvPlanTokens(store, () => MINTED);
  return h;
}

const body = (row: Row) => ({ ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: row.minutes,
  ...(row.firstPin === null ? {} : { reroute: { token: TOKEN, first_pin: row.firstPin } }) });

async function answer(row: Row) {
  const response = await handlePlan(planRequest(body(row)), {}, rig(row).deps);
  return { status: response.status, body: (await response.json()) as Record<string, unknown> };
}

/** The body recomputed from the builders: planReroute through the row's remaining pins, else planScenic. */
async function oracle(row: Row, continued: boolean) {
  const h = rig(row);
  const deps = h.deps;
  const snapshot = await deps.closures();
  const picker = closurePicker(snapshot.closures);
  const who = await deps.identify(planRequest(body(row)));
  const origin: LatLon = SANTA_MONICA_TOPANGA_BODY.origin;
  const destination = (await deps.resolvePlace("la:topanga"))!;
  const budget = row.minutes * 60;
  const record = row.record as typeof RECORD;
  const plan = await guardedPlan(deps.upstream, who, async (call) => continued
    ? (await planReroute(call, deps.routerBase, origin, destination, budget, record.pins.slice(row.firstPin!),
      record.lambda, picker.pick, picker.returned))!
    : planScenic(call, deps.routerBase, origin, destination, budget, picker.pick, picker.returned, false));
  const whole = { ...withClosuresHazard(plan, snapshot, picker.dropped(), picker.crosses()), 
    plan_token: row.store === "unbound" ? null : MINTED, continued };
  return { status: 200, body: JSON.parse(JSON.stringify(whole)) as Record<string, unknown> };
}

const topanga = (label: string, over: Partial<Row>): Row =>
  ({ label, router: () => SANTA_MONICA_TOPANGA, store: "bound", record: RECORD, minutes: 25, firstPin: 1, ...over });
const ceiling = (label: string, atFour: number, over: Partial<Row> = {}): Row =>
  ({ label, router: () => curve(atFour), store: "bound", record: { ...RECORD, lambda: 4 }, minutes: MINUTES,
    firstPin: 0, ...over });

/** Recalled rows: each is the rest of THIS drive. */
const CONTINUED: Row[] = [
  topanga("recalled, first_pin 0", { firstPin: 0 }),
  topanga("recalled, first_pin 1", { firstPin: 1 }),
  topanga("recalled, first_pin 3 (the stored count)", { firstPin: 3 }),
  ceiling("recalled, exactly at the ceiling", CEILING_MS),
];

/** Unusable rows, each with the one-variable OPPOSITE that makes it usable again (the meta-test runs those). */
const FRESH: [Row, Row][] = [
  [topanga("no reroute at all", { firstPin: null }), topanga("opposite: a reroute", {})],
  [topanga("unknown or expired token (KV answers null)", { record: null }), topanga("opposite: remembered", {})],
  [topanga("PLANS unbound", { store: "unbound" }), topanga("opposite: bound", {})],
  [topanga("KV read throws", { store: "throws" }), topanga("opposite: read answers", {})],
  [topanga("another device's record", { record: { ...RECORD, device: "device-2" } }), topanga("opposite: this device", {})],
  [topanga("another place", { record: { ...RECORD, place: "la:malibu" } }), topanga("opposite: this place", {})],
  [topanga("first_pin 4, past the 3 pins", { firstPin: 4 }), topanga("opposite: first_pin 3", { firstPin: 3 })],
  [ceiling("over the ceiling by 1 s", CEILING_MS + 1000), ceiling("opposite: at the ceiling", CEILING_MS)],
];

describe("POST /plan says whether it continued the drive (T-0330 R2)", () => {
  it("a recalled token's answer is planReroute's body, whole, with continued true", async () => {
    for (const row of CONTINUED) {
      expect([row.label, await answer(row)]).toEqual([row.label, await oracle(row, true)]);
    }
  });

  it("every unusable token's answer is the fresh plan's body, whole, with continued false", async () => {
    for (const [row] of FRESH) {
      expect([row.label, await answer(row)]).toEqual([row.label, await oracle(row, false)]);
    }
  });

  it("meta: no fresh row ignores its variant - each opposite continues, and the marker is the only difference in kind", async () => {
    for (const [row, opposite] of FRESH) {
      const got = await answer(opposite);
      expect([opposite.label, got]).toEqual([opposite.label, await oracle(opposite, true)]);
      expect([row.label, (await answer(row)).body.continued, got.body.continued]).toEqual([row.label, false, true]);
    }
  });
});
