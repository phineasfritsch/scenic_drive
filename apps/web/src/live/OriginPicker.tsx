import { ORIGINS } from "./places";
import type { Origin } from "./types";

interface Props {
  value: Origin | null;
  onChange: (origin: Origin) => void;
}

const same = (a: Origin | null, b: Origin) => a !== null && a.lat === b.lat && a.lon === b.lon;

/** Start: a few presets, or a map click. Either way the server gets one point at 2 decimals (about 1 km). */
export function OriginPicker({ value, onChange }: Props) {
  const fromMap = value !== null && !ORIGINS.some((o) => same(value, o));
  return (
    <div className="section">
      <span className="section-label" id="origin-label">
        Start
      </span>
      <div className="chips" role="radiogroup" aria-labelledby="origin-label">
        {ORIGINS.map((o) => (
          <button
            key={o.name}
            type="button"
            role="radio"
            aria-checked={same(value, o)}
            className={same(value, o) ? "chip-button chip-on" : "chip-button"}
            onClick={() => onChange(o)}
          >
            {o.name}
          </button>
        ))}
        {fromMap && (
          <button type="button" role="radio" aria-checked className="chip-button chip-on">
            {value.name}
          </button>
        )}
      </div>
      <p className="hint">Or tap the map. Your start is sent rounded to about 1 km, and nothing else about where you are.</p>
    </div>
  );
}
