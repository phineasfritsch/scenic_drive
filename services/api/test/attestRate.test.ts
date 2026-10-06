/**
 * T-0280 R5-R6: POST /attest/challenge through the shipped ROUTES is limited to ATTEST_CHALLENGES_PER_DEVICE_HOUR per
 * device per UTC clock hour and ATTEST_CHALLENGES_PER_DAY in all per UTC day, reserved in the batch before any other
 * write; over either limit it is 429 challenge_rate_limited with all four tables unchanged. Each limit is met at the
 * limit and refused at limit + 1; slots roll over at the hour and the day; KILL changes nothing on this D1-only route.
 * Answers and tables are compared WHOLE.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ATTEST_CHALLENGES_PER_DAY, ATTEST_CHALLENGES_PER_DEVICE_HOUR } from "../src/attestStore";
import { DEVICE, NOW } from "./attestHarness";
import { allTables, DAY, DAY_SLOT, freshAssertTables, HOUR, HOUR_SLOT, post, route, seedRate } from "./assertHarness";

const OTHER_DEVICE = "7a6b5c4d-3e2f-4a1b-9c8d-0123456789ab";
const LIMITED = { status: 429, json: { error: "challenge_rate_limited" } };

const ask = (device?: string, e = {}) => route("/attest/challenge", e, post({}, device === undefined ? {} : { "x-scenic-device": device }));
const issuedRow = (a: { json: Record<string, unknown> }, at = NOW) => ({ challenge: a.json.challenge, expires_at: at + 300_000 });
const byChallenge = (rows: { challenge: unknown }[]) => rows.sort((a, b) => String(a.challenge).localeCompare(String(b.challenge)));

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAssertTables();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("the per-device hourly limit through ROUTES['/attest/challenge'] (R5)", () => {
  it("the ruled literals: 10 per device per hour, 10000 per day", () => {
    expect([ATTEST_CHALLENGES_PER_DEVICE_HOUR, ATTEST_CHALLENGES_PER_DAY]).toEqual([10, 10_000]);
  });

  it("a device's 10th challenge in its hour is issued (the limit); its 11th is 429 and writes nothing (limit + 1)", async () => {
    const answers = [];
    for (let i = 0; i < 10; i++) answers.push(await ask(DEVICE));
    expect({ statuses: answers.map((a) => a.status), tables: await allTables() }).toEqual({
      statuses: Array(10).fill(200),
      tables: { challenges: byChallenge(answers.map((a) => issuedRow(a))), keys: [], counts: [],
        rates: [{ bucket: `device:${DEVICE}`, slot: HOUR_SLOT, issued: 10 }, { bucket: "global", slot: DAY_SLOT, issued: 10 }] },
    });
    const before = await allTables();
    expect({ answer: await ask(DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
  });

  it("an upper-case device header counts in the lower-case device's bucket", async () => {
    await seedRate(`device:${DEVICE}`, HOUR_SLOT, 10);
    const before = await allTables();
    expect({ answer: await ask(DEVICE.toUpperCase()), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
  });

  it("another device is not limited by a full device bucket", async () => {
    await seedRate(`device:${DEVICE}`, HOUR_SLOT, 10);
    const a = await ask(OTHER_DEVICE);
    expect({ status: a.status, tables: await allTables() }).toEqual({ status: 200, tables: { challenges: [issuedRow(a)], keys: [], counts: [],
      rates: [{ bucket: `device:${DEVICE}`, slot: HOUR_SLOT, issued: 10 }, { bucket: `device:${OTHER_DEVICE}`, slot: HOUR_SLOT, issued: 1 }, { bucket: "global", slot: DAY_SLOT, issued: 1 }] } });
  });

  it("no header and a malformed header share the one unidentified bucket: full, both 429 with nothing written", async () => {
    await seedRate("device:unidentified", HOUR_SLOT, 10);
    const before = await allTables();
    expect({ answers: [await ask(), await ask("not-a-uuid"), await ask(`${DEVICE}0`)], tables: await allTables() })
      .toEqual({ answers: [LIMITED, LIMITED, LIMITED], tables: before });
  });

  it("the last ms of the hour still counts in it (429); the next hour's first ms issues and prunes the old slot", async () => {
    await seedRate(`device:${DEVICE}`, HOUR_SLOT, 10);
    vi.setSystemTime(NOW + HOUR - 1);
    const before = await allTables();
    expect({ answer: await ask(DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
    vi.setSystemTime(NOW + HOUR);
    const a = await ask(DEVICE);
    expect({ status: a.status, tables: await allTables() }).toEqual({ status: 200, tables: { challenges: [issuedRow(a, NOW + HOUR)], keys: [], counts: [],
      rates: [{ bucket: `device:${DEVICE}`, slot: HOUR_SLOT + HOUR, issued: 1 }, { bucket: "global", slot: DAY_SLOT, issued: 1 }] } });
  });
});

describe("the global daily ceiling through ROUTES['/attest/challenge'] (R5)", () => {
  it("the day's 10000th challenge is issued (the limit); the 10001st is 429 and writes nothing (limit + 1)", async () => {
    await seedRate("global", DAY_SLOT, 9_999);
    const a = await ask(DEVICE);
    expect({ status: a.status, tables: await allTables() }).toEqual({ status: 200, tables: { challenges: [issuedRow(a)], keys: [], counts: [],
      rates: [{ bucket: `device:${DEVICE}`, slot: HOUR_SLOT, issued: 1 }, { bucket: "global", slot: DAY_SLOT, issued: 10_000 }] } });
    const before = await allTables();
    expect({ answer: await ask(OTHER_DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
  });

  it("the last ms of the UTC day still counts in it (429); the next day's first ms issues and prunes the old day", async () => {
    await seedRate("global", DAY_SLOT, 10_000);
    vi.setSystemTime(DAY_SLOT + DAY - 1);
    const before = await allTables();
    expect({ answer: await ask(DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
    vi.setSystemTime(DAY_SLOT + DAY);
    const a = await ask(DEVICE);
    expect({ status: a.status, tables: await allTables() }).toEqual({ status: 200, tables: { challenges: [issuedRow(a, DAY_SLOT + DAY)], keys: [], counts: [],
      rates: [{ bucket: `device:${DEVICE}`, slot: DAY_SLOT + DAY, issued: 1 }, { bucket: "global", slot: DAY_SLOT + DAY, issued: 1 }] } });
  });

  it("a full global ceiling refuses a device with room: 429, nothing written", async () => {
    await seedRate("global", DAY_SLOT, 10_000);
    const before = await allTables();
    expect({ answer: await ask(DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
  });

  it("a refused challenge prunes nothing: old slots stay until an issue", async () => {
    await seedRate("global", DAY_SLOT, 10_000);
    await seedRate(`device:${DEVICE}`, HOUR_SLOT - HOUR, 3);
    await seedRate("global", DAY_SLOT - DAY, 5);
    const before = await allTables();
    expect({ answer: await ask(OTHER_DEVICE), tables: await allTables() }).toEqual({ answer: LIMITED, tables: before });
  });

  it("an issue prunes older device slots and older days but keeps this hour's and this day's rows", async () => {
    await seedRate(`device:${OTHER_DEVICE}`, HOUR_SLOT - HOUR, 3);
    await seedRate(`device:${OTHER_DEVICE}`, HOUR_SLOT, 2);
    await seedRate("global", DAY_SLOT - DAY, 5);
    await seedRate("global", DAY_SLOT, 7);
    const a = await ask(DEVICE);
    expect({ status: a.status, tables: await allTables() }).toEqual({ status: 200, tables: { challenges: [issuedRow(a)], keys: [], counts: [],
      rates: [{ bucket: `device:${DEVICE}`, slot: HOUR_SLOT, issued: 1 }, { bucket: `device:${OTHER_DEVICE}`, slot: HOUR_SLOT, issued: 2 }, { bucket: "global", slot: DAY_SLOT, issued: 8 }] } });
  });

  it("KILL=1 changes nothing on this D1-only route; without the secret it is 503 with nothing written", async () => {
    const killed = await ask(DEVICE, { KILL: "1" });
    expect(killed.status).toBe(200);
    const before = await allTables();
    expect({ answer: await ask(DEVICE, { SESSION_JWT_SECRET: undefined }), tables: await allTables() })
      .toEqual({ answer: { status: 503, json: { error: "attest_unavailable" } }, tables: before });
  });
});
