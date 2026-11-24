/**
 * Builds src/data/demo.json from the scenic router's recorded answers (Tests/Fixtures/t0239: GraphHopper 11 over
 * the real LA graph) and the curated LA seeds. It scores every route with the Worker's own RouteScore
 * (services/api/src/routeScore.ts), so the demo ranks routes exactly the way live /plan would.
 *
 *     npm run data
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";
import { decisionPoints, haversineMeters, tableRows } from "../../../services/api/src/planWaypoints.ts";
import { decodeRoutePath, overlap, wayIds, type RoutePath } from "../../../services/api/src/routePath.ts";
import { routeScoreOf } from "../../../services/api/src/routeScore.ts";
import type { Corridor, DemoData, RouteOption, ScenicRun, ScenicStop } from "../src/plan/types.ts";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../../..");
const LAMBDAS = [0, 2, 4, 6, 8];
const ROAD_MIN_METRES = 400;
const MOTORWAY = new Set(["motorway", "trunk"]);
/** Google Maps directions links accept up to 9 waypoints; the Worker hands the same decision points to Apple Maps. */
const GOOGLE_WAYPOINTS = 9;

const CORRIDORS = [
  {
    id: "topanga-malibu",
    title: "Topanga to Malibu",
    blurb: "Over Saddle Peak instead of down the canyon and along PCH.",
    from: "Topanga",
    to: "Malibu Civic Center",
  },
  {
    id: "zuma-agoura",
    title: "Zuma Beach to Agoura Hills",
    blurb: "Up from the coast through the Santa Monica Mountains.",
    from: "Zuma Beach",
    to: "Agoura Hills",
  },
];

const round5 = (n: number) => Math.round(n * 1e5) / 1e5;

function readPaths(corridor: string, file: string): { recorded: Record<string, string>; paths: RoutePath[] } {
  const body = JSON.parse(readFileSync(resolve(repo, "Tests/Fixtures/t0239", corridor, `${file}.json`), "utf8"));
  const paths = (body.paths as unknown[]).map((p) => decodeRoutePath(JSON.stringify({ paths: [p] })));
  return { recorded: body.recorded, paths };
}

function roadsOf(path: RoutePath): string[] {
  const names: string[] = [];
  for (const run of path.details.street_name ?? []) {
    const name = typeof run.value === "string" ? run.value.trim() : "";
    if (!name) continue;
    let metres = 0;
    for (let i = run.from; i < run.to; i += 1) metres += haversineMeters(path.coordinates[i]!, path.coordinates[i + 1]!);
    if (metres >= ROAD_MIN_METRES && names[names.length - 1] !== name && !names.includes(name)) names.push(name);
  }
  return names;
}

function runsOf(path: RoutePath): ScenicRun[] {
  const runs: ScenicRun[] = [];
  for (const row of tableRows(path)) {
    const last = runs[runs.length - 1];
    if (last && last.score === row.scenicScore && last.to === row.fromIndex) last.to = row.toIndex;
    else runs.push({ from: row.fromIndex, to: row.toIndex, score: row.scenicScore });
  }
  return runs;
}

function option(id: string, kind: RouteOption["kind"], path: RoutePath, fastest: RoutePath): RouteOption {
  const score = routeScoreOf(path);
  if (!score) throw new Error(`${id}: the route has no scorable roads`);
  const motorwayM = tableRows(path)
    .filter((row) => row.highway !== null && MOTORWAY.has(row.highway))
    .reduce((sum, row) => sum + row.meters, 0);
  return {
    id,
    kind,
    timeS: Math.round(path.timeMs / 1000),
    distanceM: Math.round(path.distanceM),
    score: { value: score.value, mean: score.mean, episodes: score.episodeCount, dudFraction: score.dudFraction },
    coordinates: path.coordinates.map(([lon, lat]) => [round5(lon), round5(lat)]),
    runs: runsOf(path),
    roads: roadsOf(path),
    motorwayM: Math.round(motorwayM),
    sharedWithFastest: overlap(wayIds(path), wayIds(fastest)),
    waypoints: decisionPoints(path, GOOGLE_WAYPOINTS).map(({ lat, lon }) => [round5(lon), round5(lat)]),
  };
}

function corridor(spec: (typeof CORRIDORS)[number]): Corridor {
  const { recorded, paths } = readPaths(spec.id, "fastest");
  const fastestPath = paths[0]!;
  const seen = new Set<string>([`${fastestPath.distanceM.toFixed(1)}|${fastestPath.timeMs}`]);
  const alternatives: RouteOption[] = [];
  for (const lambda of LAMBDAS) {
    for (const path of readPaths(spec.id, `alternatives-lambda-${lambda}`).paths) {
      const key = `${path.distanceM.toFixed(1)}|${path.timeMs}`;
      if (seen.has(key)) continue;
      seen.add(key);
      alternatives.push(option(`${spec.id}-l${lambda}-${alternatives.length}`, "scenic", path, fastestPath));
    }
  }
  alternatives.sort((a, b) => a.timeS - b.timeS);
  const [from, to] = [recorded.from!, recorded.to!].map((s) => s.split(",").map(Number) as [number, number]);
  return {
    id: spec.id,
    title: spec.title,
    blurb: spec.blurb,
    from: { name: spec.from, at: [from![1], from![0]] },
    to: { name: spec.to, at: [to![1], to![0]] },
    fastest: option(`${spec.id}-fastest`, "fastest", fastestPath, fastestPath),
    alternatives,
    provenance: `GraphHopper ${recorded.graphhopper} over the Los Angeles road graph`,
  };
}

function stops(): ScenicStop[] {
  const doc = parse(readFileSync(resolve(repo, "services/etl/regions/la/curated.yaml"), "utf8")) as {
    seeds: { id: string; name: string; hook: string; category: string; lat: number; lon: number }[];
  };
  return doc.seeds.map((s) => ({ id: s.id, name: s.name, hook: s.hook, category: s.category, at: [s.lon, s.lat] }));
}

const data: DemoData = { corridors: CORRIDORS.map(corridor), stops: stops() };
const out = resolve(here, "../src/data/demo.json");
writeFileSync(out, `${JSON.stringify(data)}\n`);
for (const c of data.corridors) {
  console.log(`${c.id}: fastest ${(c.fastest.timeS / 60).toFixed(1)} min, score ${c.fastest.score.value.toFixed(2)}`);
  for (const a of c.alternatives) {
    console.log(`  +${((a.timeS - c.fastest.timeS) / 60).toFixed(1)} min ${(a.distanceM / 1000).toFixed(1)} km score ${a.score.value.toFixed(2)} ${a.roads.slice(0, 4).join(", ")}`);
  }
}
console.log(`stops: ${data.stops.length}; wrote ${out}`);
