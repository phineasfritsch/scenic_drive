/**
 * T-0267 acceptance 1: every signedPayload defect is 400 invalid_notification with ZERO state change. Each case is
 * an EXPIRED for a seeded active row with a newer signedDate - accepting it would flip the row - posted through
 * the shipped handleAsn with production deps whose only replacement is the root fingerprint (R2). The self-made
 * root goes through ROUTES["/asn"] itself, where the pinned Apple root refuses it.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { APPLE_ROOT_CA_G3_SHA256 } from "../src/appleJws";
import { asnDepsFromEnv, handleAsn } from "../src/asn";
import type { Env } from "../src/index";
import { appleChain, b64, b64url, notification, party, signJws, type Chain, type Party } from "./appleChain";
import { NOW, TOKEN, answer, freshTable, postAsn, routeAsn, row, rows, testDeps } from "./asnHarness";

const TX = { originalTransactionId: "1000", productId: "scenic.pro.monthly", appAccountToken: TOKEN };
const INVALID = { status: 400, json: { error: "invalid_notification" } };
const SEEDED = [row({})];

let good: Chain;
let stranger: Chain;
let otherKey: Party;
const chains: Record<string, Chain> = {};

const expired = (over: Partial<Parameters<typeof notification>[1]> = {}, chain = good) =>
  notification(chain, { type: "EXPIRED", signedDate: NOW, tx: TX, ...over });
const parts = async () => (await expired()).split(".");
/** The whole EXPIRED notification (data and nested transaction included) re-signed under an altered header, so a
 * header defect is the ONLY thing wrong with it. */
const withHeader = async (header: Record<string, unknown>, key?: CryptoKey) => {
  const p = (await parts())[1]!;
  const payload = JSON.parse(new TextDecoder().decode(flip(p, false)));
  return signJws(payload, good, header, key);
};
const flip = (s: string, change = true) => {
  const raw = Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
  if (change) raw[10] ^= 0x01;
  return raw;
};

beforeAll(async () => {
  good = await appleChain({ now: NOW });
  stranger = await appleChain({ now: NOW });
  otherKey = await party("Not The Leaf", "P-256");
  const signer = await party("Test WWDR - G6", "P-384");
  const specs: Record<string, Parameters<typeof appleChain>[0]> = {
    "expired leaf": { now: NOW, leaf: { notAfter: NOW - 1000 } },
    "leaf not yet valid": { now: NOW, leaf: { notBefore: NOW + 1000 } },
    "expired intermediate": { now: NOW, intermediate: { notAfter: NOW - 1000 } },
    "intermediate not yet valid": { now: NOW, intermediate: { notBefore: NOW + 1000 } },
    "expired root": { now: NOW, root: { notAfter: NOW - 1000 } },
    "root not yet valid": { now: NOW, root: { notBefore: NOW + 1000 } },
    "leaf without the App Store OID": { now: NOW, leaf: { extensions: [] } },
    "intermediate without the WWDR OID": { now: NOW, intermediate: { extensions: [] } },
    "leaf signed by a key that is not the intermediate's": { now: NOW, leafSigner: signer },
    "leaf naming another issuer": { now: NOW, leaf: { issuerName: "Someone Else" } },
    "leaf key on P-384": { now: NOW, leafCurve: "P-384" },
    "intermediate signed by a key that is not the root's": { now: NOW, intermediateSigner: await party("Test Root CA - G3", "P-384") },
    "root valid until 2051 (GeneralizedTime)": { now: NOW, root: { notAfter: Date.UTC(2051, 0, 1) } },
    "leaf valid until exactly now": { now: NOW, leaf: { notAfter: NOW } },
    "leaf valid from exactly now": { now: NOW, leaf: { notBefore: NOW } },
  };
  for (const [name, spec] of Object.entries(specs)) chains[name] = await appleChain(spec);
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
  const seed = await notification(good, { type: "SUBSCRIBED", signedDate: NOW - 60_000, tx: TX });
  expect(await postAsn(seed, testDeps(good.rootSha256))).toEqual({ status: 200, json: { received: true } });
  expect(await rows()).toEqual(SEEDED);
});

afterEach(() => vi.useRealTimers());

/** [name, the defective signedPayload, the chain whose OWN root is trusted (default: good)] - a defect chain is
 * trusted at its own root, so the row fails on its defect and not on the root. */
