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
export function via(route: RouteOption, fastest: RouteOption, others: RouteOption[] = []): string {
  const names = (r: RouteOption) => [...new Set(r.roads.map(baseRoad))];
  const onFastest = new Set(names(fastest));
  const rivals = others.filter((o) => o.id !== route.id && o.id !== fastest.id).map((o) => new Set(names(o)));
  const own = names(route).filter((n) => !onFastest.has(n));
  return distinguishingPair(own, rivals).join(" & ") || "Local roads";
}

/** Two of `own`, in driving order, that no rival route also has both of; else the first two. */
function distinguishingPair(own: string[], rivals: Set<string>[]): string[] {
  const unique = own.find((n) => rivals.every((r) => !r.has(n)));
  if (unique) return [unique, ...own.filter((n) => n !== unique)].slice(0, 2).sort((a, b) => own.indexOf(a) - own.indexOf(b));
  for (let i = 0; i < own.length; i += 1) {
    for (let j = i + 1; j < own.length; j += 1) {
      if (rivals.every((r) => !(r.has(own[i]!) && r.has(own[j]!)))) return [own[i]!, own[j]!];
    }
  }
  return own.slice(0, 2);
}

/** "Mulholland Highway (The Snake)" and "Mulholland Highway" are one road to a driver. */
export function baseRoad(name: string): string {
  return shortRoad(name.replace(/\s*\(.*\)\s*$/, ""));
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
  return directionsUrl(route.coordinates[0]!, route.coordinates[route.coordinates.length - 1]!, route.waypoints);
}

/** Google Maps directions from start to end through up to 9 waypoints, all [lon, lat]. */
export function directionsUrl(start: [number, number], end: [number, number], waypoints: [number, number][]): string {
  const ll = ([lon, lat]: [number, number]) => `${lat},${lon}`;
  const params = new URLSearchParams({ api: "1", origin: ll(start), destination: ll(end), travelmode: "driving" });
  if (waypoints.length > 0) params.set("waypoints", waypoints.slice(0, 9).map(ll).join("|"));
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}
