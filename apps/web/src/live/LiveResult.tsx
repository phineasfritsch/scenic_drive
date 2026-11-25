import { useEffect, useRef } from "react";
import { miles, minutes } from "../format";
import { Clock } from "../ui/Icons";
import { endGapKm } from "./budget";
import type { LiveFailure, LivePlace, LivePlan } from "./types";

interface Props {
  destination: LivePlace;
  budget: number;
  loading: boolean;
  plan: LivePlan | null;
  failure: LiveFailure | null;
  onRetry: (overrides: { budget?: number; allBackRoads?: boolean }) => void;
}

const MAX_LAMBDA = 8;
/** Past this, say the drive stops short of the place (peaks and viewpoints often sit off the road). */
const END_GAP_NOTE_KM = 0.3;

/** The live answer: the same stat row as a recorded drive, from the fields /plan really sends. */
export function LiveResult({ destination, budget, loading, plan, failure, onRetry }: Props) {
  const anchor = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!plan && !failure) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    anchor.current?.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
  }, [plan, failure]);
  return (
    <div ref={anchor} className="live-anchor">
      <LiveBody destination={destination} budget={budget} loading={loading} plan={plan} failure={failure} onRetry={onRetry} />
    </div>
  );
}

/** The answer arrives seconds after the press; bring it into view above the sticky footer. */
function LiveBody({ destination, budget, loading, plan, failure, onRetry }: Props) {
  if (loading) {
    return (
      <section className="hero hero-loading" aria-live="polite" aria-busy="true">
        <span className="eyebrow">Planning…</span>
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-row" />
        <p className="hint">The router compares several scenic weightings. This usually takes a few seconds.</p>
      </section>
    );
  }
  if (failure) return <LiveFailureCard failure={failure} budget={budget} onRetry={onRetry} />;
  if (!plan) return null;
  const extraS = plan.eta_s - plan.fastest_eta_s;
  const hazards = [...new Set(plan.hazards.map((h) => h.value || h.kind))];
  const gapKm = endGapKm(plan.route.coordinates, destination.at);
  return (
    <section className="hero" aria-live="polite" aria-label="Live plan">
      <div className="hero-top">
        <span className="eyebrow eyebrow-scenic">Live plan</span>
        <span className="badge" title="Times come from road speeds, not live traffic">
          <Clock /> estimate · no traffic data
        </span>
      </div>
      <h2 className="hero-title">To {destination.name}</h2>
      {plan.fastest_is_scenic && (
        <p className="hint">The fastest way is already the scenic way, so this drive takes no extra time.</p>
      )}
      <dl className="stats">
        <div>
          <dt>Drive time</dt>
          <dd>{minutes(plan.eta_s)}</dd>
          <span className="stat-sub">{extraS < 60 ? "as fast as it gets" : `+${Math.round(extraS / 60)} min`}</span>
        </div>
        <div>
          <dt>Distance</dt>
          <dd>{miles(plan.route.distance_m)}</dd>
          <span className="stat-sub">fastest {minutes(plan.fastest_eta_s)}</span>
        </div>
        <div>
          <dt>Scenic weight</dt>
          <dd className={plan.lambda >= 4 ? "score-good" : undefined}>{Math.round((plan.lambda / MAX_LAMBDA) * 100)}%</dd>
          <span className="stat-sub">of the planner's max</span>
        </div>
      </dl>
      <p className="hint">
        Within your +{budget} min: at most {minutes(plan.ceiling_s)}. Line colours by scenic score are only on featured drives.
      </p>
      {gapKm > END_GAP_NOTE_KM && (
        <p className="hint">
          The drive ends at the nearest road, {miles(gapKm * 1000)} from {destination.name}.
        </p>
      )}
      {hazards.length > 0 && (
        <p className="honest">
          <span>Heads up on this route: {hazards.join(", ")}.</span>
        </p>
      )}
    </section>
  );
}

function LiveFailureCard({ failure, budget, onRetry }: { failure: LiveFailure; budget: number; onRetry: Props["onRetry"] }) {
  const card = (title: string, body: string, actions: React.ReactNode = null) => (
    <section className="hero" role="status">
      <h2 className="hero-title">{title}</h2>
      <p className="hint">{body}</p>
      {actions && <div className="chips">{actions}</div>}
    </section>
  );
  switch (failure.kind) {
    case "nothing_pretty":
      return card(
        "Nothing pretty fits yet",
        `No route is scenic enough within +${budget} min.`,
        <>
          {failure.moreTimeMinutes !== null && (
            <button type="button" className="button-secondary" onClick={() => onRetry({ budget: failure.moreTimeMinutes! })}>
              Try +{failure.moreTimeMinutes} min
            </button>
          )}
          {failure.backRoadsBudgetMinutes !== null && (
            <button type="button" className="button-secondary"
              onClick={() => onRetry({ budget: failure.backRoadsBudgetMinutes!, allBackRoads: true })}>
              All back roads{failure.backRoadsEtaS !== null ? ` (${minutes(failure.backRoadsEtaS)})` : ""}
            </button>
          )}
        </>,
      );
    case "quota_exhausted": {
      const when = failure.resetsAt ? new Date(failure.resetsAt).toLocaleString([], { weekday: "short", hour: "numeric", minute: "2-digit" }) : null;
      return card("You've used today's live plans", `Free plans reset${when ? ` ${when}` : " tomorrow"}. Featured drives still work.`);
    }
    case "offline":
      return card("The live planner is offline", "The routing server isn't reachable right now. Featured drives still work.");
    case "no_scenic_alternative": {
      const more = Math.min(180, budget + 15);
      return card(
        "No different route fits",
        `Within +${budget} min, the prettiest option mostly follows the fastest way. More time may open one up.`,
        budget < 180 ? (
          <button type="button" className="button-secondary" onClick={() => onRetry({ budget: more })}>
            Try +{more} min
          </button>
        ) : null,
      );
    }
    case "no_route":
      return card(
        "No road reaches it from here",
        "The router found no drivable connection to this place. A nearby trailhead or town usually works.",
      );
    case "unknown_place":
      return card("That place isn't in the planner yet", "Try a nearby place from the list.");
    case "region_unsupported":
      return card("That start is outside Los Angeles", "Live planning covers the LA region for now.");
    default:
      return card("Planning didn't work", `The planner answered: ${failure.detail}.`);
  }
}
