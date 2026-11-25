import { BudgetSlider } from "../ui/BudgetSlider";
import { LIVE_MAX_BUDGET_MINUTES } from "./budget";
import { LiveResult } from "./LiveResult";
import { OriginPicker } from "./OriginPicker";
import { PlacePicker } from "./PlacePicker";
import type { LivePlanner } from "./useLivePlanner";

/** Plan any drive: start, destination, budget, then one explicit press per plan. */
export function LivePanel({ live }: { live: LivePlanner }) {
  if (!live.available) {
    return (
      <section className="hero" role="status">
        <h2 className="hero-title">Live planning runs in dev</h2>
        <p className="hint">
          This build has no API proxy. Run <code>npm run dev</code>, or set VITE_API_BASE to an API that allows
          this origin.
        </p>
      </section>
    );
  }
  const current = live.current;
  return (
    <>
      <OriginPicker value={live.origin} onChange={live.setOrigin} />
      <PlacePicker value={live.destination} origin={live.origin} onChange={live.setDestination} />
      <BudgetSlider value={live.budget} max={LIVE_MAX_BUDGET_MINUTES} onChange={live.setBudget} />
      {live.destination && (
        <LiveResult
          destination={live.destination}
          budget={live.budget}
          loading={live.loading}
          plan={current?.state === "done" ? current.plan : null}
          failure={current?.state === "failed" ? current.failure : null}
          onRetry={(overrides) => void live.plan(overrides)}
        />
      )}
    </>
  );
}
