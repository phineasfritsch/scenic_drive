/**
 * T-0382: the Worker's model gate covers every encoded value the SHIPPED base profile hard-gates on.
 *
 * The list is never restated here. GATE_IDS is read from services/routing/profiles/car_scenic_base.json: the
 * identifiers in the `if` of every `multiply_by: "0"` priority clause, in profile order. BUILDER_IDS is what
 * buildCustomModel's own output reads. FORBIDDEN_ENCODED_VALUES must equal GATE_IDS minus BUILDER_IDS, and the
 * overlap must be exactly road_class (the builder's MINOR_CONDITION reads it; refusing it refuses every plan).
 *
 * Each derived name then gets a GENERATED near-miss corpus, placed in every clause shape and sent through
 * scenicPlanner.route - the function every /plan router request goes through, which runs rejectCustomModel on
 * the model just before the router call. Oracle: refused iff the lowered text contains a derived name (the
 * gate's documented substring rule), else forwarded once with the model unchanged.
 */
import { describe, expect, it } from "vitest";
import profile from "../../routing/profiles/car_scenic_base.json";
import { buildCustomModel, FORBIDDEN_ENCODED_VALUES, LAMBDA_MAX, LAMBDA_MIN, type ClosureCollection } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { RouteError } from "../src/routePath";
import { route, SCENIC_PROFILE } from "../src/scenicPlanner";
import { harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

type Clause = { if?: string; else_if?: string; else?: string; multiply_by?: string };

const IDENTIFIER = /[A-Za-z_][A-Za-z0-9_]*/g;
/** A GraphHopper condition names an encoded value in lower case; enum constants (PRIVATE, GRADE3) are upper. */
function identifiersOf(condition: string): string[] {
  return (condition.match(IDENTIFIER) ?? []).filter((t) => /^[a-z]/.test(t) && t !== "true" && t !== "false");
}
const unique = (xs: string[]) => [...new Set(xs)];
const conditionOf = (c: Clause) => c.if ?? c.else_if ?? c.else ?? "";

const ZERO_CLAUSES = (profile.priority as Clause[]).filter((c) => c.multiply_by === "0");
const GATE_IDS = unique(ZERO_CLAUSES.flatMap((c) => identifiersOf(conditionOf(c))));

const SQUARE = { type: "Polygon" as const, coordinates: [[[-118.5, 34], [-118.4, 34], [-118.4, 34.1], [-118.5, 34]]] };
const ONE_CLOSURE = { type: "FeatureCollection", features: [{ type: "Feature", geometry: SQUARE }] } as ClosureCollection;
const BUILDER_IDS = unique([LAMBDA_MIN, LAMBDA_MAX].flatMap((lambda) => [null, ONE_CLOSURE]
  .flatMap((closures) => buildCustomModel(lambda, closures).priority.flatMap((c) => identifiersOf(conditionOf(c))))));

const DERIVED = GATE_IDS.filter((name) => !BUILDER_IDS.includes(name));

describe("T-0382 FORBIDDEN_ENCODED_VALUES is bound to the shipped base profile", () => {
  it("equals the identifiers of every multiply_by 0 clause of car_scenic_base.json, in order, minus the builder's own", () => {
    expect(ZERO_CLAUSES.map((c) => typeof c.if)).toEqual(ZERO_CLAUSES.map(() => "string"));
    expect(GATE_IDS.filter((name) => BUILDER_IDS.includes(name))).toEqual(["road_class"]);
    expect([...FORBIDDEN_ENCODED_VALUES]).toEqual(DERIVED);
  });
});

const SEPARATORS = [" ", "\t", ";", "_", "-", ",", "|", "x"];
const FAMILIES = ["affix", "case", "compound", "deletion", "empty", "exact", "operator", "separator"];
type Row = { family: string; text: string };

/** Every row is a function of the name: nothing here is a hand-picked spelling of one name. */
function corpus(name: string): Row[] {
  const rows: Row[] = [{ family: "exact", text: name }, { family: "empty", text: "" }];
  rows.push({ family: "case", text: name.toUpperCase() });
  rows.push({ family: "case", text: name[0]!.toUpperCase() + name.slice(1) });
  rows.push({ family: "case", text: [...name].map((ch, at) => (at % 2 === 1 ? ch.toUpperCase() : ch)).join("") });
  for (let at = 0; at < name.length; at += 1) rows.push({ family: "deletion", text: name.slice(0, at) + name.slice(at + 1) });
  for (const sep of SEPARATORS) {
    for (let at = 0; at <= name.length; at += 1) rows.push({ family: "separator", text: name.slice(0, at) + sep + name.slice(at) });
  }
  for (const text of [`x${name}`, `${name}x`, `${name}_x`, `in_${name}`]) rows.push({ family: "affix", text });
  for (const text of [`${name};paved`, `paved;${name}`, `${name};${name}`]) rows.push({ family: "compound", text });
  for (const text of [`${name} == GRADE3`, `${name} != NO`, `!${name}`, `${name} >= 3`, `${name} < 1`, `true && ${name}`,
    `${name} || false`, `(${name} == BAD)`, `scenic_score >= 7 && ${name} == X`, `road_class == PRIMARY || ${name}`]) {
    rows.push({ family: "operator", text });
  }
  return rows;
}

interface Shape { shape: string; path: (text: string) => string; model: (text: string) => unknown }
const SHAPES: Shape[] = [
  { shape: "priority if", path: () => "priority[0].if", model: (t) => ({ priority: [{ if: t, multiply_by: "1" }] }) },
  { shape: "priority else_if", path: () => "priority[1].else_if",
    model: (t) => ({ priority: [{ if: "scenic_score >= 7", multiply_by: "1" }, { else_if: t, multiply_by: "0.5" }] }) },
  { shape: "speed if", path: () => "speed[0].if", model: (t) => ({ speed: [{ if: t, limit_to: "100" }] }) },
  { shape: "speed else_if", path: () => "speed[1].else_if",
    model: (t) => ({ speed: [{ if: "true", multiply_by: "0.9" }, { else_if: t, multiply_by: "0.5" }] }) },
  { shape: "areas property", path: () => "areas.features[0].properties.note",
    model: (t) => ({ priority: [{ if: "in_a", multiply_by: "0" }],
      areas: { type: "FeatureCollection", features: [{ type: "Feature", id: "a", properties: { note: t }, geometry: SQUARE }] } }) },
  { shape: "object key", path: (t) => `priority[0].${t}`, model: (t) => ({ priority: [{ [t]: "1", multiply_by: "1" }] }) },
];

/** The oracle reads the PROFILE-derived list, never the constant under test. */
const firstMention = (text: string) => DERIVED.find((name) => text.toLowerCase().includes(name)) ?? null;

const POINTS = [{ lat: 34.02, lon: -118.49 }, { lat: 34.07, lon: -118.6 }];
const FORWARDED = new Error("forwarded to the router");

/** One model through the shipped route(): what it threw, and the model the router received (or the call count). */
async function send(model: unknown): Promise<{ outcome: string; routerGot: unknown }> {
  const sent: string[] = [];
  const call = async (_url: string, init?: RequestInit): Promise<Response> => {
    sent.push(String(init?.body));
    throw FORWARDED;
  };
  let outcome = "resolved";
  try {
    await route(call, "http://router.test", POINTS, SCENIC_PROFILE, model);
  } catch (error) {
    outcome = error === FORWARDED ? "forwarded"
      : error instanceof RouteError ? `${error.reason}: ${error.message}` : `threw ${String(error)}`;
  }
  const routerGot = sent.length === 1 ? (JSON.parse(sent[0]!) as { custom_model: unknown }).custom_model : sent.length;
  return { outcome, routerGot };
}

function expected(shape: Shape, text: string): { outcome: string; routerGot: unknown } {
  const word = firstMention(text);
  return word === null
    ? { outcome: "forwarded", routerGot: shape.model(text) }
    : { outcome: `router_refused: refusing to send: custom model mentions ${word} at ${shape.path(text)}`, routerGot: 0 };
}

describe("T-0382 scenicPlanner.route refuses every clause shape reading a shipped gate value", () => {
  it("the corpus is generated for every derived name: every family, refused and forwarded rows both present", () => {
    const seen = DERIVED.map((name) => {
      const rows = corpus(name);
      return { name, families: unique(rows.map((r) => r.family)).sort(),
        refused: rows.some((r) => firstMention(r.text) !== null), forwarded: rows.some((r) => firstMention(r.text) === null),
        exactAlwaysRefused: rows.filter((r) => r.family === "exact" || r.family === "operator").every((r) => firstMention(r.text) === name) };
    });
    expect(seen).toEqual(DERIVED.map((name) => ({ name, families: FAMILIES, refused: true, forwarded: true, exactAlwaysRefused: true })));
  });

  for (const name of DERIVED) {
    it(`${name}: every near miss in every clause shape is refused iff it contains a gate name, else forwarded unchanged`, async () => {
      const rows = corpus(name).flatMap((row) => SHAPES.map((shape) => ({ shape, row })));
      const actual: unknown[] = [];
      for (const { shape, row } of rows) actual.push({ shape: shape.shape, ...row, ...(await send(shape.model(row.text))) });
      expect(actual).toEqual(rows.map(({ shape, row }) => ({ shape: shape.shape, ...row, ...expected(shape, row.text) })));
    });
  }
});

describe("T-0382 ROUTES['/plan'] never takes a client model naming a gate value", () => {
  it("handlePlan refuses a body carrying custom_model that reads each derived name: 400, zero upstream calls", async () => {
    const answers: unknown[] = [];
    for (const name of DERIVED) {
      const h = harness(SANTA_MONICA_TOPANGA);
      const custom_model = { priority: [{ if: `${name} == X`, multiply_by: "1" }] };
      const response = await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, custom_model }), {}, h.deps);
      answers.push([name, response.status, ((await response.json()) as { error: string }).error, h.sent, h.events]);
    }
    expect(answers).toEqual(DERIVED.map((name) => [name, 400, "invalid_request", [], []]));
  });
});
