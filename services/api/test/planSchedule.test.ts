/**
 * T-0403: /plan's router requests run two at a time (car_fast || lambda 4, then lambda 0 || the second midpoint)
 * and every answer is byte-equal to the one-at-a-time schedule's.
 *
 * Acceptance 1: each row's WHOLE answer - status, sha256 and length of the exact response text - equals GOLDEN,
 * captured from main 0399dcea's src (the sequential schedule) before any src change; the capture is quoted in the
 * task Log. Acceptance 2: the same rows over a router whose every request takes T ms on a virtual clock answer
 * inside the stated number of rounds, never with more than 2 requests in flight.
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { curveRouter, harness, planRequest, recorded, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY,
  type Recording } from "./planHarness";
import { timedRouter } from "./timedRouter";
import wwFastest from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/fastest.json?raw";
import ww0 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-0.json?raw";
import ww4 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-4.json?raw";
import ww6 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-6.json?raw";
import ww7 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.json?raw";
import ww75 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.5.json?raw";
import ww775 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.75.json?raw";
import wmFastest from "../../../Tests/Fixtures/t0221/westwood-malibu/fastest.json?raw";
import wm0 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-0.json?raw";
import wm2 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-2.json?raw";
import wm3 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.json?raw";
import wm325 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.25.json?raw";
import wm35 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.5.json?raw";
import wm4 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-4.json?raw";

const WESTWOOD_WOODLAND_HILLS = recorded(wwFastest, new Map([[0, ww0], [4, ww4], [6, ww6], [7, ww7], [7.5, ww75], [7.75, ww775]]));
/** As planHonest/planBackRoads: no lambda-8 recording exists, so lambda 8 answers the recorded lambda-4 body. */
const WESTWOOD_MALIBU = recorded(wmFastest, new Map([[0, wm0], [2, wm2], [3, wm3], [3.25, wm325], [3.5, wm35], [4, wm4], [8, wm4]]));
const FAST_WAYS = [1, 2, 3, 4, 5];
const SCENIC_WAYS = [1, 10, 11, 12, 13, 14];
const refusing = (r: Recording, which: "fastest" | "scenic"): Recording => which === "fastest"
  ? { fastest: JSON.stringify({ message: "refused" }), scenic: r.scenic } : { fastest: r.fastest, scenic: () => undefined };

/** planCeiling's seeded generator, so a failing curve is reproducible from its index. */
function lcg(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

interface Row {
  name: string;
  router: Recording;
  body: Record<string, unknown>;
  /** Acceptance 2: the most router rounds (T each) the answer may take; absent = not a timed row. */
  rounds?: number;
}

const plan = (minutes: number, extra: Record<string, unknown> = {}) => ({ ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: minutes, ...extra });

const ROWS: Row[] = [
  { name: "santa-monica-topanga +25", router: SANTA_MONICA_TOPANGA, body: plan(25), rounds: 4 },
  { name: "westwood-woodland-hills +25", router: WESTWOOD_WOODLAND_HILLS, body: plan(25), rounds: 4 },
  { name: "westwood-malibu +25", router: WESTWOOD_MALIBU, body: plan(25), rounds: 5 },
  { name: "westwood-malibu back roads 32", router: WESTWOOD_MALIBU, body: plan(32, { back_roads: true }), rounds: 1 },
  { name: "westwood-malibu back roads 31", router: WESTWOOD_MALIBU, body: plan(31, { back_roads: true }), rounds: 1 },
  { name: "step at lambda 4", router: curveRouter(1_000_000, (l) => (l >= 4 ? 9_000_000 : 1_000_000 + l * 100_000), FAST_WAYS, SCENIC_WAYS),
    body: plan(25), rounds: 4 },
  { name: "every scenic route overshoots", router: curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000 + 1, FAST_WAYS, SCENIC_WAYS),
    body: plan(25), rounds: 5 },
  { name: "exactly at the ceiling", router: curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000, FAST_WAYS, SCENIC_WAYS), body: plan(25) },
  { name: "router refuses car_fast", router: refusing(SANTA_MONICA_TOPANGA, "fastest"), body: plan(25) },
  { name: "router refuses every scenic model", router: refusing(SANTA_MONICA_TOPANGA, "scenic"), body: plan(25) },
  ...Array.from({ length: 40 }, (_, index): Row => {
    const random = lcg(index + 1);
    const fastestMs = 600_000 + Math.floor(random() * 1_200_000);
    const minutes = Math.floor(random() * 40);
    const knots = Array.from({ length: 9 }, () => Math.floor(random() * 3_000_000));
    const curve = (lambda: number) => Math.max(1, fastestMs + knots[Math.min(8, Math.floor(lambda))]! - 900_000);
    return { name: `random curve ${index + 1}`, router: curveRouter(fastestMs, curve, FAST_WAYS, SCENIC_WAYS), body: plan(minutes) };
  }),
];

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function answer(row: Row) {
  const h = harness(row.router);
  const response = await handlePlan(planRequest(row.body), {}, h.deps);
  const text = await response.text();
  return { status: response.status, length: text.length, sha256: await sha256(text) };
}

