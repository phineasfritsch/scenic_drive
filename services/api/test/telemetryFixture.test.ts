/**
 * T-0279 acceptance 1: the Worker accepts every data point the Swift encoder writes (Tests/Fixtures/t0279, recorded
 * by TelemetryWireFixtureTests from Sources/Telemetry) and writes each to Analytics Engine unchanged - full equality
 * per row, through the shipped ROUTES['/telemetry']. R4: every published H3 res-5 cell of uber/h3 passes the cell rule.
 */
import pentagonRaw from "../../../Tests/TelemetryTests/Fixtures/pentagon05points.txt?raw";
import randRaw from "../../../Tests/TelemetryTests/Fixtures/rand05centers.txt?raw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MAX_TELEMETRY_EVENTS_PER_REQUEST, parseTelemetryBody, TELEMETRY_WIRE } from "../src/telemetryPoint";
import { dailyTelemetry, FIXTURE, FIXTURE_LINES, NOW, post, telemetryRig } from "./telemetryHarness";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
});

const cellsOf = (raw: string) => [...new Set(raw.split(/\r?\n/).filter((l) => l.length > 0).map((l) => l.split(" ")[0]!))];

describe("POST /telemetry over the Swift encoder's own JSON (T-0279 R10)", () => {
  it("the fixture is the 36 rows the Swift suite pins, one JSON object per line", () => {
    expect(FIXTURE_LINES.length).toBe(36);
    expect(FIXTURE_LINES.map((line) => JSON.stringify(JSON.parse(line)))).toEqual(FIXTURE_LINES);
  });

  it("every fixture row is accepted alone and written to Analytics Engine as the identical {indexes, blobs, doubles}", async () => {
    for (const row of FIXTURE) {
      const rig = telemetryRig();
      expect(await post(rig.env, { events: [row] })).toEqual({ status: 200, json: { written: 1 } });
      expect(rig.writes).toStrictEqual([row]);
      expect(rig.quota.state()).toEqual(dailyTelemetry(1));
    }
  });

  it("the whole fixture, in requests of MAX_TELEMETRY_EVENTS_PER_REQUEST, is written in order and byte-identical", async () => {
    const rig = telemetryRig();
    for (let at = 0; at < FIXTURE.length; at += MAX_TELEMETRY_EVENTS_PER_REQUEST) {
      const chunk = FIXTURE.slice(at, at + MAX_TELEMETRY_EVENTS_PER_REQUEST);
      expect(await post(rig.env, { events: chunk })).toEqual({ status: 200, json: { written: chunk.length } });
    }
    expect(rig.writes).toStrictEqual(FIXTURE);
    expect(rig.writes.map((w) => JSON.stringify(w))).toEqual(FIXTURE_LINES);
    expect(rig.quota.state()).toEqual(dailyTelemetry(36));
  });

  it("the fixture's wire names and labels are exactly the whitelist's: fifteen names, every label of every closed enum", () => {
    const labels: Record<string, string[]> = {};
    for (const row of FIXTURE) labels[row.blobs[0]!] = [...new Set([...(labels[row.blobs[0]!] ?? []), row.blobs[1]!])].sort();
    const ruled = Object.fromEntries(Object.entries(TELEMETRY_WIRE).map(([name, rule]) => [name, [...rule.labels].sort()]));
    expect(Object.keys(labels).sort()).toEqual(Object.keys(ruled).sort());
    expect(Object.keys(ruled).length).toBe(15);
    expect(labels).toEqual(ruled);
  });

  it("every published res-5 cell of uber/h3 (rand05centers and the pentagon ring) is an accepted plan_requested cell", () => {
    const cells = [...cellsOf(randRaw), ...cellsOf(pentagonRaw)];
    // Measured 2026-10-06: each file's distinct cells, concatenated, are 5532.
    expect(cells.length).toBe(5532);
    const refused: string[] = [];
    for (const cell of cells) {
      const point = { indexes: ["plan_requested"], blobs: ["plan_requested", "scenic", cell], doubles: [30, 0] };
      if (!parseTelemetryBody({ events: [point] }).ok) refused.push(cell);
    }
    expect(refused).toEqual([]);
  });
});
