import type { Tier } from "./quota";
import type { UpstreamDeps } from "./upstream";

export interface PlanDeps {
  upstream: UpstreamDeps;
  routerBase: string;
  resolvePlace(id: string): Promise<{ lat: number; lon: number } | null>;
  identify(req: Request): { userId: string; tier: Tier };
}

export async function handlePlan(_req: Request, _env: { KILL?: string }, _deps: PlanDeps | null): Promise<Response> {
  return new Response(JSON.stringify({ error: "not implemented" }), { status: 501 });
}