/** Captured from main 0399dcea's src (sequential schedule), before any src change - quoted in the task Log. */
const GOLDEN: Record<string, { status: number; length: number; sha256: string }> = {
  "every scenic route overshoots": { status: 502, length: 118, sha256: "a5de0ac7046d669f99db8df12363c3f70f868b496754ec2fcf36018071b91f7b" },
  "exactly at the ceiling": { status: 200, length: 771, sha256: "3dadb0b3b3ffbaad94894efae3050d24351a0e3b4419128e6e09d145728fade0" },
  "random curve 1": { status: 200, length: 778, sha256: "0a2582b9e9166b922a799a7fdb5de4f3700e0064087673048c25993fab299762" },
  "random curve 10": { status: 200, length: 780, sha256: "cfef97f3ba754eec19dd03679c3e12b00f10aa986fcb5fdd176ae81d3afae3d0" },
  "random curve 11": { status: 200, length: 779, sha256: "f94f23f1dd74023a3848b0cdec1700a95da62eb3303f80ddc133eb34deb7055a" },
  "random curve 12": { status: 200, length: 781, sha256: "7e0bb9306e7b76c34af2259f08b2ca1beafad76f2be3790a225ae506c2d36a1d" },
  "random curve 13": { status: 200, length: 783, sha256: "5d9c20903c8ee3c08c863478c5d1da4ed837213abd7d99439cdb6970d8628e69" },
  "random curve 14": { status: 200, length: 779, sha256: "f370549ebb720374c61ecd91b944b42c18c37d9787c1b03f48e4759068b6c266" },
  "random curve 15": { status: 200, length: 782, sha256: "1a186f012b969ee247bedae8b0755d57fd16e5cc3186022fd7d64d06c173b29f" },
  "random curve 16": { status: 200, length: 788, sha256: "008fd63de2510fd3a1315dbda71a38b1d60f01951646c3f59d85fcd16fc51887" },
  "random curve 17": { status: 200, length: 779, sha256: "78ed0d5934cc141b80b95efabbdcf11724f3521adba0b5378a1323f262081af7" },
  "random curve 18": { status: 200, length: 779, sha256: "0c786aa5020282fe109438f255d1418b8b91d8ab468e0a31ef40e4ece222624e" },
  "random curve 19": { status: 200, length: 777, sha256: "cc8bc2e242c9a7eae509d01f17480b9f99f19fa3352c176e74ebae4d98603ce3" },
  "random curve 2": { status: 200, length: 782, sha256: "49864c28e3b9f03d0698f56c988221ced937b507b9b5dd7d0f6ce0a2b2e25ace" },
  "random curve 20": { status: 502, length: 132, sha256: "de664d022a4b79f853ac6b070e41936c79a6b465511e9df19893c5d904cbe850" },
  "random curve 21": { status: 200, length: 778, sha256: "d09d279fa1febd5be1b0684752683152f24706dab799786493cd00b189b46e4c" },
  "random curve 22": { status: 200, length: 781, sha256: "0d048dfac08d302d3a492167deb4618488de64439b74c1f2f693b4f12de6b692" },
  "random curve 23": { status: 200, length: 777, sha256: "4e2361c65fe6de8906d15f0e7c3bc0885f8bd104ce9b670d11aa481f41c602e1" },
  "random curve 24": { status: 200, length: 782, sha256: "d6e190ff732fbda305fc57b939db6ee95c683b6096e2c475914ae9b0aeea7c8d" },
  "random curve 25": { status: 200, length: 779, sha256: "7a8a93fd52b79b2c5e28bec6d5f1686ee6f3d3966978b34a6a0fc31daed798a4" },
  "random curve 26": { status: 200, length: 779, sha256: "a6fac0fdacab2e1df2d600d43601a508ac8e7de87514c2dd46f3c4ab52bcfe2c" },
  "random curve 27": { status: 200, length: 791, sha256: "4c9ed35b48ffb91ec4c92a57fb6fa60f05519ac72a4a30910d45e40e5fb33c74" },
  "random curve 28": { status: 200, length: 779, sha256: "83c3d16b8357a5389298f30f41a1e09786ce30761b4c8d7e61d5e00a97bb1ae2" },
  "random curve 29": { status: 200, length: 779, sha256: "f5a00989a84038a5063fc50383daae8a02deacfad5b712b247a2805768b608ff" },
  "random curve 3": { status: 200, length: 779, sha256: "0efb3b59f1c9fcc6e5579ec0f710c7253fb759b4283e9545ad0fb6ee094cf04c" },
  "random curve 30": { status: 200, length: 779, sha256: "c0f44d4c1834ed6a10f2b2f5caa9ad7e064a6a868039d6089800d17105d3a81c" },
  "random curve 31": { status: 200, length: 788, sha256: "f46811c7af0a83074c1c7b6219f6eafe6b39b7f0d7cc89411ccd81d8899b8379" },
  "random curve 32": { status: 200, length: 781, sha256: "0ab96be444f871f48ae85de74bf946b049184b6df2e2911726e4f5c54a60cab5" },
  "random curve 33": { status: 200, length: 788, sha256: "d46226a7f22d957679129a4c38ace20ba948782f5e14a7d1753a99f06fcf4477" },
  "random curve 34": { status: 200, length: 788, sha256: "8e7aa47748da1d96e7bc3c70508b013655f1d8b7f5efdc38ba53809d664ea784" },
  "random curve 35": { status: 200, length: 782, sha256: "6ad307090ef000cb45e848e0ca0a6a9e823d051dc30d873f304bd778eff7fe2c" },
  "random curve 36": { status: 200, length: 782, sha256: "4e54d8bc43fe1be8266236f982ce1d13e8fcf96a828478d26aaad9fe232a77c8" },
  "random curve 37": { status: 200, length: 792, sha256: "4a742481e7ad3fff708553225fed63a5c32ecd02055fb70de9c4bb30ee132bbd" },
  "random curve 38": { status: 200, length: 779, sha256: "82722340265c84781e39843ce87d646305abce9fab1974520de0a282fe6970f6" },
  "random curve 39": { status: 200, length: 782, sha256: "be738744822cbf438e30f64cca81dd94928e894ddfd5fda383b9cd628993feff" },
  "random curve 4": { status: 200, length: 779, sha256: "2fc9b9daf8753909ca66c17b9cd2a9572b863481d1cb367a24cbd8d4f94a817b" },
  "random curve 40": { status: 200, length: 782, sha256: "ec0b81987f59f58ab16b105dfb613b5664cb13cc6db4a6cda82d239292e98060" },
  "random curve 5": { status: 200, length: 792, sha256: "fdb1c4f07e30aaad25f37effffc2de59cb291fe2ca1aa2581876e3bbfbbaf4e2" },
  "random curve 6": { status: 200, length: 779, sha256: "dfe0aab2e4207a0d1b2bbb9347ce51b2f59283fbe83d4b6bc180058558843780" },
  "random curve 7": { status: 200, length: 792, sha256: "5b9050cd06899e3625058750eb8dbb131c7eb6fbb4dc940c8fe6ba05bcd89709" },
  "random curve 8": { status: 200, length: 777, sha256: "c38902ceb78e30db8f1ea1d7b7d3fbfb78986a7055e2e682eac9868c1292c9f6" },
  "random curve 9": { status: 200, length: 778, sha256: "3ad89d37930f2266e79f34683b9ddf4478b89293969167c50ebf92eee1e5b752" },
  "router refuses car_fast": { status: 502, length: 39, sha256: "f99f1a657abe8aef7b0f2bb6ba7af0cb40ecd58224cafbda8d9211d32a2b647a" },
  "router refuses every scenic model": { status: 502, length: 61, sha256: "5ae17c4d09e7f32cfcd98ff1ff7c25a10bc1e5f1d3c3c53184b1a60b3cc8b397" },
  "santa-monica-topanga +25": { status: 200, length: 17016, sha256: "4aef4e516b779603df39ccbec0a86ff3ebbb2e8039c564b7b2e09f5194deab9a" },
  "step at lambda 4": { status: 200, length: 772, sha256: "722df4eac76fcb86f6d03f91a694e2a001686d7de53998895b719f9b953edb09" },
  "westwood-malibu +25": { status: 422, length: 127, sha256: "0715a41dca92e98be08d963e29d6f6a1e995aa923bff5acf0ebe1f6c8d066300" },
  "westwood-malibu back roads 31": { status: 500, length: 28, sha256: "97211b2d6ab36ce00b6db45b6574de54441d58b50d5b2b0ca49fa5799df7408c" },
  "westwood-malibu back roads 32": { status: 200, length: 45085, sha256: "e8dd87bcd7dcfbb2cd88b4fb0dbd89063295e78652b3c7d3fde3cbb1a83ff9e7" },
  "westwood-woodland-hills +25": { status: 200, length: 18835, sha256: "5ca7b072c771d5ce1794074963fa74638db7557672372633789b278dc24dbe8d" },
};

