/**
 * T-0267 R2 as a WHITELIST: the pinned Apple root is a literal, never read from env. Every line of src/ that names
 * rootSha256 is one of the approved sites below - the AsnPolicy field, the comparison in the verifier and the one
 * assignment in asnDepsFromEnv, to the literal APPLE_ROOT_CA_G3_SHA256 - so an env or secret override of the pin
 * (`env.X ?? APPLE_ROOT_CA_G3_SHA256`, a spread over the deps in ROUTES) changes this set and fails. On the test
 * side, the only places a rootSha256 value is BUILT (not read with `.rootSha256`) are the test chain and testDeps,
 * so no test reaches ROUTES with a replaced root. Whole lines compared; only //-leading lines are dropped.
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob("../src/**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const TEST = import.meta.glob("./**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const SELF = "./asnRootPin.test.ts";

function sites(files: Record<string, string>, keep: (line: string) => boolean): [string, string][] {
  const out: [string, string][] = [];
  for (const [path, text] of Object.entries(files).sort(([a], [b]) => a.localeCompare(b))) {
    if (path === SELF) continue;
    for (const raw of text.split("\n")) {
      const line = raw.trim();
      if (!line.startsWith("//") && keep(line)) out.push([path, line]);
    }
  }
  return out;
}

describe("the Apple root pin cannot be overridden (R2)", () => {
  it("every src line naming rootSha256 is an approved site, the deps' one assigning the literal", () => {
    expect(sites(SRC, (l) => l.includes("rootSha256"))).toEqual([
      ["../src/appAttest.ts", "/** The root certificate's DER; it must hash to rootSha256 or every attestation is refused. */"],
      ["../src/appAttest.ts", "rootSha256: string;"],
      ["../src/appAttest.ts", "if ((await sha256Hex(trust.rootDer)) !== trust.rootSha256) reject(\"root is not the pinned root\");"],
      ["../src/appleJws.ts", "rootSha256: string;"],
      ["../src/appleJws.ts", "if ((await sha256Hex(root.der)) !== trust.rootSha256) reject(\"root is not the pinned root\");"],
      ["../src/asn.ts", "rootSha256: APPLE_ROOT_CA_G3_SHA256,"],
      ["../src/attest.ts", "rootSha256: APPLE_APP_ATTEST_ROOT_CA_SHA256,"],
    ]);
  });

  it("T-0278: every src line naming the App Attest root DER is an approved site, the deps' one the decoded literal", () => {
    expect(sites(SRC, (l) => l.includes("rootDer") || l.includes("ROOT_DER"))).toEqual([
      ["../src/appAttest.ts", "rootDer: Uint8Array;"],
      ["../src/appAttest.ts", "if ((await sha256Hex(trust.rootDer)) !== trust.rootSha256) reject(\"root is not the pinned root\");"],
      ["../src/appAttest.ts", "certs = [...x5c, trust.rootDer].map(parseCertificate);"],
      ["../src/attest.ts", "const ROOT_DER = Uint8Array.from(atob(APPLE_APP_ATTEST_ROOT_CA), (c) => c.charCodeAt(0));"],
      ["../src/attest.ts", "rootDer: ROOT_DER,"],
    ]);
  });

  it("every test line building a rootSha256 value is the test chain or testDeps", () => {
    expect(sites(TEST, (l) => l.replace(/\.rootSha256/g, "").includes("rootSha256"))).toEqual([
      ["./appleChain.ts", "export interface Chain { x5c: string[]; leaf: Party; rootSha256: string }"],
      ["./appleChain.ts", "return { x5c: [leafDer, interDer, rootDer].map(b64), leaf, rootSha256: await fingerprint(rootDer) };"],
      ["./asnHarness.ts", "export function testDeps(rootSha256: string, extra: Partial<Env> = {}): AsnDeps {"],
      ["./asnHarness.ts", "return { ...asnDepsFromEnv({ ...(env as unknown as Env), ...extra }), rootSha256 };"],
      ["./attestHarness.ts", "export interface Attested { keyId: string; attestation: string; rootDer: Uint8Array; rootSha256: string; publicKeyHex: string }"],
      ["./attestHarness.ts", "return { keyId: b64(spec.keyId ? spec.keyId(keyId) : keyId), attestation: b64(cbor(object)), rootDer, rootSha256: hex(await sha(rootDer)),"],
      ["./attestHarness.ts", "export function testDeps(a: Pick<Attested, \"rootDer\" | \"rootSha256\">, extra: Partial<Env> = {}): AttestDeps {"],
      ["./attestHarness.ts", "return { ...attestDepsFromEnv({ ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET, ...extra }), rootDer: a.rootDer, rootSha256: a.rootSha256 };"],
      ["./attestVerify.test.ts", "{ name: \"the root does not hash to the pin\", deps: (a) => ({ rootSha256: `${a.rootSha256.slice(0, -1)}${a.rootSha256.endsWith(\"0\") ? \"1\" : \"0\"}` }) },"],
    ]);
  });
});
