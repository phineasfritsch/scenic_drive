/**
 * T-0359 R3/R4 (P-PRIV-05): POST /search takes the typed text and at most ONE bias coordinate at 2 dp, and the one
 * Photon request carries exactly that - by full string equality to a URL written out here, not built by the module.
 * Every case drives the SHIPPED ROUTES["/search"] over the QuotaCounter fake with fetch recorded.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../src/index";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { feature, NOW, SEARCH_SECRET, SEARCH_URL, searchEnv, searchRequest } from "./searchHarness";

let quota: FakeQuota;
let sent: { url: string; method: string | undefined; headers: [string, string][]; body: unknown }[];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  sent = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    sent.push({ url: String(input), method: init?.method, headers: [...new Headers(init?.headers).entries()], body: init?.body });
    return new Response(JSON.stringify({ features: [feature({ name: "Topanga", state: "California" })] }));
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function send(body: unknown) {
  const req = searchRequest(body);
  const response = await ROUTES["/search"]!(req, searchEnv(quota), new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

/** The ruled template (R4), written out: q, limit 8, lang en, the California bbox, then lat/lon at 2 dp. */
const BBOX = "-124.48%2C32.53%2C-114.13%2C42.01";
const expectedUrl = (q: string, near?: [string, string]) =>
  `${SEARCH_URL}/api?q=${q}&limit=8&lang=en&bbox=${BBOX}` + (near ? `&lat=${near[0]}&lon=${near[1]}` : "");

const LONG = "a".repeat(100);
// [body, the q as URLSearchParams encodes it, the bias as sent upstream or none]
const ACCEPTED: [unknown, string, [string, string] | undefined][] = [
  [{ q: "a" }, "a", undefined],
  [{ q: LONG }, LONG, undefined],
  [{ q: "  Topanga Canyon  " }, "++Topanga+Canyon++", undefined],
  [{ q: "Café & 2nd #4 ?x=1~" }, "Caf%C3%A9+%26+2nd+%234+%3Fx%3D1%7E", undefined],
  [{ q: "Mulholland Drive", near: { lat: 34.13, lon: -118.45 } }, "Mulholland+Drive", ["34.13", "-118.45"]],
  [{ q: "x", near: { lat: 90, lon: 180 } }, "x", ["90.00", "180.00"]],
  [{ q: "x", near: { lat: -90, lon: -180 } }, "x", ["-90.00", "-180.00"]],
  [{ q: "x", near: { lat: 34.1, lon: -118 } }, "x", ["34.10", "-118.00"]],
  [{ q: "x", near: { lat: 0.01, lon: -0.01 } }, "x", ["0.01", "-0.01"]],
  [{ near: { lon: 1.5, lat: -2.25 }, q: "x" }, "x", ["-2.25", "1.50"]],
];

const REFUSED: [string, unknown][] = [
  ["q empty", { q: "" }],
  ["q whitespace only", { q: "   " }],
  ["q 101 units", { q: "a".repeat(101) }],
  ["q 100 units plus one astral char", { q: "a".repeat(99) + "\u{1F697}" }],
  ["q with U+001F", { q: "a\u001fb" }],
  ["q with U+0000", { q: "a\u0000b" }],
  ["q with a tab", { q: "a\tb" }],
  ["q with a newline", { q: "a\nb" }],
  ["q with U+007F", { q: "a\u007fb" }],
  ["q a number", { q: 5 }],
  ["q null", { q: null }],
  ["q missing", { near: { lat: 34.13, lon: -118.45 } }],
  ["lat 3 dp", { q: "x", near: { lat: 34.131, lon: -118.45 } }],
  ["lon 3 dp", { q: "x", near: { lat: 34.13, lon: -118.451 } }],
  ["lat 90.01", { q: "x", near: { lat: 90.01, lon: 0 } }],
  ["lat -90.01", { q: "x", near: { lat: -90.01, lon: 0 } }],
  ["lon 180.01", { q: "x", near: { lat: 0, lon: 180.01 } }],
  ["lon -180.01", { q: "x", near: { lat: 0, lon: -180.01 } }],
  ["lat a string", { q: "x", near: { lat: "34.13", lon: -118.45 } }],
  ["lon null", { q: "x", near: { lat: 34.13, lon: null } }],
  ["near one key", { q: "x", near: { lat: 34.13 } }],
  ["near empty", { q: "x", near: {} }],
  ["near null", { q: "x", near: null }],
  ["near an array", { q: "x", near: [34.13, -118.45] }],
  ["a third key inside near", { q: "x", near: { lat: 34.13, lon: -118.45, alt: 1 } }],
  ["a second coordinate at the top", { q: "x", near: { lat: 34.13, lon: -118.45 }, origin: { lat: 34.1, lon: -118.4 } }],
  ["a device id at the top", { q: "x", device: "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab" }],
  ["the body an array", [{ q: "x" }]],
  ["the body null", null],
  ["the body a string", "q=x"],
];

describe("POST /search takes the typed text and one 2-dp coordinate, and sends exactly that (T-0359 R3/R4, P-PRIV-05)", () => {
  it("every refused bound is 400 invalid_request with zero Photon requests and no reservation", async () => {
    const answered: [string, number, unknown][] = [];
    for (const [name, body] of REFUSED) {
      const answer = await send(body);
      answered.push([name, answer.status, answer.json.error]);
    }
    expect([answered, sent, quota.state()]).toEqual([REFUSED.map(([name]) => [name, 400, "invalid_request"]), [], {}]);
  });

  it("a body that is not JSON is 400 with zero Photon requests", async () => {
    const answer = await send("{\"q\": ");
    expect([answer.status, answer.json, sent]).toEqual([400, { error: "invalid_request", detail: "the body is not JSON" }, []]);
  });

  it("every accepted body sends ONE GET whose URL equals the written-out template and whose only header is the search secret", async () => {
    for (const [body] of ACCEPTED) expect((await send(body)).status).toBe(200);
    expect(sent).toEqual(ACCEPTED.map(([, q, near]) => ({
      url: expectedUrl(q, near), method: "GET", headers: [["x-scenic-search-secret", SEARCH_SECRET]], body: undefined,
    })));
  });
});
