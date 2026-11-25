import type { LivePlace, LivePlan, Origin } from "../live/types";
import type { Corridor, RouteOption, ScenicRun } from "../plan/types";

/** What the map draws. Recorded drives and live plans both reduce to this, so MapView has one job. */
export interface MapScene {
  /** Changes exactly when the camera should refit. */
  fitKey: string;
  fitTo: [number, number][];
  /** The chosen route. `uniform` draws it in the route colour: live /plan sends no per-stretch scenic scores. */
  selected: { coordinates: [number, number][]; runs: ScenicRun[]; uniform: boolean } | null;
  others: { id: string; coordinates: [number, number][]; fastest: boolean }[];
  endpoints: { role: "from" | "to"; name: string; at: [number, number] }[];
}

/** A recorded drive. `planned` is false until the safety gate is accepted: no route is drawn before it. */
export function corridorScene(corridor: Corridor, selected: RouteOption, planned: boolean): MapScene {
  const all = [corridor.fastest, ...corridor.alternatives];
  return {
    fitKey: `corridor:${corridor.id}`,
    fitTo: all.flatMap((r) => r.coordinates),
    selected: planned ? { coordinates: selected.coordinates, runs: selected.runs, uniform: false } : null,
    others: planned
      ? all.filter((r) => r.id !== selected.id).map((r) => ({ id: r.id, coordinates: r.coordinates, fastest: r.kind === "fastest" }))
      : [],
    endpoints: [
      { role: "from", name: corridor.from.name, at: corridor.from.at },
      { role: "to", name: corridor.to.name, at: corridor.to.at },
    ],
  };
}

/** Santa Monica Mountains to downtown: the view before a trip has two ends. */
const REGION_VIEW: [number, number][] = [
  [-118.85, 33.95],
  [-118.2, 34.2],
];

/** A live plan, or the endpoints picked so far. */
export function liveScene(origin: Origin | null, destination: LivePlace | null, plan: LivePlan | null): MapScene {
  const endpoints: MapScene["endpoints"] = [];
  if (origin) endpoints.push({ role: "from", name: origin.name, at: [origin.lon, origin.lat] });
  if (destination) endpoints.push({ role: "to", name: destination.name, at: destination.at });
  const coordinates = plan?.route.coordinates ?? [];
  const points = endpoints.map((e) => e.at);
  const fitTo = coordinates.length > 0 ? coordinates : points.length >= 2 ? points : [...points, ...REGION_VIEW];
  return {
    fitKey: plan ? `live:plan:${coordinates.length}:${coordinates[0]?.join()}` : `live:${endpoints.map((e) => e.at.join()).join("|")}`,
    fitTo,
    selected: plan ? { coordinates, runs: [{ from: 0, to: coordinates.length - 1, score: null }], uniform: true } : null,
    others: [],
    endpoints,
  };
}
