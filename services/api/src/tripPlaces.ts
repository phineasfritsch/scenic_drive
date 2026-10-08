/**
 * A road trip's candidate stops and lodgings, from the server's own corpus (T-0316 R1, R3): the D1 table
 * trip_places (migrations/0009_trip_places.sql), whose CHECK constraints are the row validation. The read binds
 * nothing - no request value reaches it - and the splitter (roadTrip.ts) filters the rows exactly. A read that
 * throws is the caller's "not searched", never "no lodging".
 */
import type { RoadTripPlace } from "./roadTrip";

export const TRIP_PLACES_QUERY = "SELECT name, kind, score, lat, lon FROM trip_places";

interface TripPlaceRow { name: string; kind: RoadTripPlace["kind"]; score: number; lat: number; lon: number }

export function d1TripPlaces(db: D1Database): () => Promise<RoadTripPlace[]> {
  return async () => {
    const { results } = await db.prepare(TRIP_PLACES_QUERY).all<TripPlaceRow>();
    return results.map((r) => ({ name: r.name, kind: r.kind, score: r.score, coordinate: { lat: r.lat, lon: r.lon } }));
  };
}
