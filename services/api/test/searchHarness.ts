/**
 * T-0359: the /search fixtures every search test and the route-enumerating tables share. Not a test file.
 */
import { fakeKv, type FakeQuota } from "./doFake";
import type { Env } from "../src/index";

/** A typed street with one 2-dp bias coordinate - the accepted body the enumerating tables send. */
export const SEARCH_BODY = { q: "Mulholland Drive", near: { lat: 34.13, lon: -118.45 } };
export const SEARCH_URL = "https://search.test";
export const SEARCH_SECRET = "test-search-secret";
export const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
export const NOW = new Date("2026-10-10T12:00:00Z");

/** The env the shipped ROUTES['/search'] builds its deps from: QUOTA, SEARCH_URL, SEARCH_SECRET; `extra` overrides. */
export function searchEnv(quota: FakeQuota, extra: Record<string, unknown> = {}): Env {
  return {
    GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, SEARCH_URL, SEARCH_SECRET, CLOSURES: fakeKv({}), ...extra,
  } as unknown as Env;
}

export function searchRequest(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request("https://scenic-api.test/search", {
    method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE, ...headers },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}

/** One Photon feature as docs/api-v1.md@1.3.0 shows them. */
export function feature(properties: Record<string, unknown>, coordinates: unknown[] = [-118.45, 34.13]) {
  return { type: "Feature", geometry: { type: "Point", coordinates }, properties };
}
