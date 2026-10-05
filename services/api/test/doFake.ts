/**
 * The in-memory DurableObjectState the QuotaCounter tests run over, and the recording router the shipped deps
 * reach through the global fetch. Not a test file (vitest includes *.test.ts).
 *
 * R9: storage.get returns a structuredClone of what is stored (DO storage is structured-clone serialised, so a
 * caller mutating what it read cannot change storage); storage.put stores a structuredClone; transaction(fn)
 * hands fn a txn over a STAGED copy and commits it only when fn resolves - a throw discards it.
 */
import { QuotaCounter } from "../src/QuotaCounter";
import type { Recording } from "./planHarness";

type Store = Map<string, unknown>;

function view(store: Store) {
  return {
    async get<T>(key: string): Promise<T | undefined> {
      return store.has(key) ? (structuredClone(store.get(key)) as T) : undefined;
    },
    async put(key: string, value: unknown): Promise<void> {
      store.set(key, structuredClone(value));
    },
  };
}

export class FakeStorage {
  readonly data: Store = new Map();

  get<T>(key: string): Promise<T | undefined> {
    return view(this.data).get<T>(key);
  }

  put(key: string, value: unknown): Promise<void> {
    return view(this.data).put(key, value);
  }

  async transaction<T>(fn: (txn: ReturnType<typeof view>) => Promise<T>): Promise<T> {
    const staged: Store = new Map([...this.data].map(([k, v]) => [k, structuredClone(v)]));
    const result = await fn(view(staged));
    this.data.clear();
    for (const [k, v] of staged) this.data.set(k, v);
    return result;
  }
}

export interface FakeQuota {
  ns: DurableObjectNamespace<QuotaCounter>;
  /** Every instance's whole storage, by the name it was addressed by. */
  state(): Record<string, Record<string, unknown>>;
  /** Put a record straight into a named instance's storage. */
  seed(name: string, key: string, value: unknown): void;
}

export function fakeQuotaNamespace(): FakeQuota {
  const instances = new Map<string, { storage: FakeStorage; counter: QuotaCounter }>();
  const instance = (name: string) => {
    let found = instances.get(name);
    if (!found) {
      const storage = new FakeStorage();
      // workerd's DurableObjectBase constructor refuses anything but a real DurableObjectState, so the instance is
      // the real class's prototype with `ctx` set as that constructor sets it: every method under test is the
      // shipped one, and QuotaCounter declares no constructor of its own to skip.
      const counter = Object.assign(Object.create(QuotaCounter.prototype), { ctx: { storage }, env: {} }) as QuotaCounter;
      found = { storage, counter };
      instances.set(name, found);
    }
    return found;
  };
  const ns = {
    idFromName: (name: string) => ({ name }),
    get: (id: { name: string }) => instance(id.name).counter,
  };
  return {
    ns: ns as unknown as DurableObjectNamespace<QuotaCounter>,
    state: () => Object.fromEntries([...instances].map(([name, i]) => [name, Object.fromEntries(i.storage.data)])),
    seed: (name, key, value) => void instance(name).storage.data.set(key, value),
  };
}

export interface RouterCall {
  url: string;
  headers: [string, string][];
  body: Record<string, unknown>;
}

/** A stand-in for the global fetch: answers /plan from a recording and /loop's round_trip with `loop`. */
export function recordingRouter(plan: Recording, loop: string, onFetch: () => void = () => {}) {
  const calls: RouterCall[] = [];
  const fetchImpl = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    onFetch();
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    calls.push({ url: String(input), headers: [...new Headers(init?.headers)], body });
    if (body.algorithm === "round_trip") return new Response(loop);
    if (body.profile === "car_fast" && body.custom_model === undefined) return new Response(plan.fastest);
    const text = body.profile === "car_scenic" ? plan.scenic(body.custom_model) : undefined;
    if (text !== undefined) return new Response(text);
    return new Response(JSON.stringify({ message: "no recording" }), { status: 400 });
  };
  return { calls, fetchImpl };
}

/** A KV namespace that answers `get` from a table, or throws when told to. */
export function fakeKv(values: Record<string, string>, fail = false): KVNamespace {
  return {
    get: async (key: string) => {
      if (fail) throw new Error("kv unavailable");
      return values[key] ?? null;
    },
  } as unknown as KVNamespace;
}
