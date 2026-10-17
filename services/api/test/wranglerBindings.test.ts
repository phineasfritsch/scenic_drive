/**
 * T-0390: the bindings wrangler.jsonc declares are exactly the bindings the shipped Worker's Env reads. Env is
 * type-only, so its declarations are read from src/index.ts: every line of `export interface Env { ... }` is blank,
 * a //-leading line, or a `NAME?: TYPE;` declaration - any other line fails (fail closed). A field typed `string` is a
 * var or a secret; every other field is a binding whose wrangler section follows from its type, and a type this
 * table does not know maps to no section, so it fails. The two maps are compared whole: a binding added or dropped
 * on either side, or moved to another section, fails.
 */
import { describe, expect, it } from "vitest";
import wranglerRaw from "../wrangler.jsonc?raw";
import indexRaw from "../src/index.ts?raw";

const SECTION_OF_TYPE: Record<string, string> = {
  D1Database: "d1_databases",
  KVNamespace: "kv_namespaces",
  KillSwitchRead: "kv_namespaces",
  "DurableObjectNamespace<QuotaCounter>": "durable_objects",
  AnalyticsEngineDataset: "analytics_engine_datasets",
};

const KV_NAMESPACES = [
  { binding: "PLANS", id: "33e411b3b03246a19cda166c0c05cfd6" },
  { binding: "CONFIG", id: "8dd224a7fb554dc4a270f67162d28bb6" },
  { binding: "KILL_SWITCH", id: "8946404cc991458196d195c65ea15d7b" },
  { binding: "CLOSURES", id: "5e3eb553f16c4e4ba4d5297e001ef5ea" },
];

type Field = { name: string; type: string };

function envFields(source: string): Field[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const start = lines.indexOf("export interface Env {");
  const end = lines.indexOf("}", start);
  if (start < 0 || end < 0) throw new Error("no `export interface Env {` ... `}` block in src/index.ts");
  const fields: Field[] = [];
  for (const line of lines.slice(start + 1, end)) {
    const trimmed = line.trim();
    if (trimmed === "" || trimmed.startsWith("//")) continue;
    const m = /^([A-Z][A-Z0-9_]*)\??: ([^;]+);(\s*\/\/.*)?$/.exec(trimmed);
    if (!m) throw new Error(`an Env line that is not a NAME?: TYPE; declaration: ${trimmed}`);
    fields.push({ name: m[1], type: m[2].trim() });
  }
  return fields;
}

function wrangler(): Record<string, unknown> {
  return JSON.parse(wranglerRaw.split("\n").filter((line) => !line.trim().startsWith("//")).join("\n"));
}

function wranglerBindings(config: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {};
  const add = (section: string, entries: unknown) => {
    if (!Array.isArray(entries)) throw new Error(`wrangler section ${section} is not an array`);
    for (const e of entries as Record<string, unknown>[]) {
      const name = String(e.binding ?? e.name);
      if (name in out) throw new Error(`binding ${name} declared twice`);
      out[name] = section;
    }
  };
  for (const [key, value] of Object.entries(config)) {
    if (key === "durable_objects") add(key, (value as { bindings: unknown }).bindings);
    else if (key === "queues") add(key, (value as { producers: unknown }).producers);
    else if (Array.isArray(value) && value.some((e) => e && typeof e === "object" && ("binding" in e))) add(key, value);
  }
  return out;
}

function envBindings(fields: Field[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const f of fields) if (f.type !== "string") out[f.name] = SECTION_OF_TYPE[f.type] ?? `UNKNOWN TYPE ${f.type}`;
  return out;
}

describe("wrangler.jsonc binds exactly what the shipped Env reads (T-0390)", () => {
  it("the binding set of wrangler.jsonc equals the Env's non-string fields, each in its type's section", () => {
    expect(wranglerBindings(wrangler())).toEqual(envBindings(envFields(indexRaw)));
  });

  it("the four KV namespaces are bound by the shipped names to the owner's ids", () => {
    expect(wrangler().kv_namespaces).toEqual(KV_NAMESPACES);
  });

  it("every wrangler var is a string field of Env", () => {
    const strings = envFields(indexRaw).filter((f) => f.type === "string").map((f) => f.name);
    const vars = Object.keys(wrangler().vars as Record<string, string>);
    expect(vars.filter((v) => !strings.includes(v))).toEqual([]);
  });
});
