/**
 * The per-request GraphHopper custom model, and the gate in front of request-supplied ones.
 *
 * Two halves of one safety property (plan "GraphHopper profiles", :98-110 and P-SAFE-01 :242):
 *
 *   1. `buildCustomModel` is the ONLY thing allowed to write a custom model. The safety gates
 *      (`road_access == PRIVATE || NO`, the unpaved `surface` list, `road_class == TRACK`) live in
 *      car_scenic_base.json on the server and are not restated here, because a per-request model that
 *      mentioned them could relax them. So the model this builds never names `road_access` or `surface`
 *      at all - not in a condition, not in an area property. That is an assertable property of the
 *      serialised output, which a comment saying "do not add surface here" would not be.
 *
 *   2. `rejectCustomModel` refuses a request-supplied body that mentions either, ANYWHERE. It walks keys
 *      and string values recursively, because the interesting smuggling route is not a top-level key - it
 *      is an `else_if` three clauses down, or a property on an `areas` feature.
 *
 * Deliberately conservative: it refuses on substring, case-insensitively, so `ROAD_ACCESS` and
 * `road_access_x` are refused too. Over-refusing a client body costs one request; under-refusing routes a
 * driver onto a private dirt track.
 *
 * lambda comes from the budget bisection over [0, 8] (plan :116). Out of range THROWS. It must never be
 * clamped: a clamp turns "the caller has a bug" into "the route is quietly not the one that was asked
 * for", and the bisection's feasibility argument depends on the bracket being real.
 */

/** The bisection's bracket, plan :116. */
export const LAMBDA_MIN = 0;
export const LAMBDA_MAX = 8;
/** Closures KV holds <= 50 polygons (plan :110, :144). More than that is a corrupt feed, not a big day. */
export const MAX_CLOSURE_POLYGONS = 50;
/** Encoded values a request-supplied model may not touch; they are the safety gates (plan :98). */
export const FORBIDDEN_ENCODED_VALUES = ["road_access", "surface"] as const;
/** Decimals kept when a multiplier is serialised. Fixed so the model is byte-stable across boxes. */
export const MULTIPLIER_DECIMALS = 6;
/** A body nested deeper than this is refused rather than walked. */
const MAX_WALK_DEPTH = 64;

export type CustomModelRefusal =
  | "lambda_not_finite"
  | "lambda_out_of_range"
  | "closures_not_feature_collection"
  | "closure_not_polygon"
  | "too_many_closure_polygons";

/** Thrown by the builder. Never returned, never swallowed, never turned into a clamp. */
export class CustomModelError extends Error {
  constructor(
    public readonly reason: CustomModelRefusal,
    message: string,
  ) {
    super(message);
    this.name = "CustomModelError";
  }
}

export interface ClosurePolygon {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: number[][][] };
  properties?: Record<string, unknown> | null;
  id?: string;
}

export interface ClosureCollection {
  type: "FeatureCollection";
  features: ClosurePolygon[];
}

/** One GraphHopper `priority` clause: exactly one of if/else_if/else, plus a STRING multiply_by. */
export interface CustomModelClause {
  if?: string;
  else_if?: string;
  else?: string;
  multiply_by: string;
}

export interface CustomModelAreas {
  type: "FeatureCollection";
  features: { type: "Feature"; id: string; properties: Record<string, never>; geometry: ClosurePolygon["geometry"] }[];
}

export interface CustomModel {
  priority: CustomModelClause[];
  areas?: CustomModelAreas;
}

/** The three scenic_score bands of plan :105-107, as numbers. */
export interface ScenicBandMultipliers {
  /** scenic_score >= 7 */
  high: number;
  /** scenic_score >= 4 */
  mid: number;
  /** everything else, motorway included - penalised, never excluded */
  low: number;
}

function assertLambda(lambda: number): void {
  if (typeof lambda !== "number" || !Number.isFinite(lambda)) {
    throw new CustomModelError("lambda_not_finite", `lambda must be a finite number, got ${String(lambda)}`);
  }
  if (lambda < LAMBDA_MIN || lambda > LAMBDA_MAX) {
    throw new CustomModelError(
      "lambda_out_of_range",
      `lambda must be within [${LAMBDA_MIN}, ${LAMBDA_MAX}], got ${lambda}`,
    );
  }
}

/**
 * plan :105-107. lambda = 0 leaves every band at 1, which is what makes lambda = 0 the fastest route and
 * the bisection's lower bracket. Rising lambda only ever pushes a band down.
 */
