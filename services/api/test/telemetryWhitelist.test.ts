/**
 * T-0279 acceptance 2 (R3, R4, P-PRIV-05): the /telemetry WHITELIST, table-tested through the shipped
 * ROUTES['/telemetry'] at EVERY bound. A refused body is 400 invalid_request with zero Analytics Engine writes and no
 * reservation; an accepted bound is 200 with exactly its point written.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NOW, post, telemetryRig, type Point } from "./telemetryHarness";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
});

const p = (name: string, label = "", cell = "", d1 = 0, d2 = 0): Point =>
  ({ indexes: [name], blobs: [name, label, cell], doubles: [d1, d2] });
const one = (point: unknown) => ({ events: [point] });
const raw = (point: Point, doubles: string) => JSON.stringify(one(point)).replace(/"doubles":\[[^\]]*\]/, `"doubles":${doubles}`);

/** An H3 index from its fields (R4): mode 1, resolution 5, `base`, digits 1-5, and `tail` in digits 6-15. */
function cell(base: number, digits: number[], tail = 7, mode = 1n, reserved = 0n, res = 5n): string {
  let v = (mode << 59n) | (reserved << 56n) | (res << 52n) | (BigInt(base) << 45n);
  for (let r = 1; r <= 15; r++) v |= BigInt(r <= 5 ? digits[r - 1]! : tail) << BigInt((15 - r) * 3);
  return v.toString(16);
}
const CELL = "850dab63fffffff";
const plan = (c: string) => one(p("plan_requested", "scenic", c, 30));

const ACCEPTED: [string, unknown][] = [
  ["the cell built from fields equals the published cell", plan(cell(6, [6, 5, 3, 3, 0]))],
  ["base cell 0, all digits 0", plan(cell(0, [0, 0, 0, 0, 0]))],
  ["base cell 121 (the last), all digits 6", plan(cell(121, [6, 6, 6, 6, 6]))],
  ["pentagon base cell 4, first non-zero digit 2 after a 0", plan(cell(4, [0, 2, 1, 1, 1]))],
  ["pentagon base cell 117, all digits 0", plan(cell(117, [0, 0, 0, 0, 0]))],
  ["plan_requested budget 0", one(p("plan_requested", "loop", CELL, 0))],
  ["plan_requested budget 1440", one(p("plan_requested", "road_trip", CELL, 1440))],
  ["drive_completed 0% and 0 deviations", one(p("drive_completed", "", "", 0, 0))],
  ["drive_completed 100% and 1000 deviations", one(p("drive_completed", "", "", 100, 1000))],
  ["drive_abandoned 100%", one(p("drive_abandoned", "", "", 100))],
  ["corpus_activated 0", one(p("corpus_activated", "", "", 0))],
  ["corpus_activated 2147483647", one(p("corpus_activated", "", "", 2147483647))],
  ["20 events, the per-request maximum", { events: Array.from({ length: 20 }, () => p("drive_started")) }],
];

