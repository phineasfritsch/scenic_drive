import { extra, miles, minutes, scenicScore, via } from "../format";
import type { Choice } from "../plan/choose";
import type { Corridor } from "../plan/types";
import { ScenicStrip } from "./ScenicStrip";

interface Props {
  corridor: Corridor;
  choice: Choice;
  selectedId: string;
  onSelect: (id: string) => void;
  onBudget: (minutes: number) => void;
}

/**
 * Every route the planner found. One that is over budget is never offered as a pick: choosing it raises the
 * budget to fit, so the screen keeps the ceiling true (returned ETA <= fastest + budget).
 */
export function RouteList({ corridor, choice, selectedId, onSelect, onBudget }: Props) {
  const all = choice.options.map((o) => o.route);
  return (
    <section className="section">
      <h3 className="section-label">All routes</h3>
      <ul className="routes">
        {choice.options.map(({ route, extraS, fitsBudget, recommended }) => {
          const selected = route.id === selectedId;
          const needed = Math.ceil(extraS / 60);
          const className = ["route", selected && "route-selected", !fitsBudget && "route-over"].filter(Boolean).join(" ");
          return (
            <li key={route.id}>
              <button
                type="button"
                className={className}
                aria-pressed={selected}
                onClick={() => (fitsBudget ? onSelect(route.id) : onBudget(needed))}
              >
                <span className="route-main">
                  <span className="route-time">{route.kind === "fastest" ? minutes(route.timeS) : extra(extraS)}</span>
                  <span className="route-via">
                    {route.kind === "fastest" ? "Fastest route" : via(route, corridor.fastest, all)}
                  </span>
                </span>
                <span className="route-meta">
                  <span>{miles(route.distanceM)}</span>
                  <span className="route-score">{scenicScore(route.score.value)}</span>
                </span>
                <ScenicStrip route={route} compact />
                {recommended && <span className="route-flag">Recommended</span>}
                {!fitsBudget && <span className="route-flag route-flag-over">Needs {needed} min extra</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