describe("POST /plan two in flight: every answer byte-equal (T-0403 acceptance 1, P-SAFE-04)", () => {
  it("the table covers 50 rows and GOLDEN holds exactly those rows", () => {
    expect(ROWS).toHaveLength(50);
    expect(Object.keys(GOLDEN).sort()).toEqual(ROWS.map((r) => r.name).sort());
  });

  for (const row of ROWS) {
    it(`${row.name}: status, length and sha256 of the whole answer equal the sequential schedule's`, async () => {
      expect({ [row.name]: await answer(row) }).toEqual({ [row.name]: GOLDEN[row.name] });
    });
  }

  it("the back roads 31 row is the ceiling refusal, byte for byte", async () => {
    const h = harness(WESTWOOD_MALIBU);
    const response = await handlePlan(planRequest(plan(31, { back_roads: true })), {}, h.deps);
    expect({ status: response.status, text: await response.text() }).toEqual({ status: 500, text: JSON.stringify({ error: "ceiling_breached" }) });
  });
});

const T = 100;

describe("POST /plan over a router that takes T ms per request (T-0403 acceptance 2, P-COST-04)", () => {
  for (const row of ROWS.filter((r) => r.rounds !== undefined)) {
    it(`${row.name}: wall <= ${row.rounds}T, never more than 2 requests in flight`, async () => {
      const h = harness(row.router);
      const timed = timedRouter(h, T);
      const { value: status, wall } = await timed.drive(async () => (await handlePlan(planRequest(row.body), {}, h.deps)).status);
      expect({ status, roundsAtMost: wall <= row.rounds! * T, wall, peak: timed.peakInFlight() <= 2 })
        .toEqual({ status: GOLDEN[row.name]!.status, roundsAtMost: true, wall: row.rounds! * T, peak: true });
      expect(timed.calls.every((c) => c.end - c.start === T)).toBe(true);
      expect(timed.calls).toHaveLength(h.sent.length);
    });
  }

  it("a full plan keeps 2 requests in flight in every round (T-0411): fast || 4, 0 || 6, 7 || 7.5 (the guess), then 7.75", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const timed = timedRouter(h, T);
    await timed.drive(() => handlePlan(planRequest(plan(25)), {}, h.deps));
    const lambdaOf = (model: unknown) => [0, 4, 6, 7, 7.5, 7.75].find((l) => JSON.stringify(model) === JSON.stringify(buildCustomModel(l, null)));
    expect(h.sent.map((s) => s.body.profile === "car_fast" ? "fast" : lambdaOf(s.body.custom_model))).toEqual(["fast", 4, 0, 6, 7, 7.5, 7.75]);
    expect(timed.calls.map((c) => c.start)).toEqual([0, 0, T, T, 2 * T, 2 * T, 3 * T]);
    expect(timed.peakInFlight()).toBe(2);
  });
});
