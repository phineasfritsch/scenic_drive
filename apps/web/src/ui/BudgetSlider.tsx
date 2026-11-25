import type { CSSProperties } from "react";
import { minutes } from "../format";
import { MAX_BUDGET_MINUTES } from "../plan/choose";

interface Props {
  value: number;
  /** Known for recorded drives; for a live plan it arrives with the answer. */
  fastestS?: number;
  onChange: (minutes: number) => void;
}

/** The extra-time budget. It is a ceiling, and the copy says so: "at most", never "about". */
export function BudgetSlider({ value, fastestS, onChange }: Props) {
  const fill = { "--fill": `${(value / MAX_BUDGET_MINUTES) * 100}%` } as CSSProperties;
  return (
    <div className="section">
      <div className="budget-head">
        <label htmlFor="budget" className="section-label">
          Extra time I'll give it
        </label>
        <output htmlFor="budget" className="budget-value">
          {value === 0 ? "None" : `+${value} min`}
        </output>
      </div>
      <input
        id="budget"
        type="range"
        min={0}
        max={MAX_BUDGET_MINUTES}
        step={1}
        value={value}
        style={fill}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={fastestS === undefined ? `${value} extra minutes at most`
          : `${value} extra minutes, at most ${minutes(fastestS + value * 60)} in total`}
        className="budget"
      />
      <div className="budget-scale" aria-hidden>
        <span>0</span>
        <span>10</span>
        <span>20</span>
        <span>30 min</span>
      </div>
      <p className="hint">
        {fastestS === undefined
          ? `The drive will take at most the fastest time plus ${value} min.`
          : `At most ${minutes(fastestS + value * 60)} door to door. The fastest way is ${minutes(fastestS)}.`}
      </p>
    </div>
  );
}
