/**
 * The manual kill switch (P-COST-01, T-0256 R5). Either source pauses - OR, never precedence - so a KV value can
 * never UN-pause a deploy whose env says KILL=1:
 *   env.KILL === "1"                 the existing override, read first and always;
 *   KV `KILL_SWITCH`, key "KILL"     when that namespace is bound: "1" pauses, and a read that throws pauses.
 * Read once, first, before the request body - the handler hands that one answer to guardedPlan.
 */
export const KILL_KEY = "KILL";

export interface KillEnv {
  /** Manual override: "1" pauses all planning without a deploy. */
  KILL?: string;
  /** Optional KV namespace; the owner binds it. Its key KILL = "1" pauses all planning without a deploy. */
  KILL_SWITCH?: KVNamespace;
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
