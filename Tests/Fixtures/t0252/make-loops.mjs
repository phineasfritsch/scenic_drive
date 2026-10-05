#!/usr/bin/env node
/**
 * Writes loops.json - the shared retrace fixture (T-0252 R7). `node Tests/Fixtures/t0252/make-loops.mjs`.
 *
 * Points are INTEGER microdegrees ([latE6, lonE6]); both sides divide by 1e6, so no decimal parser is in the
 * comparison. Seven synthetic shapes near UCLA plus two loops built from the RECORDED t0221
 * santa-monica-topanga geometry. `fraction_bits` / `acceptable` are recorded from the SWIFT original
 * (LoopRetraceParityTests prints its own bits on a mismatch) and are carried over from an existing loops.json
 * by name, so re-running this never invents an expectation. `max_ulps` is 0 - exact - unless a `witness` names
 * the libm call two implementations round differently (T-0252 Log); it is carried over the same way.
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "loops.json");
const BASE = [34.0689, -118.4452];

function line(start, bearing, spacing, count) {
  const rad = (bearing * Math.PI) / 180;
  const dLat = (Math.cos(rad) * spacing) / 111_132.0;
  const dLon = (Math.sin(rad) * spacing) / (111_320.0 * Math.cos((start[0] * Math.PI) / 180));
  return Array.from({ length: count }, (_, i) => [start[0] + dLat * i, start[1] + dLon * i]);
}
const last = (pts) => pts[pts.length - 1];
const chain = (start, legs) => {
  let pts = [start];
  for (const [bearing, spacing, count] of legs) pts = pts.concat(line(last(pts), bearing, spacing, count).slice(1));
  return pts;
};
const recorded = (file) => JSON.parse(readFileSync(join(HERE, "..", "t0221", "santa-monica-topanga", file), "utf8"))
  .paths[0].points.coordinates.map(([lon, lat]) => [lat, lon]);

const square = chain(BASE, [[0, 50, 21], [90, 50, 21], [180, 50, 21], [270, 50, 21]]);
const outAndBack = (() => { const out = line(BASE, 0, 50, 41); return out.concat(out.slice().reverse().slice(1)); })();
const lollipop = (() => {
  const stem = line(BASE, 0, 50, 13);
  const head = chain(last(stem), [[0, 50, 17], [90, 50, 17], [180, 50, 17], [270, 50, 17]]);
  return stem.concat(head.slice(1), stem.slice().reverse().slice(1));
})();
const figureEight = chain(BASE, [[0, 50, 21], [90, 50, 11], [180, 50, 41], [270, 50, 11], [0, 50, 21]]);
const parallelStreets = chain(BASE, [[0, 50, 30], [90, 40, 4], [180, 50, 30]]);
const spur = chain(BASE, [[0, 50, 21], [90, 50, 9], [0, 50, 7], [180, 50, 7], [90, 50, 13], [180, 50, 21], [270, 50, 21]]);
const carriageways = (() => {
  const out = line(BASE, 45, 40, 30);
  const offset = (14 / 111_195.080234) * Math.SQRT1_2;
  return out.concat(out.slice().reverse().map(([lat, lon]) => [lat - offset, lon + offset / Math.cos((lat * Math.PI) / 180)]));
})();
const scenic = recorded("lambda-6.json");
const fastest = recorded("fastest.json");

const shapes = [
  ["square", "synthetic: four 1 km legs", square],
  ["out-and-back", "synthetic: 2 km north and the same road back", outAndBack],
  ["lollipop", "synthetic: a 600 m stem out and back around a 800 m square", lollipop],
  ["figure-eight", "synthetic: crosses its own path at right angles", figureEight],
  ["parallel-streets", "synthetic: up one street, back down the next 120 m over", parallelStreets],
  ["spur", "synthetic: a square with a 300 m dead-end spur driven out and back", spur],
  ["carriageways", "synthetic: out on 045 and back on the other carriageway 14 m over", carriageways],
  ["topanga-scenic-out-fastest-back", "recorded t0221 lambda-6 out, fastest.json reversed back", scenic.concat(fastest.slice().reverse())],
  ["topanga-scenic-out-and-back", "recorded t0221 lambda-6 out and the same road back", scenic.concat(scenic.slice().reverse())],
];

const previous = existsSync(OUT) ? new Map(JSON.parse(readFileSync(OUT, "utf8")).loops.map((l) => [l.name, l])) : new Map();
const loops = shapes.map(([name, source, pts]) => ({
  name,
  source,
  fraction_bits: previous.get(name)?.fraction_bits ?? "PENDING",
  acceptable: previous.get(name)?.acceptable ?? null,
  max_ulps: previous.get(name)?.max_ulps ?? 0,
  ...(previous.get(name)?.witness ? { witness: previous.get(name).witness } : {}),
  points: pts.map(([lat, lon]) => [Math.round(lat * 1e6), Math.round(lon * 1e6)]),
}));
writeFileSync(OUT, `${JSON.stringify({ unit: "microdegrees [lat, lon]", loops })}\n`);
console.log(loops.map((l) => `${l.name} ${l.points.length} points`).join("\n"));