const REFUSED: [string, unknown][] = [
  // the envelope
  ["a JSON array body", [p("drive_started")]],
  ["a null body", null],
  ["events not an array", { events: p("drive_started") }],
  ["no events", { events: [] }],
  ["21 events, one past the per-request maximum", { events: Array.from({ length: 21 }, () => p("drive_started")) }],
  ["an extra top-level key", { events: [p("drive_started")], device: "x" }],
  ["no events key", { points: [p("drive_started")] }],
  // the point's keys
  ["an extra point key", one({ ...p("drive_started"), timestamp: 1 })],
  ["a coordinate beside the point", one({ ...p("drive_started"), lat: 34.05 })],
  ["a missing doubles key", one({ indexes: ["drive_started"], blobs: ["drive_started", "", ""] })],
  ["a point that is an array", one(["drive_started"])],
  ["a point that is null", one(null)],
  // the name
  ["the kind raw value paywall, not a wire name", one(p("paywall"))],
  ["an unknown name", one(p("plan_requested_v2"))],
  ["a prototype name __proto__", one(p("__proto__"))],
  ["a prototype name toString", one(p("toString"))],
  ["a prototype name hasOwnProperty", one(p("hasOwnProperty"))],
  ["indexes naming another event", one({ ...p("drive_started"), indexes: ["preview_shown"] })],
  ["two indexes", one({ ...p("drive_started"), indexes: ["drive_started", "drive_started"] })],
  ["no indexes", one({ ...p("drive_started"), indexes: [] })],
  // blobs
  ["two blobs", one({ ...p("drive_started"), blobs: ["drive_started", ""] })],
  ["four blobs", one({ ...p("drive_started"), blobs: ["drive_started", "", "", ""] })],
  ["a numeric blob", one({ ...p("drive_started"), blobs: ["drive_started", 0, ""] })],
  ["a cell that is a one-element array (it stringifies to a valid cell)", one({ ...p("plan_requested", "scenic", CELL, 30), blobs: ["plan_requested", "scenic", [CELL]] })],
  ["a label on a label-less event", one(p("preview_shown", "x"))],
  ["a long label", one(p("plan_result", "a".repeat(4096)))],
  ["a feature outside the closed enum", one(p("plan_requested", "Scenic", CELL, 30))],
  ["an empty feature", one(p("plan_requested", "", CELL, 30))],
  ["a result kind with a trailing space", one(p("plan_result", "routed "))],
  ["a handoff app outside the enum", one(p("handoff_tapped", "here_maps"))],
  ["a post-drive answer outside the enum", one(p("post_drive_answer", "maybe"))],
  ["a surprise reason outside the enum", one(p("surprise_not_this", "other"))],
  ["a paywall step as a label", one(p("paywall_shown", "shown"))],
  // the cell
  ["a cell on an event that carries none", one(p("drive_started", "", CELL))],
  ["a cell on handoff_tapped", one(p("handoff_tapped", "waze", CELL))],
  ["plan_requested with no cell", plan("")],
  ["an uppercase cell", plan(CELL.toUpperCase())],
  ["a 16-digit cell", plan(`0${CELL}`)],
  ["a 14-digit cell", plan(CELL.slice(1))],
  ["a non-hex cell", plan("850dab63ffffffg")],
  ["a mode-0 index (bit 59 clear)", plan(cell(6, [6, 5, 3, 3, 0], 7, 0n).padStart(15, "0"))],
  ["a resolution-4 cell", plan(cell(6, [6, 5, 3, 3, 7], 7, 1n, 0n, 4n))],
  ["a resolution-6 field", plan(cell(6, [6, 5, 3, 3, 0], 7, 1n, 0n, 6n))],
  ["reserved bits 56-58 set", plan(cell(6, [6, 5, 3, 3, 0], 7, 1n, 1n))],
  ["base cell 122, one past the last", plan(cell(122, [0, 0, 0, 0, 0]))],
  ["base cell 127", plan(cell(127, [0, 0, 0, 0, 0]))],
  ["digit 1 = 7", plan(cell(6, [7, 5, 3, 3, 0]))],
  ["digit 5 = 7", plan(cell(6, [6, 5, 3, 3, 7]))],
  ["digit 6 = 6 (finer than resolution 5)", plan(cell(6, [6, 5, 3, 3, 0], 6))],
  ["the last digit not 7", plan(`${CELL.slice(0, 14)}e`)],
  ["pentagon base cell 4, leading digit 1", plan(cell(4, [1, 0, 0, 0, 0]))],
  ["pentagon base cell 117, first non-zero digit 1 after zeros", plan(cell(117, [0, 0, 0, 1, 2]))],
  // the doubles, at every bound
  ["plan_requested budget -1", one(p("plan_requested", "scenic", CELL, -1))],
  ["plan_requested budget 1441", one(p("plan_requested", "scenic", CELL, 1441))],
  ["plan_requested budget 30.5", one(p("plan_requested", "scenic", CELL, 30.5))],
  ["plan_requested v2 = 1", one(p("plan_requested", "scenic", CELL, 30, 1))],
  ["drive_completed -1%", one(p("drive_completed", "", "", -1, 0))],
  ["drive_completed 101%", one(p("drive_completed", "", "", 101, 0))],
  ["drive_completed 98.7%", one(p("drive_completed", "", "", 98.7, 0))],
  ["drive_completed -1 deviations", one(p("drive_completed", "", "", 50, -1))],
  ["drive_completed 1001 deviations", one(p("drive_completed", "", "", 50, 1001))],
  ["drive_abandoned -1%", one(p("drive_abandoned", "", "", -1))],
  ["drive_abandoned 101%", one(p("drive_abandoned", "", "", 101))],
  ["drive_abandoned v2 = 1", one(p("drive_abandoned", "", "", 50, 1))],
  ["corpus_activated -1", one(p("corpus_activated", "", "", -1))],
  ["corpus_activated 2147483648", one(p("corpus_activated", "", "", 2147483648))],
  ["preview_shown v1 = 1", one(p("preview_shown", "", "", 1))],
  ["preview_shown v2 = 1", one(p("preview_shown", "", "", 0, 1))],
  ["paywall_converted v1 = 0.5", one(p("paywall_converted", "", "", 0.5))],
  ["a string double", one({ ...p("drive_started"), doubles: ["0", 0] })],
  ["a null double", one({ ...p("drive_started"), doubles: [null, 0] })],
  ["one double", one({ ...p("drive_started"), doubles: [0] })],
  ["three doubles", one({ ...p("drive_started"), doubles: [0, 0, 0] })],
  ["an unused double of -0", raw(p("drive_started"), "[-0,0]")],
  ["a percent of -0", raw(p("drive_abandoned"), "[0,-0]")],
  ["a double past Number.MAX_VALUE", raw(p("drive_started"), "[1e999,0]")],
  ["a body that is not JSON", "{not json"],
];

describe("POST /telemetry whitelist through ROUTES['/telemetry'] (T-0279 R3/R4, P-PRIV-05)", () => {
  it("every ruled bound and closed-enum edge is accepted and written exactly", async () => {
    expect(cell(6, [6, 5, 3, 3, 0])).toBe(CELL);
    for (const [name, body] of ACCEPTED) {
      const rig = telemetryRig();
      const events = (body as { events: Point[] }).events;
      expect([name, await post(rig.env, body)]).toEqual([name, { status: 200, json: { written: events.length } }]);
      expect([name, rig.writes]).toStrictEqual([name, events]);
      // Written in the device's own key order whatever the sender's: the rebuilt point, never the body's object.
      expect([name, rig.writes.map((w) => Object.keys(w as object))]).toEqual([name, events.map(() => ["blobs", "doubles", "indexes"])]);
    }
  });

  it("every other body is 400 invalid_request with zero writes and no reservation", async () => {
    for (const [name, body] of REFUSED) {
      const rig = telemetryRig();
      const answer = await post(rig.env, body);
      expect([name, answer.status, answer.json.error]).toEqual([name, 400, "invalid_request"]);
      expect([name, rig.writes, rig.quota.state()]).toEqual([name, [], {}]);
    }
  });
});
