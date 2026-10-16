/**
 * The box a trip's trip_places read is bounded to (T-0318 R3): every place that can be a corridor stop (5 km) or a
 * night (15 km) lies within OVERNIGHT_RADIUS_METERS of a route vertex, so the box is the vertices' extremes padded by
 * PLACES_PAD_METERS (15 km + 1 km for float rounding), rounded OUTWARD to a 0.1 degree grid (R4: no bind carries more
 * than one decimal place). Latitude: great-circle distance >= R x |dlat|. Longitude: the haversine gives
 * cos(lat1) cos(lat2) sin^2(dlon / 2) <= sin^2(d / 2R), and both cosines are >= cos of the band's largest |lat|.
 * A band reaching a pole, or a box past the antimeridian, reads the whole longitude range.
 */
import type { LatLon } from "./latLon";
import { EARTH_RADIUS_METERS } from "./roadTrip";

export const PLACES_PAD_METERS = 16_000;
export const PLACES_GRID_PER_DEGREE = 10;

export interface PlacesBox { south: number; north: number; west: number; east: number }

const degrees = (r: number) => (r * 180) / Math.PI;
const down = (x: number) => Math.floor(x * PLACES_GRID_PER_DEGREE) / PLACES_GRID_PER_DEGREE;
const up = (x: number) => Math.ceil(x * PLACES_GRID_PER_DEGREE) / PLACES_GRID_PER_DEGREE;

export function placesBox(vertices: LatLon[]): PlacesBox {
  let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
  for (const v of vertices) {
    minLat = Math.min(minLat, v.lat);
    maxLat = Math.max(maxLat, v.lat);
    minLon = Math.min(minLon, v.lon);
    maxLon = Math.max(maxLon, v.lon);
  }
  const pad = PLACES_PAD_METERS / EARTH_RADIUS_METERS;
  const south = Math.max(-90, down(minLat - degrees(pad)));
  const north = Math.min(90, up(maxLat + degrees(pad)));
  const ratio = Math.sin(pad / 2) / Math.cos((Math.max(-south, north) * Math.PI) / 180);
  if (!(ratio < 1)) return { south, north, west: -180, east: 180 };
  const lonPad = degrees(2 * Math.asin(ratio));
  const west = down(minLon - lonPad);
  const east = up(maxLon + lonPad);
  if (west < -180 || east > 180) return { south, north, west: -180, east: 180 };
  return { south, north, west, east };
}
