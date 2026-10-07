/**
 * The served region (T-0293 R2, R3): the union of the la and sfbay region bboxes, each inclusive on all four edges.
 *
 * ONE source of truth: the region file under services/etl/regions/<id>/, which the ETL cuts the graph and corpus with, is
 * IMPORTED here and bundled into the Worker at build time - compiled in, never fetched, never restated as a literal.
 * A bbox, not a polygon: the region file carries no other geometry, and a coordinate inside the box is routable.
 */
import la from "../../etl/regions/la/region.json";
import sfbay from "../../etl/regions/sfbay/region.json";
import type { LatLon } from "./latLon";

export interface Bbox {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
}

export const SERVED_REGIONS: readonly { id: string; bbox: Bbox }[] = [
  { id: la.id, bbox: la.bbox },
  { id: sfbay.id, bbox: sfbay.bbox },
];

/** True when `point` lies in `box`, edges included. */
export function inBbox(point: LatLon, box: Bbox): boolean {
  return point.lat >= box.min_lat && point.lat <= box.max_lat && point.lon >= box.min_lon && point.lon <= box.max_lon;
}

/** True when `point` lies in any served region's bbox. */
export function inServedRegion(point: LatLon): boolean {
  return SERVED_REGIONS.some((region) => inBbox(point, region.bbox));
}
