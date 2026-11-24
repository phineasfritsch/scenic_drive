import type { Corridor } from "../plan/types";

interface Props {
  corridors: Corridor[];
  value: string;
  onChange: (id: string) => void;
}

/** A radio group of drives (no native select: ux-principles checklist item 9). Few choices, all visible (P14). */
export function DrivePicker({ corridors, value, onChange }: Props) {
  return (
    <fieldset className="section">
      <legend className="section-label">Drive</legend>
      <div className="drive-list" role="radiogroup" aria-label="Drive">
        {corridors.map((c) => {
          const checked = c.id === value;
          return (
            <label key={c.id} className={checked ? "drive drive-checked" : "drive"}>
              <input
                type="radio"
                name="drive"
                value={c.id}
                checked={checked}
                onChange={() => onChange(c.id)}
                className="visually-hidden"
              />
              <span className="drive-text">
                <span className="drive-end">
                  <span className="dot dot-from" aria-hidden />
                  {c.from.name}
                </span>
                <span className="drive-arrow" aria-label="to">→</span>
                <span className="drive-end">
                  <span className="dot dot-to" aria-hidden />
                  {c.to.name}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