const DEFECTS: [string, () => Promise<unknown>, string?][] = [
  ["bad signature", async () => { const [h, p, s] = await parts(); return `${h}.${p}.${b64url(flip(s!))}`; }],
  ["a signature by a key that is not the leaf's", () => withHeader({}, otherKey.keys.privateKey)],
  ["a chain to a self-made root that is not the trusted one", () => expired({}, stranger)],
  ["expired leaf", () => expired({}, chains["expired leaf"]), "expired leaf"],
  ["leaf not yet valid", () => expired({}, chains["leaf not yet valid"]), "leaf not yet valid"],
  ["expired intermediate", () => expired({}, chains["expired intermediate"]), "expired intermediate"],
  ["intermediate not yet valid", () => expired({}, chains["intermediate not yet valid"]), "intermediate not yet valid"],
  ["expired root", () => expired({}, chains["expired root"]), "expired root"],
  ["root not yet valid", () => expired({}, chains["root not yet valid"]), "root not yet valid"],
  ["leaf without the App Store OID", () => expired({}, chains["leaf without the App Store OID"]), "leaf without the App Store OID"],
  ["intermediate without the WWDR OID", () => expired({}, chains["intermediate without the WWDR OID"]), "intermediate without the WWDR OID"],
  ["leaf signed by a key that is not the intermediate's", () => expired({}, chains["leaf signed by a key that is not the intermediate's"]), "leaf signed by a key that is not the intermediate's"],
  ["intermediate signed by a key that is not the root's", () => expired({}, chains["intermediate signed by a key that is not the root's"]), "intermediate signed by a key that is not the root's"],
  ["leaf certificate with a trailing byte", () => expired({}, { ...good,
    x5c: [b64(new Uint8Array([...Uint8Array.from(atob(good.x5c[0]!), (c) => c.charCodeAt(0)), 0])), ...good.x5c.slice(1)] })],
  ["leaf naming another issuer", () => expired({}, chains["leaf naming another issuer"]), "leaf naming another issuer"],
  ["leaf key on P-384 (no 64-byte ES256 signature)", () => expired({}, chains["leaf key on P-384"]), "leaf key on P-384"],
  ["missing x5c", () => withHeader({ x5c: undefined })],
  ["x5c of two certificates", () => withHeader({ x5c: good.x5c.slice(0, 2) })],
  ["x5c of four certificates", () => withHeader({ x5c: [...good.x5c, good.x5c[2]] })],
  ["x5c entry that is not base64", () => withHeader({ x5c: ["%%%", ...good.x5c.slice(1)] })],
  ["x5c entry that is not a certificate", () => withHeader({ x5c: [b64(new Uint8Array([48, 1, 2])), ...good.x5c.slice(1)] })],
  ["alg none", () => withHeader({ alg: "none" })],
  ["alg none with an empty signature", async () => { const [h, p] = (await withHeader({ alg: "none" })).split("."); return `${h}.${p}.`; }],
  ["alg HS256", () => withHeader({ alg: "HS256" })],
  ["alg ES384", () => withHeader({ alg: "ES384" })],
  ["alg absent", () => withHeader({ alg: undefined })],
  ["truncated JWS: two parts", async () => (await parts()).slice(0, 2).join(".")],
  ["truncated JWS: one part", async () => (await parts())[0]],
  ["truncated JWS: signature cut to 63 bytes", async () => { const [h, p, s] = await parts(); return `${h}.${p}.${s!.slice(0, 84)}`; }],
  ["truncated JWS: payload cut in half", async () => { const [h, p, s] = await parts(); return `${h}.${p!.slice(0, p!.length >> 1)}.${s}`; }],
  ["empty string", async () => ""],
  ["signedPayload not a string", async () => 42],
  ["payload not JSON", () => signJws("not json", good)],
  ["payload a JSON array", () => signJws([1, 2], good)],
  ["no notificationType", () => signJws({ signedDate: NOW, data: {} }, good)],
  ["signedDate not a number", () => signJws({ notificationType: "EXPIRED", signedDate: "now", data: {} }, good)],
  ["no data", () => signJws({ notificationType: "EXPIRED", signedDate: NOW }, good)],
  ["environment neither Production nor Sandbox", () => expired({ environment: "Staging" })],
  ["signedTransactionInfo missing", () => expired({ tx: null })],
  ["signedTransactionInfo with a bad signature", async () => {
    const tx = (await signJws(TX, good)).split(".");
    return signJws({ notificationType: "EXPIRED", signedDate: NOW, data: { environment: "Production", bundleId: "com.phineasfritsch.scenicdrive",
      signedTransactionInfo: `${tx[0]}.${tx[1]}.${b64url(flip(tx[2]!))}` } }, good);
  }],
  ["signedTransactionInfo from a self-made root that is not the trusted one", async () =>
    signJws({ notificationType: "EXPIRED", signedDate: NOW, data: { environment: "Production", bundleId: "com.phineasfritsch.scenicdrive",
      signedTransactionInfo: await signJws(TX, stranger) } }, good)],
  ["transaction without originalTransactionId", () => expired({ tx: { productId: "scenic.pro.monthly" } })],
  ["transaction with an empty originalTransactionId", () => expired({ tx: { ...TX, originalTransactionId: "" } })],
  ["transaction without productId", () => expired({ tx: { originalTransactionId: "1000" } })],
  ["SUBSCRIBED with an expiresDate that is not epoch ms", () => expired({ type: "SUBSCRIBED", tx: { ...TX, expiresDate: "soon" } })],
  ["GRACE_PERIOD without signedRenewalInfo", () => expired({ type: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD" })],
  ["GRACE_PERIOD without gracePeriodExpiresDate", () => expired({ type: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD", renewal: { autoRenewStatus: 1 } })],
  ["GRACE_PERIOD with a negative gracePeriodExpiresDate", () => expired({ type: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD", renewal: { gracePeriodExpiresDate: -1 } })],
];

describe("every signedPayload defect is 400 with zero state change (shipped handleAsn)", () => {
  it.each(DEFECTS)("%s", async (_name, build, trusted) => {
    expect(await postAsn(await build(), testDeps((trusted ? chains[trusted]! : good).rootSha256))).toEqual(INVALID);
    expect(await rows()).toEqual(SEEDED);
  });

  it("a body that is not JSON is 400 with zero state change", async () => {
    const req = new Request("https://scenic-api.test/asn", { method: "POST", body: "{not json" });
    expect(await answer(await handleAsn(req, testDeps(good.rootSha256)))).toEqual(INVALID);
    expect(await rows()).toEqual(SEEDED);
  });

  it("a body without signedPayload is 400 with zero state change", async () => {
    const req = new Request("https://scenic-api.test/asn", { method: "POST", body: JSON.stringify({ payload: await expired() }) });
    expect(await answer(await handleAsn(req, testDeps(good.rootSha256)))).toEqual(INVALID);
    expect(await rows()).toEqual(SEEDED);
  });
});

describe("the validity bounds are inclusive at the Worker's clock", () => {
  it.each(["leaf valid until exactly now", "leaf valid from exactly now", "root valid until 2051 (GeneralizedTime)"])("%s is accepted and the row flips", async (name) => {
    expect(await postAsn(await expired({}, chains[name]), testDeps(chains[name]!.rootSha256))).toEqual({ status: 200, json: { received: true } });
    expect(await rows()).toEqual([row({ status: "inactive", notification_type: "EXPIRED", signed_date: NOW })]);
  });
});

describe("the shipped ROUTES['/asn'] pins Apple's root", () => {
  it("the production deps pin exactly the measured SHA-256 of AppleRootCA-G3.cer", () => {
    expect(asnDepsFromEnv(env as unknown as Env).rootSha256).toBe("63343abfb89a6a03ebb57e9b3f5fa7be7c4f5c756f3017b3a8c488c3653e9179");
    expect(APPLE_ROOT_CA_G3_SHA256).toBe("63343abfb89a6a03ebb57e9b3f5fa7be7c4f5c756f3017b3a8c488c3653e9179");
  });

  it("a chain valid in every respect but its self-made root is 400 through ROUTES with zero state change", async () => {
    expect(await routeAsn(JSON.stringify({ signedPayload: await expired() }))).toEqual(INVALID);
    expect(await rows()).toEqual(SEEDED);
  });

  it("ROUTES['/asn'] refuses GET with 405", async () => {
    const req = new Request("https://scenic-api.test/asn");
    const { ROUTES } = await import("../src/index");
    expect(await answer(await ROUTES["/asn"]!(req, env as unknown as Env, new URL(req.url)))).toEqual({ status: 405, json: { error: "POST only" } });
  });
});