export function scenicBandMultipliers(lambda: number): ScenicBandMultipliers {
  assertLambda(lambda);
  return { high: 1, mid: 1 / (1 + 0.5 * lambda), low: 1 / (1 + lambda) };
}

/** GraphHopper wants multiply_by as a string. Trailing zeros are dropped so 1 stays "1" (plan :105). */
export function formatMultiplier(value: number): string {
  return Number(value.toFixed(MULTIPLIER_DECIMALS)).toString();
}

function closureGeometries(closures: ClosureCollection | null): ClosurePolygon["geometry"][] {
  if (closures === null) return [];
  if (typeof closures !== "object" || (closures as ClosureCollection).type !== "FeatureCollection" || !Array.isArray(closures.features)) {
    throw new CustomModelError("closures_not_feature_collection", "closures must be a GeoJSON FeatureCollection or null");
  }
  if (closures.features.length > MAX_CLOSURE_POLYGONS) {
    throw new CustomModelError(
      "too_many_closure_polygons",
      `closures carry ${closures.features.length} polygons, more than the ${MAX_CLOSURE_POLYGONS} allowed`,
    );
  }
  return closures.features.map((feature, index) => {
    const geometry = feature?.geometry;
    if (!geometry || geometry.type !== "Polygon" || !Array.isArray(geometry.coordinates)) {
      throw new CustomModelError("closure_not_polygon", `closure feature ${index} is not a Polygon`);
    }
    return { type: "Polygon" as const, coordinates: geometry.coordinates };
  });
}

/**
 * Build the per-request model. The closure features are REBUILT from their geometry alone with empty
 * properties and a generated id: whatever the KV feed put in `properties` never reaches the router, so the
 * "never mentions road_access or surface" property holds for closures we did not write either.
 */
export function buildCustomModel(lambda: number, closures: ClosureCollection | null): CustomModel {
  const bands = scenicBandMultipliers(lambda);
  const geometries = closureGeometries(closures);

  const priority: CustomModelClause[] = [
    { if: "scenic_score >= 7", multiply_by: formatMultiplier(bands.high) },
    { else_if: "scenic_score >= 4", multiply_by: formatMultiplier(bands.mid) },
    { else: "", multiply_by: formatMultiplier(bands.low) },
    // anti rat-run, plan :108
    { if: "road_class == RESIDENTIAL && scenic_score < 7", multiply_by: "0.5" },
  ];

  if (geometries.length === 0) return { priority };

  const ids = geometries.map((_, index) => `closure_${index + 1}`);
  priority.push({ if: ids.map((id) => `in_${id}`).join(" || "), multiply_by: "0" });

  return {
    priority,
    areas: {
      type: "FeatureCollection",
      features: geometries.map((geometry, index) => ({
        type: "Feature" as const,
        id: ids[index]!,
        properties: {},
        geometry,
      })),
    },
  };
}

function mentioned(text: string): string | null {
  const lowered = text.toLowerCase();
  for (const word of FORBIDDEN_ENCODED_VALUES) {
    if (lowered.includes(word)) return word;
  }
  return null;
}

function walk(value: unknown, path: string, depth: number): string | null {
  if (depth > MAX_WALK_DEPTH) return `custom model nests deeper than ${MAX_WALK_DEPTH} levels at ${path}`;
  if (typeof value === "string") {
    const word = mentioned(value);
    return word === null ? null : `custom model mentions ${word} at ${path}`;
  }
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const problem = walk(value[index], `${path}[${index}]`, depth + 1);
      if (problem !== null) return problem;
    }
    return null;
  }
  if (value !== null && typeof value === "object") {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      const here = path === "" ? key : `${path}.${key}`;
      const word = mentioned(key);
      if (word !== null) return `custom model mentions ${word} at ${here}`;
      const problem = walk(child, here, depth + 1);
      if (problem !== null) return problem;
    }
  }
  return null;
}

/**
 * The refusal of plan :98. Returns the reason a request-supplied body may not be forwarded, or null when
 * it may - the shape src/ro.ts already uses for `readOnlyProblem`.
 *
 * It walks the WHOLE body, not a `custom_model` key, so it is correct whether the caller hands it the
 * model or the request that carries one. That also means the Worker must add its own `details=surface,
 * road_access` (plan :120) to the upstream request AFTER this gate, never to the body it checks.
 */
export function rejectCustomModel(body: unknown): string | null {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    return "custom model must be a JSON object";
  }
  return walk(body, "", 0);
}
