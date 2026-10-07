/**
 * T-0288: the intrinsics snapshot - globalThis's own properties, theirs, and their prototypes' (every descriptor by
 * identity: value, getter, setter, flags; every [[Prototype]]; 1000+ entries) - shared by the load-time check
 * (configAnswerPath.test.ts) and the post-sweep check (configSweep.test.ts). Moved here unchanged from
 * configAnswerPath.test.ts (rv4 B1) so both checks compare the SAME descriptor population.
 */
export type Shot = Map<string, unknown[]>;

/** Measured: the descriptors workerd answers with a fresh array (or a fresh getter) per lookup; compared by the JSON of the value. */
const BY_VALUE = new Set(["globalThis.navigator.languages", "globalThis.[[Prototype]].PerformanceObserver.supportedEntryTypes"]);

/**
 * globalThis's own properties, theirs, and their prototype's: every descriptor by identity, every [[Prototype]].
 * Breadth first (rv4 B1, measured): depth first let an object first met at depth 2 (never expanded) mark itself seen,
 * so its later depth-1 path was skipped - Response.prototype's own members went unrecorded and a request-time patch
 * of Response.prototype.text passed the post-sweep check. Breadth first records every object at its shallowest path.
 */
export function snapshot(): Shot {
  const shot: Shot = new Map();
  const seen = new Set<object>([globalThis]);
  const queue: [object, string, number][] = [[globalThis, "globalThis", 0]];
  for (let i = 0; i < queue.length; i++) {
    const [o, path, depth] = queue[i]!;
    const proto = Object.getPrototypeOf(o) as object | null;
    shot.set(`${path} [[Prototype]]`, [proto]);
    // workerd defines its API classes (Response, Request, Headers, URL...) on the global scope's PROTOTYPE, not as own
    // properties of globalThis (measured, rv4 B1: a Response.prototype.text patch passed). Every object on globalThis's
    // prototype chain is walked as a global scope itself (depth 0).
    if (depth === 0 && proto !== null && !seen.has(proto)) {
      seen.add(proto);
      queue.push([proto, `${path}.[[Prototype]]`, 0]);
    }
    for (const key of Reflect.ownKeys(o)) {
      const d = Object.getOwnPropertyDescriptor(o, key);
      if (d === undefined) continue;
      const at = `${path}.${String(key)}`;
      if (BY_VALUE.has(at)) {
        let value: unknown = d.value;
        if (d.get !== undefined) try { value = d.get.call(o); } catch { value = "getter threw"; }
        shot.set(at, [JSON.stringify(value), typeof d.get, typeof d.set, d.writable, d.enumerable, d.configurable]);
        continue;
      }
      shot.set(at, [d.value, d.get, d.set, d.writable, d.enumerable, d.configurable]);
      // A global scope's accessor (a lazily defined global) is resolved against globalThis and its value expanded.
      let v = d.value as unknown;
      if (depth === 0 && d.get !== undefined) try { v = d.get.call(globalThis); } catch { v = undefined; }
      if (depth < 2 && v !== null && (typeof v === "object" || typeof v === "function") && !seen.has(v as object)) {
        seen.add(v as object);
        queue.push([v as object, at, depth + 1]);
      }
    }
  }
  return shot;
}

/** Measured (rv4 B1): the test RUNNER's own bookkeeping, which moves between any two snapshots; nothing src runs on. */
export const RUNNER = ["globalThis.__vitest_worker__.", "globalThis.Symbol($$jest-matchers-object)."];

export function changed(before: Shot, after: Shot): string[] {
  const keys = new Set([...before.keys(), ...after.keys()]);
  return [...keys].filter((k) => !RUNNER.some((r) => k.startsWith(r))).filter((k) => {
    const a = before.get(k);
    const b = after.get(k);
    return a === undefined || b === undefined || a.length !== b.length || a.some((x, i) => !Object.is(x, b[i]));
  }).sort();
}
