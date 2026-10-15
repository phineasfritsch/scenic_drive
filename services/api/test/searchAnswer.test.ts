/**
 * T-0359 R6: Photon's answer -> the WHOLE /search answer, through the SHIPPED ROUTES["/search"]. Expected labels are
 * written out here, never rebuilt by searchLabel; every malformed answer refuses the whole of it (502 search_failed).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../src/index";
import { fakeQuotaNamespace } from "./doFake";
import { feature, NOW, SEARCH_BODY, searchEnv, searchRequest } from "./searchHarness";

let upstream: () => Promise<Response>;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  vi.stubGlobal("fetch", () => upstream());
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function answerFor(photon: () => Promise<Response>) {
  upstream = photon;
  const req = searchRequest(SEARCH_BODY);
  const response = await ROUTES["/search"]!(req, searchEnv(fakeQuotaNamespace()), new URL(req.url));
  return { status: response.status, json: (await response.json()) as unknown };
}

const photonJson = (body: unknown, status = 200) => async () => new Response(JSON.stringify(body), { status });
const CA = { state: "California" };

const GOOD: [string, unknown[], { label: string; lat: number; lon: number }[]][] = [
  ["a house number and street", [feature({ housenumber: "23500", street: "Mulholland Highway", city: "Calabasas", ...CA }, [-118.66, 34.12])],
    [{ label: "23500 Mulholland Highway, Calabasas, California", lat: 34.12, lon: -118.66 }]],
  ["a named place with an address", [feature({ name: "Griffith Observatory", housenumber: "2800", street: "East Observatory Road",
    city: "Los Angeles", ...CA, osm_id: 1, extent: [1, 2, 3, 4] }, [-118.3004, 34.1184])],
    [{ label: "Griffith Observatory, 2800 East Observatory Road, Los Angeles, California", lat: 34.1184, lon: -118.3004 }]],
  ["a street with no number", [feature({ name: "Mulholland Drive", city: "Los Angeles", ...CA })],
    [{ label: "Mulholland Drive, Los Angeles, California", lat: 34.13, lon: -118.45 }]],
  ["a house number with no street", [feature({ name: "Cabin", housenumber: "5", ...CA })], [{ label: "Cabin, California", lat: 34.13, lon: -118.45 }]],
  ["a city named like itself", [feature({ name: "Los Angeles", city: "Los Angeles", ...CA })], [{ label: "Los Angeles, California", lat: 34.13, lon: -118.45 }]],
  ["blank and padded parts", [feature({ name: "  Topanga  ", street: " ", city: "", ...CA, county: 7 })], [{ label: "Topanga, California", lat: 34.13, lon: -118.45 }]],
  ["a non-string part", [feature({ name: 12, street: "Old Topanga Canyon Road", ...CA })], [{ label: "Old Topanga Canyon Road, California", lat: 34.13, lon: -118.45 }]],
  ["the coordinate bounds", [feature({ name: "N" }, [180, 90]), feature({ name: "S" }, [-180, -90])],
    [{ label: "N", lat: 90, lon: 180 }, { label: "S", lat: -90, lon: -180 }]],
  ["no features", [], []],
  ["ten features, eight answered", Array.from({ length: 10 }, (_, i) => feature({ name: `Place ${i}` }, [-118 - i / 100, 34])),
    Array.from({ length: 8 }, (_, i) => ({ label: `Place ${i}`, lat: 34, lon: -118 - i / 100 }))],
];

const ok = feature({ name: "Topanga", ...CA });
const BAD: [string, () => Promise<Response>][] = [
  ["not JSON", async () => new Response("<html>")],
  ["an empty object", photonJson({})],
  ["features an object", photonJson({ features: {} })],
  ["features null", photonJson({ features: null })],
  ["the body an array", photonJson([ok])],
  ["a LineString", photonJson({ features: [{ ...ok, geometry: { type: "LineString", coordinates: [[-118, 34], [-118.1, 34.1]] } }] })],
  ["one coordinate", photonJson({ features: [feature({ name: "x" }, [-118])] })],
  ["three coordinates", photonJson({ features: [feature({ name: "x" }, [-118, 34, 10])] })],
  ["lat 90.0001", photonJson({ features: [feature({ name: "x" }, [-118, 90.0001])] })],
  ["lat -90.0001", photonJson({ features: [feature({ name: "x" }, [-118, -90.0001])] })],
  ["lon 180.0001", photonJson({ features: [feature({ name: "x" }, [180.0001, 34])] })],
  ["lon -180.0001", photonJson({ features: [feature({ name: "x" }, [-180.0001, 34])] })],
  ["a string coordinate", photonJson({ features: [feature({ name: "x" }, ["-118", 34])] })],
  ["a null coordinate", photonJson({ features: [feature({ name: "x" }, [-118, null])] })],
  ["no geometry", photonJson({ features: [{ type: "Feature", properties: { name: "x" } }] })],
  ["no properties", photonJson({ features: [{ type: "Feature", geometry: ok.geometry }] })],
  ["properties an array", photonJson({ features: [{ ...ok, properties: ["x"] }] })],
  ["no usable label", photonJson({ features: [feature({ osm_id: 5, country: "United States" })] })],
  ["one good feature then a bad one", photonJson({ features: [ok, feature({ name: "x" }, [-118, 91])] })],
  ["a feature null", photonJson({ features: [ok, null] })],
  ["Photon 500", photonJson({ features: [ok] }, 500)],
  ["Photon 400", photonJson({ message: "bad" }, 400)],
  ["Photon 204", async () => new Response(null, { status: 204 })],
  ["Photon 201", photonJson({ features: [ok] }, 201)],
  ["fetch throws", async () => { throw new TypeError("network down"); }],
];

describe("the /search answer is Photon's, read fail-closed (T-0359 R6)", () => {
  it("every readable Photon answer is the whole {results} written out here", async () => {
    const answered: unknown[] = [];
    for (const [name, features] of GOOD) answered.push([name, await answerFor(photonJson({ type: "FeatureCollection", features }))]);
    expect(answered).toEqual(GOOD.map(([name, , results]) => [name, { status: 200, json: { results } }]));
  });

  it("every unreadable, non-200 or failed Photon answer is 502 search_failed, whole", async () => {
    const answered: unknown[] = [];
    for (const [name, photon] of BAD) answered.push([name, await answerFor(photon)]);
    expect(answered).toEqual(BAD.map(([name]) => [name, { status: 502, json: { error: "search_failed" } }]));
  });
});
