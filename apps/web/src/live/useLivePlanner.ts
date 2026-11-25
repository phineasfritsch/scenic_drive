import { useCallback, useEffect, useRef, useState } from "react";
import { apiBase, dailyPlanAllowance, planLive } from "./api";
import { suggestedBudget } from "./budget";
import { ORIGINS } from "./places";
import type { LiveFailure, LivePlace, LivePlan, Origin } from "./types";

export type LiveStatus =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "done"; plan: LivePlan; key: string }
  | { state: "failed"; failure: LiveFailure; key: string };

const keyOf = (origin: Origin | null, destination: LivePlace | null, budget: number) =>
  `${origin?.lat},${origin?.lon}|${destination?.id}|${budget}`;

/**
 * Live planning state. A plan is only ever requested by an explicit press: each one spends one of the
 * device's few daily plans, so nothing here plans on input changes.
 */
export function useLivePlanner() {
  const [origin, setOriginState] = useState<Origin | null>(ORIGINS[0]!);
  const [destination, setDestinationState] = useState<LivePlace | null>(null);
  const [budget, setBudget] = useState(20);
  const [status, setStatus] = useState<LiveStatus>({ state: "idle" });
  const [allowance, setAllowance] = useState<number | null>(null);
  const inflight = useRef<AbortController | null>(null);

  useEffect(() => {
    void dailyPlanAllowance().then(setAllowance);
    return () => inflight.current?.abort();
  }, []);

  // A new trip starts from a budget sized to it (budget.ts); the user's own slider move then stands.
  const suggest = (o: Origin | null, d: LivePlace | null) => {
    if (o && d) setBudget(suggestedBudget([o.lon, o.lat], d.at));
  };
  const setOrigin = (o: Origin | null) => {
    setOriginState(o);
    suggest(o, destination);
  };
  const setDestination = (d: LivePlace | null) => {
    setDestinationState(d);
    suggest(origin, d);
  };

  const key = keyOf(origin, destination, budget);
  const current = (status.state === "done" || status.state === "failed") && status.key === key ? status : null;

  const plan = useCallback(
    async (overrides: { budget?: number; allBackRoads?: boolean } = {}) => {
      if (!origin || !destination) return;
      const minutes = overrides.budget ?? budget;
      if (overrides.budget !== undefined) setBudget(minutes);
      inflight.current?.abort();
      const controller = new AbortController();
      inflight.current = controller;
      setStatus({ state: "loading" });
      try {
        const outcome = await planLive(
          { origin, placeId: destination.id, budgetMinutes: minutes, allBackRoads: overrides.allBackRoads },
          controller.signal,
        );
        const k = keyOf(origin, destination, minutes);
        setStatus(outcome.ok ? { state: "done", plan: outcome.plan, key: k } : { state: "failed", failure: outcome.failure, key: k });
      } catch {
        // Aborted by a newer request or by leaving live mode.
      }
    },
    [origin, destination, budget],
  );

  return {
    available: apiBase() !== null,
    origin,
    setOrigin,
    destination,
    setDestination,
    budget,
    setBudget,
    loading: status.state === "loading",
    /** The plan or failure for exactly the current inputs; null once any input changes. */
    current,
    plan,
    allowance,
  };
}

export type LivePlanner = ReturnType<typeof useLivePlanner>;
