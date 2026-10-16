/**
 * A road trip's candidate stops and lodgings, from the server's own corpus (T-0316 R1, R3): the D1 table
 * trip_places (migrations/0009_trip_places.sql), whose CHECK constraints are the row validation. T-0318 R2: the read
 * is bounded to the route's box (tripPlacesBox.ts) - four numbers on a 0.1 degree grid, no request field - and the
 * lat index (migrations/0010_trip_places_lat.sql) makes D1 read only the box's latitude band. The splitter
 * (roadTrip.ts) still filters the rows exactly. A read that throws is the caller's "not searched", never "no lodging".
 */
import type { RoadTripPlace } from "./roadTrip";
import type { PlacesBox } from "./tripPlacesBox";

export const TRIP_PLACES_QUERY =
  "SELECT name, kind, score, lat, lon FROM trip_places WHERE lat >= ?1 AND lat <= ?2 AND lon >= ?3 AND lon <= ?4";

interface TripPlaceRow { name: string; kind: RoadTripPlace["kind"]; score: number; lat: number; lon: number }

export function d1TripPlaces(db: D1Database): (box: PlacesBox) => Promise<RoadTripPlace[]> {
  return async (box) => {
    const { results } = await db.prepare(TRIP_PLACES_QUERY).bind(box.south, box.north, box.west, box.east).all<TripPlaceRow>();
    return results.map((r) => ({ name: r.name, kind: r.kind, score: r.score, coordinate: { lat: r.lat, lon: r.lon } }));
  };
}
