import { SCORE_STOPS } from "../map/routeLayers";
import type { RouteOption } from "../plan/types";
import { useAppearance } from "./useAppearance";

function lerp(a: string, b: string, t: number): string {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i]! - v) * t)).join(",")})`;
}

/** The same ramp the map line uses (routeLayers SCORE_STOPS), so the strip doubles as its legend. */
export function scoreColor(score: number | null, stops: [number, string][]): string {
  const s = score ?? 0;
  if (s <= stops[0]![0]) return stops[0]![1];
  for (let i = 1; i < stops.length; i += 1) {
    const [x1, c1] = stops[i]!;
    const [x0, c0] = stops[i - 1]!;
    if (s <= x1) return lerp(c0, c1, (s - x0) / (x1 - x0));
  }
  return stops[stops.length - 1]![1];
}

function runLengths(route: RouteOption): { metres: number; score: number | null }[] {
  return route.runs.map((run) => {
    let metres = 0;
    for (let i = run.from; i < run.to; i += 1) {
      const [lon1, lat1] = route.coordinates[i]!;
      const [lon2, lat2] = route.coordinates[i + 1]!;
      const x = (lon2 - lon1) * Math.cos(((lat1 + lat2) / 2) * (Math.PI / 180));
      metres += Math.hypot(x, lat2 - lat1) * 111_320;
    }
    return { metres, score: run.score };
  });
}

/** The drive from start to finish, coloured by how scenic each stretch is. */
export function ScenicStrip({ route, compact = false }: { route: RouteOption; compact?: boolean }) {
  const stops = SCORE_STOPS[useAppearance()];
  const runs = runLengths(route);
  const total = runs.reduce((s, r) => s + r.metres, 0) || 1;
  return (
    <div className={compact ? "strip strip-compact" : "strip"} role="img" aria-label="How scenic each stretch of the drive is, start to finish">
      {runs.map((r, i) => (
        <span key={i} style={{ flexGrow: r.metres / total, background: scoreColor(r.score, stops) }} />
      ))}
    </div>
  );
}

export function StripLegend() {
  const stops = SCORE_STOPS[useAppearance()];
  return (
    <div className="strip-legend" aria-hidden>
      <span>Ordinary</span>
      {stops.map(([score, color]) => (
        <span key={score} className="strip-legend-swatch" style={{ background: color }} />
      ))}
      <span>Scenic</span>
    </div>
  );
}
