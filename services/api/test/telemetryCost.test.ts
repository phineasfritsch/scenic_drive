/**
 * T-0279 acceptance 2 (R5, R6, P-COST-01): /telemetry's spend control through the shipped ROUTES['/telemetry'].
 * KILL pauses before the body is read; the device's day of events (quota kind "telemetry") is reserved in one
 * transaction BEFORE the first Analytics Engine write; a request that would cross the cap is refused whole.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dailyQuota, DAILY_TELEMETRY_QUOTA } from "../src/quota";
import { MAX_TELEMETRY_EVENTS_PER_REQUEST } from "../src/telemetryPoint";
import { fakeKv } from "./doFake";
import { DEVICE, dailyTelemetry, NOW, post, telemetryRig, type Point } from "./telemetryHarness";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
});

const started: Point = { indexes: ["drive_started"], blobs: ["drive_started", "", ""], doubles: [0, 0] };
const events = (n: number) => ({ events: Array.from({ length: n }, () => started) });
const exhausted = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-07T00:00:00.000Z" } };

describe("POST /telemetry spend control (T-0279 R5/R6, P-COST-01)", () => {
  it("the ruled caps: 20 events a request, 200 a device a day on every tier", () => {
    expect([MAX_TELEMETRY_EVENTS_PER_REQUEST, DAILY_TELEMETRY_QUOTA]).toEqual([20, 200]);
    expect((["anon", "free", "paid"] as const).map((tier) => dailyQuota("telemetry", tier))).toEqual([200, 200, 200]);
  });

  it("KILL=1 or the KV KILL_SWITCH key is 503 telemetry_paused before the body is read: zero writes, no reservation", async () => {
    for (const source of [{ KILL: "1" }, { KILL_SWITCH: fakeKv({ KILL: "1" }) }, { KILL_SWITCH: fakeKv({}, true) }]) {
      const rig = telemetryRig(source);
      expect(await post(rig.env, "{not json")).toEqual({ status: 503, json: { error: "telemetry_paused" } });
      expect(await post(rig.env, events(1))).toEqual({ status: 503, json: { error: "telemetry_paused" } });
      expect([rig.writes, rig.quota.state()]).toEqual([[], {}]);
    }
  });

  it("KILL other than exactly 1 does not pause telemetry", async () => {
    const rig = telemetryRig({ KILL: "0", KILL_SWITCH: fakeKv({ KILL: "0" }) });
    expect(await post(rig.env, events(1))).toEqual({ status: 200, json: { written: 1 } });
  });

  it("the request's events are reserved in one transaction before the first Analytics Engine write", async () => {
    const rig = telemetryRig();
    expect(await post(rig.env, events(3))).toEqual({ status: 200, json: { written: 3 } });
    expect(rig.quotaAtWrite).toEqual([dailyTelemetry(3), dailyTelemetry(3), dailyTelemetry(3)]);
  });

  it("200 events a day in requests of 20; the 201st is 429 quota_exhausted with zero writes", async () => {
    const rig = telemetryRig();
    for (let i = 0; i < 10; i++) expect(await post(rig.env, events(20))).toEqual({ status: 200, json: { written: 20 } });
    expect(await post(rig.env, events(1))).toEqual(exhausted);
    expect([rig.writes.length, rig.quota.state()]).toEqual([200, dailyTelemetry(200)]);
  });

  it("a request that would cross the cap is refused whole; one that lands on it is written", async () => {
    const rig = telemetryRig();
    rig.quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-06", plan: 0, loop: 0, telemetry: 190 });
    expect(await post(rig.env, events(11))).toEqual(exhausted);
    expect([rig.writes, rig.quota.state()]).toEqual([[], dailyTelemetry(190)]);
    expect(await post(rig.env, events(10))).toEqual({ status: 200, json: { written: 10 } });
    expect([rig.writes.length, rig.quota.state()]).toEqual([10, dailyTelemetry(200)]);
  });

  it("a new UTC day and another device each start at zero", async () => {
    const rig = telemetryRig();
    rig.quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 0, loop: 0, telemetry: 200 });
    expect(await post(rig.env, events(2))).toEqual({ status: 200, json: { written: 2 } });
    expect(await post(rig.env, events(1), { device: "1f8b6d5e-1a2b-4c3d-8e9f-0123456789ab" })).toEqual({ status: 200, json: { written: 1 } });
    expect(rig.quota.state()).toEqual({
      ...dailyTelemetry(2),
      "device:1f8b6d5e-1a2b-4c3d-8e9f-0123456789ab": { daily: { day: "2026-10-06", plan: 0, loop: 0, telemetry: 1 } },
    });
  });

  it("an unbound TELEMETRY or QUOTA is 503 telemetry_unavailable with zero writes", async () => {
    for (const unbound of [{ TELEMETRY: undefined }, { QUOTA: undefined }]) {
      const rig = telemetryRig(unbound);
      expect(await post(rig.env, events(1))).toEqual({ status: 503, json: { error: "telemetry_unavailable" } });
      expect([rig.writes, rig.quota.state()]).toEqual([[], {}]);
    }
  });

  it("GET is 405 and nothing is written", async () => {
    const rig = telemetryRig();
    expect(await post(rig.env, undefined, { method: "GET" })).toEqual({ status: 405, json: { error: "POST only" } });
    expect([rig.writes, rig.quota.state()]).toEqual([[], {}]);
  });
});
