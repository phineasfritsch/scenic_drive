/** The demo's data model. A live PlanSource (services/api /plan) fills the same shapes. */

export interface Place {
  name: string;
  /** [lon, lat], GeoJSON order. */
  at: [number, number];
}

/** A run of the route's coordinates sharing one scenic score (0..10 as the router encodes it; null = unscored). */
export interface ScenicRun {
  from: number;
  to: number;
  score: number | null;
}

export interface RouteScoreSummary {
  /** RouteScore.value, 0..1: the planner's whole-route score. */
  value: number;
  /** Length-weighted mean of the per-road scenic score, 0..1. */
  mean: number;
  /** Stretches over 0.6 lasting at least 800 m. */
  episodes: number;
  /** Fraction of metres scoring 0.25 or less. */
  dudFraction: number;
}

export interface RouteOption {
  id: string;
  kind: "fastest" | "scenic";
  timeS: number;
  distanceM: number;
  score: RouteScoreSummary;
  /** [lon, lat] pairs. */
  coordinates: [number, number][];
  runs: ScenicRun[];
  /** Named roads in driving order, each at least a few hundred metres long. */
  roads: string[];
  motorwayM: number;
  /** Jaccard overlap of OSM way ids with the fastest route, 0..1. */
  sharedWithFastest: number;
  /** Up to 9 decision points ([lon, lat]) that pin a map app to this route, from the API's decisionPoints. */
  waypoints: [number, number][];
}

export interface Corridor {
  id: string;
  title: string;
  blurb: string;
  from: Place;
  to: Place;
  fastest: RouteOption;
  /** Distinct scenic alternatives, not including the fastest route. */
  alternatives: RouteOption[];
  /** Where the recording came from, shown in the "about this demo" note. */
  provenance: string;
}

export interface ScenicStop {
  id: string;
  name: string;
  hook: string;
  category: string;
  at: [number, number];
}

export interface DemoData {
  corridors: Corridor[];
  stops: ScenicStop[];
}
