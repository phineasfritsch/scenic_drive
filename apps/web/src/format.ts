import type { RouteOption } from "./plan/types";

const METRES_PER_MILE = 1609.344;

export function minutes(seconds: number): string {
  const m = Math.round(seconds / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  return `${h} h ${m % 60} min`;
}

export function extra(seconds: number): string {
  const m = Math.round(seconds / 60);
  return m <= 0 ? "Fastest" : `+${m} min`;
}

export function miles(metres: number): string {
  const mi = metres / METRES_PER_MILE;
  return `${mi < 10 ? mi.toFixed(1) : Math.round(mi)} mi`;
}

/** RouteScore.value (0..1) as the 0-100 number the UI shows. */
export function scenicScore(value: number): number {
  return Math.round(value * 100);
}

/** "Mulholland Highway & Cold Canyon Road": the roads that make this route different from the fastest one. */
export function via(route: RouteOption, fastest: RouteOption): string {
  const distinct = route.roads.filter((r) => !fastest.roads.includes(r));
  const pick = (distinct.length > 0 ? distinct : route.roads).slice(0, 2).map(shortRoad);
  return pick.length === 0 ? "Local roads" : pick.join(" & ");
}

export function shortRoad(name: string): string {
  return name
    .replace(/\bBoulevard\b/g, "Blvd")
    .replace(/\bHighway\b/g, "Hwy")
    .replace(/\bRoad\b/g, "Rd")
    .replace(/\bDrive\b/g, "Dr")
    .replace(/\bCanyon\b/g, "Cyn")
    .replace(/^(North|South|East|West) /, "");
}

/** Google Maps directions pinned to this route by its decision points. Opened only by the user's own click. */
export function googleMapsUrl(route: RouteOption): string {
  const start = route.coordinates[0]!;
  const end = route.coordinates[route.coordinates.length - 1]!;
  const ll = ([lon, lat]: [number, number]) => `${lat},${lon}`;
  const params = new URLSearchParams({
    api: "1",
    origin: ll(start),
    destination: ll(end),
    travelmode: "driving",
  });
  if (route.waypoints.length > 0) params.set("waypoints", route.waypoints.map(ll).join("|"));
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}
