import { describe, expect, it } from "vitest";
import places from "../data/places.json";
import { failureOf, planBody } from "./api";
import { mapPointOrigin, ORIGINS, searchPlaces, SUGGESTED } from "./places";
import type { LivePlace } from "./types";

const all = places as unknown as LivePlace[];

const decimals = (n: number) => (String(n).split(".")[1] ?? "").length;

describe("planBody (the only place a /plan body is built)", () => {
  it("never sends an origin with more than 2 decimals", () => {
    const body = planBody({ origin: { name: "x", lat: 34.069925, lon: -118.439883 }, placeId: "1", budgetMinutes: 15 });
    const origin = body.origin as { lat: number; lon: number };
    expect(decimals(origin.lat)).toBeLessThanOrEqual(2);
    expect(decimals(origin.lon)).toBeLessThanOrEqual(2);
    expect(origin).toEqual({ lat: 34.07, lon: -118.44 });
  });

  it("sends exactly the keys /plan whitelists, and back_roads only as true", () => {
    const plain = planBody({ origin: ORIGINS[0]!, placeId: "710486223536647933", budgetMinutes: 25 });
    expect(Object.keys(plain).sort()).toEqual(["budget_minutes", "destination", "origin"]);
    expect(plain.destination).toEqual({ place: "710486223536647933" });
    const back = planBody({ origin: ORIGINS[0]!, placeId: "1", budgetMinutes: 25, allBackRoads: true });
    expect(back.back_roads).toBe(true);
  });

  it("keeps the budget inside the API's [0, 180]", () => {
    expect(planBody({ origin: ORIGINS[0]!, placeId: "1", budgetMinutes: 999 }).budget_minutes).toBe(180);
    expect(planBody({ origin: ORIGINS[0]!, placeId: "1", budgetMinutes: -5 }).budget_minutes).toBe(0);
  });

  it("presets and map clicks are 2-decimal origins", () => {
    for (const o of [...ORIGINS, mapPointOrigin(-118.123456, 34.987654)]) {
      expect(decimals(o.lat)).toBeLessThanOrEqual(2);
      expect(decimals(o.lon)).toBeLessThanOrEqual(2);
    }
  });
});

describe("failureOf", () => {
  it("maps the API's error bodies", () => {
    expect(failureOf(429, { error: "quota_exhausted", resets_at: "2026-11-26T00:00:00Z" })).toEqual({
      kind: "quota_exhausted",
      resetsAt: "2026-11-26T00:00:00Z",
    });
    expect(failureOf(503, { error: "planning_unavailable" }).kind).toBe("offline");
    expect(failureOf(422, { error: "nothing_pretty", more_time_minutes: 40, back_roads_eta_s: 3000, back_roads_budget_minutes: 50 }))
      .toEqual({ kind: "nothing_pretty", moreTimeMinutes: 40, backRoadsEtaS: 3000, backRoadsBudgetMinutes: 50 });
    expect(failureOf(502, { error: "no_route", detail: "router answered 400" })).toEqual({ kind: "no_route" });
    expect(failureOf(500, { error: "weird" })).toEqual({ kind: "other", detail: "weird" });
  });
});

describe("places", () => {
  it("keeps 64-bit place ids exact, as strings", () => {
    const topanga = all.find((p) => p.name === "Topanga");
    expect(topanga?.id).toBe("710486223536647933");
    for (const p of all) expect(p.id).toMatch(/^\d+$/);
  });

  it("finds every suggested destination by its full name", () => {
    for (const name of SUGGESTED) expect(searchPlaces(all, name)[0]?.name).toBe(name);
  });

  it("ranks a name prefix above a word match above a substring", () => {
    const names = searchPlaces(all, "topanga", 20).map((p) => p.name);
    expect(names[0]!.toLowerCase().startsWith("topanga")).toBe(true);
    expect(searchPlaces(all, "")).toEqual([]);
  });
});
