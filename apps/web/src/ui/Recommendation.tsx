import { extra, miles, minutes, scenicScore, via } from "../format";
import type { Choice } from "../plan/choose";
import type { Corridor, RouteOption } from "../plan/types";
import { Clock, Sparkle } from "./Icons";
import { ScenicStrip, StripLegend } from "./ScenicStrip";

interface Props {
  corridor: Corridor;
  choice: Choice;
  selected: RouteOption;
  bestBudget: number;
  onBudget: (minutes: number) => void;
}

/** The hero card: Strava's stat row (big number, small label), one primary action (P15). */
export function Recommendation({ corridor, choice, selected, bestBudget, onBudget }: Props) {
  const isRecommended = selected.id === choice.recommended.id;
  const isFastest = selected.kind === "fastest";
  const eyebrow = isRecommended ? (isFastest ? "Your best bet" : "Most scenic that fits") : "You picked";
  return (
    <section className="hero" aria-live="polite" aria-label="Selected route">
      <div className="hero-top">
        <span className={isFastest ? "eyebrow" : "eyebrow eyebrow-scenic"}>
          {!isFastest && <Sparkle />} {eyebrow}
        </span>
        <span className="badge" title="Times come from road speeds, not live traffic">
          <Clock /> estimate · no traffic data
        </span>
      </div>
      <h2 className="hero-title">{isFastest ? "The fastest way" : `Via ${via(selected, corridor.fastest)}`}</h2>

      <dl className="stats">
        <div>
          <dt>Drive time</dt>
          <dd>{minutes(selected.timeS)}</dd>
          <span className="stat-sub">{extra(selected.timeS - corridor.fastest.timeS)}</span>
        </div>
        <div>
          <dt>Distance</dt>
          <dd>{miles(selected.distanceM)}</dd>
          <span className="stat-sub">{selected.kind === "fastest" ? "shortest" : `+${miles(selected.distanceM - corridor.fastest.distanceM)}`}</span>
        </div>
        <div>
          <dt>Scenic score</dt>
          <dd className={selected.score.value >= 0.45 ? "score-good" : undefined}>{scenicScore(selected.score.value)}</dd>
          <span className="stat-sub">fastest {scenicScore(corridor.fastest.score.value)}</span>
        </div>
      </dl>

      <ScenicStrip route={selected} />
      <StripLegend />

      {choice.honestFailure && isRecommended && (
        <div className="honest">
          <p>
            {bestBudget > 0
              ? `Nothing prettier fits in your budget. Give it ${bestBudget} minutes and the mountain roads open up.`
              : "Nothing on this drive is prettier than the fastest way."}
          </p>
          {bestBudget > 0 && (
            <button type="button" className="button-secondary" onClick={() => onBudget(bestBudget)}>
              Use +{bestBudget} min
            </button>
          )}
        </div>
      )}
    </section>
  );
}
