/**
 * The manual kill switch (P-COST-01, T-0256 R5). Either source pauses - OR, never precedence - so a KV value can
 * never UN-pause a deploy whose env says KILL=1:
 *   env.KILL === "1"                 the existing override, read first and always;
 *   KV `KILL_SWITCH`, key "KILL"     when that namespace is bound: "1" pauses, and a read that throws pauses.
 * Read once, first, before the request body - the handler hands that one answer to guardedPlan.
 */
export const KILL_KEY = "KILL";

/** The one thing the kill decision reads from the KILL_SWITCH binding (a KVNamespace satisfies it). */
export interface KillSwitchRead {
  get(key: string): Promise<string | null>;
}

export interface KillEnv {
  /** Manual override: "1" pauses all planning without a deploy. */
  KILL?: string;
  /** Optional KV namespace; the owner binds it. Its key KILL = "1" pauses all planning without a deploy. */
  KILL_SWITCH?: KillSwitchRead;
}

export async function killSwitch(env: KillEnv): Promise<boolean> {
  if (env.KILL === "1") return true;
  if (!env.KILL_SWITCH) return false;
  try {
    return (await env.KILL_SWITCH.get(KILL_KEY)) === "1";
  } catch {
    return true;
  }
}

/**
 * T-0297 (T-0292 residual R-A): workerd hands every request of an isolate the SAME binding objects, and its
 * KVNamespace.get is an inherited method - so a handler that assigned env.KILL_SWITCH.get (an own property shadowing
 * it), or the class every KV binding shares, would bend every later kill read. The kill read never goes
 * through the shared binding's get at request time: CAPTURED holds that get, bound to its binding, from the first time
 * default.fetch sees the binding - before any handler of the isolate has run - and each request's handler gets a fresh
 * frozen KillSwitchReader over the capture in place of the binding. A write to the reader, own or inherited, throws.
 */
type KillRead = (key: string) => Promise<string | null>;
const CAPTURED = new WeakMap<KillSwitchRead, KillRead>();

class KillSwitchReader implements KillSwitchRead {
  #read: KillRead = async () => {
    throw new TypeError("KillSwitchReader without a capture");
  };

  static over(read: KillRead): KillSwitchReader {
    const reader = new KillSwitchReader();
    reader.#read = read;
    return Object.freeze(reader);
  }

  async get(key: string): Promise<string | null> {
    return this.#read(key);
  }
}
Object.freeze(KillSwitchReader.prototype);

function capture(binding: KillSwitchRead): KillRead {
  try {
    return binding.get.bind(binding);
  } catch {
    return async () => {
      throw new TypeError("KILL_SWITCH has no get");
    };
  }
}

/** The per-request KILL_SWITCH a handler holds: a fresh frozen reader over the binding's get as first seen. */
export function killSwitchReader(binding: KillSwitchRead | undefined): KillSwitchRead | undefined {
  if (!binding) return undefined;
  let read = CAPTURED.get(binding);
  if (!read) {
    read = capture(binding);
    CAPTURED.set(binding, read);
  }
  return KillSwitchReader.over(read);
}
