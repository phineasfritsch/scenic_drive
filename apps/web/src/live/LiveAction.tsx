import { directionsUrl } from "../format";
import { ArrowOut } from "../ui/Icons";
import type { LivePlanner } from "./useLivePlanner";

/**
 * The one primary action of live mode (P15). It never offers to repeat a plan that just failed for the same
 * inputs: every press spends one of the device's few daily plans.
 */
export function LiveAction({ live }: { live: LivePlanner }) {
  const { origin, destination, current } = live;
  const start: [number, number] | null = origin ? [origin.lon, origin.lat] : null;
  if (start && destination && current?.state === "done") {
    const via = current.plan.waypoints.map((w): [number, number] => [w.lon, w.lat]);
    return (
      <a className="button-primary" target="_blank" rel="noreferrer" href={directionsUrl(start, destination.at, via)}>
        Open in Google Maps <ArrowOut />
      </a>
    );
  }
  if (start && destination && current?.state === "failed") {
    if (current.failure.kind === "no_scenic_alternative") {
      return (
        <a className="button-primary" target="_blank" rel="noreferrer" href={directionsUrl(start, destination.at, [])}>
          Open the fastest way in Google Maps <ArrowOut />
        </a>
      );
    }
    if (current.failure.kind !== "offline") {
      return (
        <button type="button" className="button-primary" disabled>
          Change the trip to plan again
        </button>
      );
    }
  }
  const retry = current?.state === "failed" && current.failure.kind === "offline";
  return (
    <button type="button" className="button-primary" disabled={!destination || !origin || live.loading}
      aria-busy={live.loading} onClick={() => void live.plan()}>
      {live.loading ? "Planning…" : !destination ? "Choose a destination" : retry ? "Try again" : "Plan this drive"}
    </button>
  );
}
