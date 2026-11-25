import { kmBetween } from "./places";

/** The live slider's top. /plan accepts up to 180; past 90 min of detour nobody is still "taking the pretty way". */
export const LIVE_MAX_BUDGET_MINUTES = 90;
export const MIN_SUGGESTED_BUDGET = 15;
export const MAX_SUGGESTED_BUDGET = 60;

/**
 * Extra minutes per straight-line km. Measured 2026-11-24 over 100 LA trips against the served router: the fastest
 * drive takes about 1.0 min per straight-line km (p25 0.91, p75 1.19), and the plans that passed at +45 used a
 * median 0.6-0.7x the fastest time as extra on trips over 20 min. A fixed +20 failed most trips over 35 min.
 */
export const MINUTES_PER_KM = 0.7;

/** A starting budget that grows with the trip, rounded to 5 min. The user can always move it. */
export function suggestedBudget(from: [number, number], to: [number, number]): number {
  const raw = kmBetween(from, to) * MINUTES_PER_KM;
  const rounded = Math.round(raw / 5) * 5;
  return Math.max(MIN_SUGGESTED_BUDGET, Math.min(MAX_SUGGESTED_BUDGET, rounded));
}

/** Kilometres from where the route ends to the place itself: a peak or viewpoint may sit well off the nearest road. */
export function endGapKm(route: [number, number][], place: [number, number]): number {
  const end = route[route.length - 1];
  return end ? kmBetween(end, place) : 0;
}
