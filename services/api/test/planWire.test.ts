/**
 * T-0251 R7: the bytes the Swift client (Sources/ScenicAPIClient) is tested against ARE the Worker's.
 *
 * Every response the Worker can give a POST /plan by being driven is recorded under Tests/Fixtures/t0251/, and
 * this test re-drives each scenario and holds the Worker's status and response TEXT to those files by exact
 * equality. Change a status, a code or a field name here and this fails before the client's decoder is lied to.
 * The scenarios are T-0248's own: its counting-fake harness, its recordings, its ceiling-test routers, and the
 * shipped ROUTES table through SELF for the two rows only the production wiring produces.
 */
import { SELF } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import { handlePlan } from "../src/plan";
import { curveRouter, harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import plan200 from "../../../Tests/Fixtures/t0251/200-plan.json?raw";
import hazards200 from "../../../Tests/Fixtures/t0251/200-plan-hazards.json?raw";
import invalid400 from "../../../Tests/Fixtures/t0251/400-invalid-request.json?raw";
import unknownPlace404 from "../../../Tests/Fixtures/t0251/404-unknown-place.json?raw";
import notFound404 from "../../../Tests/Fixtures/t0251/404-not-found.json?raw";
import postOnly405 from "../../../Tests/Fixtures/t0251/405-post-only.json?raw";
import noScenic422 from "../../../Tests/Fixtures/t0251/422-no-scenic-alternative.json?raw";
import quota429 from "../../../Tests/Fixtures/t0251/429-quota-exhausted.json?raw";
import noRoute502 from "../../../Tests/Fixtures/t0251/502-no-route.json?raw";
import paused503 from "../../../Tests/Fixtures/t0251/503-planning-paused.json?raw";
import unavailable503 from "../../../Tests/Fixtures/t0251/503-planning-unavailable.json?raw";

const FAST_WAYS = [1, 2, 3, 4, 5];
const SCENIC_WAYS = [1, 10, 11, 12, 13, 14];
const HAZARD_DETAILS = {
  surface: [[0, 2, "asphalt"], [2, 3, "gravel"], [3, 4, "missing"], [4, 6, "COMPACTED"]],
  road_access: [[0, 1, "yes"], [1, 2, "destination"], [2, 6, "missing"]],
};
const url = (p: string) => `https://scenic-api.test${p}`;

async function recorded(response: Response) {
  return { status: response.status, text: await response.text() };
}

export const SCENARIOS: Record<string, () => Promise<{ status: number; text: string }>> = {
  "200-plan": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, harness(SANTA_MONICA_TOPANGA).deps)),
  "200-plan-hazards": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {},
      harness(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, SCENIC_WAYS, HAZARD_DETAILS)).deps)),
  "400-invalid-request": async () =>
    recorded(await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, origin: { lat: 34.021, lon: -118.49 } }), {},
      harness(SANTA_MONICA_TOPANGA).deps)),
  "404-unknown-place": async () =>
    recorded(await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, destination: { place: "la:nowhere" } }), {},
      harness(SANTA_MONICA_TOPANGA).deps)),
  "404-not-found": async () =>
    recorded(await SELF.fetch(url("/plans"), { method: "POST", body: JSON.stringify(SANTA_MONICA_TOPANGA_BODY) })),
  "405-post-only": async () =>
    recorded(await handlePlan(planRequest(null, "GET"), {}, harness(SANTA_MONICA_TOPANGA).deps)),
  "422-no-scenic-alternative": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {},
      harness(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, [1, 2, 3])).deps)),
  "429-quota-exhausted": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {},
      harness(SANTA_MONICA_TOPANGA, { plansUsedToday: 10 }).deps)),
  "502-no-route": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {},
      harness(curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000 + 1, FAST_WAYS, SCENIC_WAYS)).deps)),
  "503-planning-paused": async () =>
    recorded(await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), { KILL: "1" }, harness(SANTA_MONICA_TOPANGA).deps)),
  "503-planning-unavailable": async () =>
    recorded(await SELF.fetch(url("/plan"), { method: "POST", body: JSON.stringify(SANTA_MONICA_TOPANGA_BODY) })),
};

const FIXTURES: Record<string, string> = {
  "200-plan": plan200,
  "200-plan-hazards": hazards200,
  "400-invalid-request": invalid400,
  "404-unknown-place": unknownPlace404,
  "404-not-found": notFound404,
  "405-post-only": postOnly405,
  "422-no-scenic-alternative": noScenic422,
  "429-quota-exhausted": quota429,
  "502-no-route": noRoute502,
  "503-planning-paused": paused503,
  "503-planning-unavailable": unavailable503,
};

describe("POST /plan wire fixtures the Swift client decodes (T-0251 R7)", () => {
  it("every scenario has exactly one fixture and every fixture one scenario", () => {
    expect(Object.keys(FIXTURES).sort()).toEqual(Object.keys(SCENARIOS).sort());
  });

  for (const name of Object.keys(SCENARIOS)) {
    it(`${name}: the Worker answers the fixture's status and exactly its bytes`, async () => {
      const { status, text } = await SCENARIOS[name]!();
      expect(status).toBe(Number(name.slice(0, 3)));
      expect(text).toBe(FIXTURES[name]);
    });
  }
});
