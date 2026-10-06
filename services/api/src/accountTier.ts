/**
 * The caller's quota tier (T-0272 R1-R5): paid exactly when the purchase id in x-scenic-account-token has a live
 * entitlement row - the same reader GET /entitlement answers from, so the two never disagree. Everything else is
 * anon: no header, a malformed one (no D1 read), an unknown token, an inactive or expired row, and ANY failure of
 * the read (fails closed on cost). Nothing here logs: the token is a bearer secret until App Attest + JWT (R5).
 */
import { ACCOUNT_TOKEN_HEADER, UUID } from "./asn";
import { readEntitlement } from "./entitlementStore";
import type { Tier } from "./quota";

export async function accountTier(req: Request, db: D1Database | undefined, nowMs: number): Promise<Tier> {
  const token = (req.headers.get(ACCOUNT_TOKEN_HEADER) ?? "").toLowerCase();
  if (db === undefined || !UUID.test(token)) return "anon";
  try {
    return (await readEntitlement(db, token, nowMs)).status === "active" ? "paid" : "anon";
  } catch {
    return "anon";
  }
}
