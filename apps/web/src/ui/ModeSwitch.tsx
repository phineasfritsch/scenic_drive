export type Mode = "featured" | "live";

const OPTIONS: { id: Mode; label: string }[] = [
  { id: "featured", label: "Featured drives" },
  { id: "live", label: "Plan any drive" },
];

/** Two modes, side by side (a segmented control; radio semantics, no native select). */
export function ModeSwitch({ value, onChange }: { value: Mode; onChange: (mode: Mode) => void }) {
  return (
    <div className="segmented" role="radiogroup" aria-label="Mode">
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          aria-checked={value === o.id}
          className={value === o.id ? "segment segment-on" : "segment"}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
