/**
 * T-0267 acceptance 2-3: what each notification type does to the entitlement row (R5), replay and out-of-order
 * safety (R6), environment and bundle (R7), and GET /entitlement through the shipped ROUTES (R8). Every check
 * compares the WHOLE entitlements table by equality.
 */
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { appleChain, notification, type Chain, type NotificationSpec } from "./appleChain";
import { NOW, TOKEN, freshTable, getEntitlement, postAsn, row, rows, testDeps } from "./asnHarness";
import type { Env } from "../src/index";

const TX = { originalTransactionId: "1000", productId: "scenic.pro.monthly", appAccountToken: TOKEN };
const EXPIRES = NOW + 30 * 24 * 3600 * 1000;
const GRACE_UNTIL = NOW + 16 * 24 * 3600 * 1000;
const OK = { status: 200, json: { received: true } };
let chain: Chain;

beforeAll(async () => {
  chain = await appleChain({ now: NOW });
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
});

afterEach(() => vi.useRealTimers());

async function send(spec: Partial<NotificationSpec> & { type: string }, extra: Partial<Env> = {}) {
  return postAsn(await notification(chain, { signedDate: NOW, tx: TX, ...spec }), testDeps(chain.rootSha256, extra));
}

async function seedActive() {
  expect(await send({ type: "SUBSCRIBED", signedDate: NOW - 60_000 })).toEqual(OK);
  expect(await rows()).toEqual([row({})]);
}

describe("activating types set the row active until the transaction's expiresDate", () => {
  it.each(["SUBSCRIBED", "DID_RENEW", "OFFER_REDEEMED"])("%s -> active", async (type) => {
    expect(await send({ type, subtype: "INITIAL_BUY", tx: { ...TX, expiresDate: EXPIRES } })).toEqual(OK);
    expect(await rows()).toEqual([row({ notification_type: type, subtype: "INITIAL_BUY", active_until: EXPIRES, signed_date: NOW })]);
  });

  it("SUBSCRIBED for a transaction without expiresDate is active with no end", async () => {
    expect(await send({ type: "SUBSCRIBED" })).toEqual(OK);
    expect(await rows()).toEqual([row({ signed_date: NOW })]);
  });

  it("a transaction without appAccountToken is stored keyed on originalTransactionId alone", async () => {
    expect(await send({ type: "SUBSCRIBED", tx: { originalTransactionId: "2000", productId: "p" } })).toEqual(OK);
    expect(await rows()).toEqual([row({ original_transaction_id: "2000", app_account_token: null, product_id: "p", signed_date: NOW })]);
  });

  it("an upper-case appAccountToken is stored lowercased", async () => {
    expect(await send({ type: "SUBSCRIBED", tx: { ...TX, appAccountToken: TOKEN.toUpperCase() } })).toEqual(OK);
    expect(await rows()).toEqual([row({ signed_date: NOW })]);
  });
});

describe("deactivating types set the row inactive", () => {
  it.each(["EXPIRED", "REFUND", "REVOKE", "GRACE_PERIOD_EXPIRED"])("%s -> inactive", async (type) => {
    await seedActive();
    expect(await send({ type, tx: { ...TX, expiresDate: EXPIRES } })).toEqual(OK);
    expect(await rows()).toEqual([row({ status: "inactive", notification_type: type, signed_date: NOW })]);
  });
});

