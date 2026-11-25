import type { ExpressionSpecification, GeoJSONSourceSpecification, LayerSpecification } from "maplibre-gl";
import type { ScenicStop } from "../plan/types";
import type { MapScene } from "./scene";
import type { Appearance } from "./basemap";

type FC = GeoJSON.FeatureCollection;

/**
 * Scenic score (the router's 0..10) to colour: ordinary road is slate, good road is the route blue, the best
 * stretches are scenic green. ScenicStrip uses the same stops, so the strip is a legend for the line.
 */
export const SCORE_STOPS: Record<Appearance, [number, string][]> = {
  light: [
    [0, "#94a3b8"],
    [4, "#2563eb"],
    [7, "#15803d"],
  ],
  dark: [
    [0, "#64748b"],
    [4, "#3b82f6"],
    [7, "#4ade80"],
  ],
};

export function scoreColorExpression(appearance: Appearance): ExpressionSpecification {
  const stops = SCORE_STOPS[appearance].flat();
  return ["interpolate", ["linear"], ["coalesce", ["get", "score"], 0], ...stops] as ExpressionSpecification;
}

function line(coordinates: [number, number][], properties: Record<string, unknown>): GeoJSON.Feature {
  return { type: "Feature", properties, geometry: { type: "LineString", coordinates } };
}

/** The selected route, one feature per run of equal scenic score. */
export function selectedRuns(selected: MapScene["selected"]): FC {
  if (!selected) return NONE;
  return {
    type: "FeatureCollection",
    features: selected.runs.map((run) =>
      line(selected.coordinates.slice(run.from, run.to + 1), { score: run.score, uniform: selected.uniform }),
    ),
  };
}

/** The other routes of the scene, thin and clickable. */
export function otherRoutes(others: MapScene["others"]): FC {
  return { type: "FeatureCollection", features: others.map((r) => line(r.coordinates, { id: r.id, fastest: r.fastest })) };
}

export function endpoints(points: MapScene["endpoints"]): FC {
  return {
    type: "FeatureCollection",
    features: points.map((p) => ({
      type: "Feature",
      properties: { role: p.role, name: p.name },
      geometry: { type: "Point", coordinates: p.at },
    })),
  };
}

const NONE: FC = { type: "FeatureCollection", features: [] };

export function stopsCollection(stops: ScenicStop[]): FC {
  return {
    type: "FeatureCollection",
    features: stops.map((s) => ({
      type: "Feature",
      properties: { id: s.id, name: s.name, hook: s.hook },
      geometry: { type: "Point", coordinates: s.at },
    })),
  };
}

export const EMPTY: GeoJSONSourceSpecification = { type: "geojson", data: { type: "FeatureCollection", features: [] } };
export const SOURCES = ["others", "selected", "endpoints", "stops"] as const;

export function overlayLayers(appearance: Appearance): LayerSpecification[] {
  const dark = appearance === "dark";
  const casing = dark ? "#0f172a" : "#ffffff";
  return [
    {
      id: "others-casing",
      type: "line",
      source: "others",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": casing, "line-width": 7, "line-opacity": 0.8 },
    },
    {
      id: "others",
      type: "line",
      source: "others",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": dark ? "#94a3b8" : "#64748b",
        "line-width": 4,
        "line-opacity": 0.55,
        "line-dasharray": ["case", ["get", "fastest"], ["literal", [1.2, 1.4]], ["literal", [1, 0]]],
      },
    },
    {
      id: "others-hit",
      type: "line",
      source: "others",
      paint: { "line-color": "#000000", "line-width": 18, "line-opacity": 0 },
    },
    {
      id: "selected-casing",
      type: "line",
      source: "selected",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": casing, "line-width": 11 },
    },
    {
      id: "selected",
      type: "line",
      source: "selected",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ["case", ["==", ["get", "uniform"], true], dark ? "#3b82f6" : "#2563eb", scoreColorExpression(appearance)],
        "line-width": 6,
      },
    },
    {
      id: "stops",
      type: "circle",
      source: "stops",
      paint: {
        "circle-radius": 5,
        "circle-color": casing,
        "circle-stroke-color": dark ? "#4ade80" : "#15803d",
        "circle-stroke-width": 3,
      },
    },
    {
      id: "endpoints",
      type: "circle",
      source: "endpoints",
      paint: {
        "circle-radius": ["case", ["==", ["get", "role"], "to"], 8, 6],
        "circle-color": ["case", ["==", ["get", "role"], "to"], dark ? "#fb923c" : "#ea580c", casing],
        "circle-stroke-color": ["case", ["==", ["get", "role"], "to"], casing, dark ? "#f8fafc" : "#0f172a"],
        "circle-stroke-width": 3,
      },
    },
    {
      id: "endpoint-labels",
      type: "symbol",
      source: "endpoints",
      layout: {
        "text-field": ["get", "name"],
        "text-font": ["Noto Sans Medium"],
        "text-size": 13,
        "text-offset": [0, 1.3],
        "text-anchor": "top",
      },
      paint: { "text-color": dark ? "#f8fafc" : "#0f172a", "text-halo-color": casing, "text-halo-width": 1.6 },
    },
  ];
}
