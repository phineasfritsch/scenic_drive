import { describe, expect, it } from "vitest";
import demo from "./data/demo.json";
import { via } from "./format";
import type { DemoData } from "./plan/types";

const data = demo as unknown as DemoData;

describe("via", () => {
  it("never names the same road twice (Mulholland Hwy and its 'The Snake' stretch are one road)", () => {
    for (const c of data.corridors) {
      const all = [c.fastest, ...c.alternatives];
      for (const r of c.alternatives) {
        const parts = via(r, c.fastest, all).split(" & ");
        expect(new Set(parts).size).toBe(parts.length);
      }
    }
  });

  it("tells every scenic alternative of a corridor apart", () => {
    for (const c of data.corridors) {
      const all = [c.fastest, ...c.alternatives];
      const labels = c.alternatives.map((r) => via(r, c.fastest, all));
      expect(new Set(labels).size).toBe(labels.length);
    }
  });
});