describe("DID_FAIL_TO_RENEW", () => {
  it("DID_FAIL_TO_RENEW with subtype GRACE_PERIOD -> active until gracePeriodExpiresDate", async () => {
    await seedActive();
    expect(await send({ type: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD", tx: { ...TX, expiresDate: NOW - 1000 },
      renewal: { gracePeriodExpiresDate: GRACE_UNTIL } })).toEqual(OK);
    expect(await rows()).toEqual([row({ notification_type: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD", active_until: GRACE_UNTIL, signed_date: NOW })]);
  });

  it("DID_FAIL_TO_RENEW without a subtype changes nothing", async () => {
    await seedActive();
    expect(await send({ type: "DID_FAIL_TO_RENEW", renewal: { gracePeriodExpiresDate: GRACE_UNTIL } })).toEqual(OK);
    expect(await rows()).toEqual([row({})]);
  });
});

const OTHERS = ["TEST", "DID_CHANGE_RENEWAL_PREF", "DID_CHANGE_RENEWAL_STATUS", "PRICE_INCREASE", "REFUND_DECLINED",
  "REFUND_REVERSED", "RENEWAL_EXTENDED", "RENEWAL_EXTENSION", "CONSUMPTION_REQUEST", "ONE_TIME_CHARGE", "METADATA_UPDATE",
  "MIGRATION", "PRICE_CHANGE", "RESCIND_CONSENT", "EXTERNAL_PURCHASE_TOKEN"];

describe("every other type is acknowledged 200 with no change", () => {
  it.each(OTHERS)("%s -> 200, no change", async (type) => {
    await seedActive();
    expect(await send({ type })).toEqual(OK);
    expect(await rows()).toEqual([row({})]);
  });
});

describe("replay and out-of-order delivery never regress state (R6)", () => {
  it("an older SUBSCRIBED after a newer EXPIRED leaves the row inactive", async () => {
    expect(await send({ type: "EXPIRED", signedDate: NOW })).toEqual(OK);
    expect(await send({ type: "SUBSCRIBED", signedDate: NOW - 1 })).toEqual(OK);
    expect(await rows()).toEqual([row({ status: "inactive", notification_type: "EXPIRED", signed_date: NOW })]);
  });

  it("a notification with the stored signedDate (a replay) changes nothing", async () => {
    await seedActive();
    expect(await send({ type: "REFUND", signedDate: NOW - 60_000 })).toEqual(OK);
    expect(await rows()).toEqual([row({})]);
  });

  it("one millisecond newer than the stored signedDate lands", async () => {
    await seedActive();
    expect(await send({ type: "REFUND", signedDate: NOW - 60_000 + 1 })).toEqual(OK);
    expect(await rows()).toEqual([row({ status: "inactive", notification_type: "REFUND", signed_date: NOW - 60_000 + 1 })]);
  });

  it("two transactions keep two rows", async () => {
    await seedActive();
    expect(await send({ type: "REFUND", tx: { ...TX, originalTransactionId: "2000" } })).toEqual(OK);
    expect(await rows()).toEqual([row({}), row({ original_transaction_id: "2000", status: "inactive", notification_type: "REFUND", signed_date: NOW })]);
  });
});

describe("environment and bundle (R7)", () => {
  it("a Sandbox notification changes nothing when ASN_ALLOW_SANDBOX is unset", async () => {
    await seedActive();
    expect(await send({ type: "EXPIRED", environment: "Sandbox" })).toEqual(OK);
    expect(await rows()).toEqual([row({})]);
  });

  it("a Sandbox notification changes nothing when ASN_ALLOW_SANDBOX is not exactly 1", async () => {
    await seedActive();
    expect(await send({ type: "EXPIRED", environment: "Sandbox" }, { ASN_ALLOW_SANDBOX: "true" })).toEqual(OK);
    expect(await rows()).toEqual([row({})]);
  });

  it("a Sandbox notification is applied and recorded as Sandbox when ASN_ALLOW_SANDBOX=1", async () => {
    expect(await send({ type: "SUBSCRIBED", environment: "Sandbox" }, { ASN_ALLOW_SANDBOX: "1" })).toEqual(OK);
    expect(await rows()).toEqual([row({ environment: "Sandbox", signed_date: NOW })]);
  });

  it("another app's bundleId changes nothing", async () => {
    expect(await send({ type: "SUBSCRIBED", bundleId: "com.example.other" })).toEqual(OK);
    expect(await rows()).toEqual([]);
  });

  it("a D1 that cannot answer is 503 entitlement_unavailable", async () => {
    const broken = { prepare: () => { throw new Error("no such table"); } } as unknown as D1Database;
    const deps = { ...testDeps(chain.rootSha256), db: broken };
    expect(await postAsn(await notification(chain, { type: "SUBSCRIBED", signedDate: NOW, tx: TX }), deps))
      .toEqual({ status: 503, json: { error: "entitlement_unavailable" } });
  });
});

describe("GET /entitlement through the shipped ROUTES (R8)", () => {
  it("no row for the token is none", async () => {
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "none", active_until: null } });
  });

  it("an active row with no end is active", async () => {
    await seedActive();
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "active", active_until: null } });
  });

  it("the header is read case-insensitively", async () => {
    await seedActive();
    expect(await getEntitlement(TOKEN.toUpperCase())).toEqual({ status: 200, json: { status: "active", active_until: null } });
  });

  it("active one millisecond before active_until, inactive at it", async () => {
    expect(await send({ type: "SUBSCRIBED", tx: { ...TX, expiresDate: NOW + 1 } })).toEqual(OK);
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "active", active_until: NOW + 1 } });
    vi.setSystemTime(NOW + 1);
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "inactive", active_until: null } });
  });

  it("after REFUND the token is inactive", async () => {
    await seedActive();
    expect(await send({ type: "REFUND" })).toEqual(OK);
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "inactive", active_until: null } });
  });

  it("of two active rows the later end is answered; an open-ended one wins", async () => {
    expect(await send({ type: "SUBSCRIBED", tx: { ...TX, expiresDate: NOW + 10 } })).toEqual(OK);
    expect(await send({ type: "SUBSCRIBED", tx: { ...TX, originalTransactionId: "2000", expiresDate: NOW + 20 } })).toEqual(OK);
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "active", active_until: NOW + 20 } });
    expect(await send({ type: "SUBSCRIBED", tx: { ...TX, originalTransactionId: "3000" } })).toEqual(OK);
    expect(await getEntitlement(TOKEN)).toEqual({ status: 200, json: { status: "active", active_until: null } });
  });

  it("another token's row is not answered", async () => {
    await seedActive();
    expect(await getEntitlement("00000000-0000-4000-8000-000000000000")).toEqual({ status: 200, json: { status: "none", active_until: null } });
  });

  it.each([["missing", null], ["empty", ""], ["not a UUID", "abc"], ["a UUID with a trailing character", `${TOKEN}0`]])(
    "a %s header is 400 invalid_request", async (_name, token) => {
      expect(await getEntitlement(token)).toEqual({ status: 400, json: { error: "invalid_request" } });
    });
});
