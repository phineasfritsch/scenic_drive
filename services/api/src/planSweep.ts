/**
 * T-0326 (P-PRIV-04): DELETE /account sweeps PLANS - every remembered plan of every one of the user's devices goes
 * with the account, not after PLAN_TOKEN_TTL_SECONDS.
 *
 * Per device the sweep lists `plan:<device>:` and follows the cursor until list_complete (a page may hold fewer keys
 * than asked, even none, while more remain - R5), deleting a key only when it is the prefix followed by a PLAN_TOKEN:
 * the key shape is a whitelist, so a longer key, an uppercase token or another device whose id extends this one is
 * never deleted. It spends at most PLAN_SWEEP_MAX_OPS KV operations (R7). The answer is true only when every list
 * and every delete succeeded inside the bound; anything else is false and the caller answers plans_pending (R6).
 * KV is eventually consistent (R8): a key written elsewhere moments before may be unlisted and lives to its TTL.
 */
import { PLAN_TOKEN, planKeyPrefix } from "./planToken";

/** 900 KV operations (lists + deletes), under the Workers limit of 1000 per invocation (T-0326 R7). */
export const PLAN_SWEEP_MAX_OPS = 900;

/** One page of a KV list - KVNamespace's shape, the fields the sweep reads. */
export interface PlanSweepPage {
  keys: { name: string }[];
  list_complete: boolean;
  cursor?: string;
}

/** The two KV calls the sweep makes - a KVNamespace satisfies it. */
export interface PlanSweepKv {
  list(options: { prefix: string; cursor?: string }): Promise<PlanSweepPage>;
  delete(key: string): Promise<void>;
}

/** Deletes every plan of every device in `devices`; true iff nothing was left undone. */
export async function sweepPlans(kv: PlanSweepKv, devices: string[]): Promise<boolean> {
  let ops = 0;
  let whole = true;
  for (const device of devices) {
    const prefix = planKeyPrefix(device);
    let cursor: string | undefined;
    for (;;) {
      if (ops >= PLAN_SWEEP_MAX_OPS) return false;
      ops += 1;
      let page: PlanSweepPage;
      try {
        page = await kv.list(cursor === undefined ? { prefix } : { prefix, cursor });
      } catch {
        whole = false;
        break;
      }
      const mine = page.keys.map((k) => k.name)
        .filter((name) => name.startsWith(prefix) && PLAN_TOKEN.test(name.slice(prefix.length)));
      const now = mine.slice(0, PLAN_SWEEP_MAX_OPS - ops);
      ops += now.length;
      const settled = await Promise.allSettled(now.map((name) => kv.delete(name)));
      if (settled.some((s) => s.status === "rejected")) whole = false;
      if (now.length < mine.length) return false;
      if (page.list_complete) break;
      if (typeof page.cursor !== "string" || page.cursor === "") {
        whole = false;
        break;
      }
      cursor = page.cursor;
    }
  }
  return whole;
}
