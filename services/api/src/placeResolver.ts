/**
 * /plan's destination place id -> its coordinate, over the D1 `places` table (T-0256 R6; DDL in
 * migrations/0001_places.sql). No row is null (404 unknown_place). A row that is not a finite in-range coordinate,
 * or a D1 that cannot answer (the table not yet migrated), THROWS - the handler answers 503 planning_unavailable
 * with zero upstream calls, because "we could not tell" is not "no such place".
 */
import type { LatLon } from "./latLon";

export const PLACE_QUERY = "SELECT lat, lon FROM places WHERE id = ?1";

export function d1PlaceResolver(db: D1Database): (id: string) => Promise<LatLon | null> {
  return async (id) => {
    const row = await db.prepare(PLACE_QUERY).bind(id).first<{ lat: unknown; lon: unknown }>();
    if (row === null) return null;
    const { lat, lon } = row;
    if (typeof lat !== "number" || !(lat >= -90 && lat <= 90) || typeof lon !== "number" || !(lon >= -180 && lon <= 180)) {
      throw new Error(`place ${id} has no valid coordinate`);
    }
    return { lat, lon };
  };
}
