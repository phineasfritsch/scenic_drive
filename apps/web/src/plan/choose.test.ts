import { describe, expect, it } from "vitest";
import demo from "../data/demo.json";
import { budgetForBest, choose } from "./choose";
import type { Corridor, DemoData, RouteOption } from "./types";

const data = demo as unknown as DemoData;

function route(id: string, minutes: number, score: number): RouteOption {
  return {
    id,
    kind: id === "fast" ? "fastest" : "scenic",
    timeS: minutes * 60,
    distanceM: minutes * 1000,
    score: { value: score, mean: score, episodes: 0, dudFraction: 0 },
    coordinates: [],
    runs: [],
    roads: [],
    motorwayM: 0,
    sharedWithFastest: 0,
    waypoints: [],
  };
}

const corridor: Corridor = {
  id: "c",
  title: "c",
  blurb: "",
  from: { name: "a", at: [0, 0] },
  to: { name: "b", at: [1, 1] },
  fastest: route("fast", 20, 0.3),
  alternatives: [route("short", 25, 0.5), route("mid", 30, 0.7), route("long", 45, 0.9)],
  provenance: "",
};

describe("choose", () => {
  it("never recommends a route over fastest + budget (the budget is a ceiling)", () => {
    for (let budget = 0; budget <= 30; budget += 1) {
      const { recommended } = choose(corridor, budget);
      expect(recommended.timeS).toBeLessThanOrEqual(corridor.fastest.timeS + budget * 60);
    }
  });

  it("picks the best score among routes that fit", () => {
    expect(choose(corridor, 5).recommended.id).toBe("short");
    expect(choose(corridor, 10).recommended.id).toBe("mid");
    expect(choose(corridor, 24).recommended.id).toBe("mid");
    expect(choose(corridor, 25).recommended.id).toBe("long");
  });

  it("falls back to the fastest route, honestly, when nothing scenic fits", () => {
    const zero = choose(corridor, 0);
    expect(zero.recommended.id).toBe("fast");
    expect(zero.honestFailure).toBe(true);
    const dull = choose({ ...corridor, alternatives: [route("dull", 22, 0.4)] }, 10);
    expect(dull.recommended.id).toBe("fast");
    expect(dull.honestFailure).toBe(true);
  });

  it("marks exactly one option recommended and flags the ones over budget", () => {
    const { options } = choose(corridor, 10);
    expect(options.filter((o) => o.recommended)).toHaveLength(1);
    expect(options.find((o) => o.route.id === "long")!.fitsBudget).toBe(false);
  });

  it("budgetForBest reaches the top-scoring route", () => {
    expect(budgetForBest(corridor)).toBe(25);
  });
});

describe("the recorded LA demo data", () => {
  it("has both corridors, each with scenic alternatives slower than the fastest", () => {
    expect(data.corridors.map((c) => c.id)).toEqual(["topanga-malibu", "zuma-agoura"]);
    for (const c of data.corridors) {
      expect(c.alternatives.length).toBeGreaterThan(0);
      for (const a of c.alternatives) expect(a.timeS).toBeGreaterThan(c.fastest.timeS);
    }
  });

  it("recommends a scenic route on Topanga to Malibu at a 15 minute budget", () => {
    const topanga = data.corridors[0]!;
    const { recommended, honestFailure } = choose(topanga, 15);
    expect(honestFailure).toBe(false);
    expect(recommended.kind).toBe("scenic");
    expect(recommended.timeS).toBeLessThanOrEqual(topanga.fastest.timeS + 15 * 60);
  });
});
