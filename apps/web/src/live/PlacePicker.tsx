import { useEffect, useId, useMemo, useRef, useState } from "react";
import { CLASS_LABEL, kmBetween, searchPlaces, SUGGESTED } from "./places";
import type { LivePlace, Origin } from "./types";

interface Props {
  value: LivePlace | null;
  origin: Origin | null;
  onChange: (place: LivePlace | null) => void;
}

/**
 * Destination search over the 1,334-place corpus, entirely in the browser: no keystroke leaves the device.
 * A select-only-style combobox (ux-principles checklist 9): role=combobox + listbox, arrows, Enter, Escape.
 */
export function PlacePicker({ value, origin, onChange }: Props) {
  const [places, setPlaces] = useState<LivePlace[] | null>(null);
  const [query, setQuery] = useState(value?.name ?? "");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const listId = useId();

  useEffect(() => {
    void import("../data/places.json").then((m) => setPlaces(m.default as unknown as LivePlace[]));
  }, []);
  useEffect(() => setQuery(value?.name ?? ""), [value]);

  const results = useMemo(() => (places && !value ? searchPlaces(places, query) : []), [places, query, value]);
  const expanded = open && results.length > 0;

  const choose = (place: LivePlace) => {
    onChange(place);
    setOpen(false);
  };
  const pickByName = (name: string) => {
    const place = places?.find((p) => p.name === name);
    if (place) choose(place);
  };
  const distance = (p: LivePlace) => (origin ? `${Math.round(kmBetween([origin.lon, origin.lat], p.at) * 0.621)} mi` : "");

  return (
    <div className="section">
      <label className="section-label" htmlFor={`${listId}-input`}>
        Destination
      </label>
      <div className="combo">
        <input
          ref={input}
          id={`${listId}-input`}
          className="combo-input"
          role="combobox"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={expanded ? `${listId}-${active}` : undefined}
          placeholder={places ? `Search ${places.length.toLocaleString()} LA places` : "Loading places…"}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setActive(0);
            setOpen(true);
            if (value) onChange(null);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setOpen(true);
              setActive((i) => Math.min(i + 1, results.length - 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((i) => Math.max(i - 1, 0));
            } else if (e.key === "Enter" && expanded) {
              e.preventDefault();
              choose(results[active]!);
            } else if (e.key === "Escape") {
              setOpen(false);
            }
          }}
        />
        {value && (
          <button type="button" className="combo-clear" aria-label="Clear destination" onClick={() => {
            onChange(null);
            setQuery("");
            input.current?.focus();
          }}>
            ×
          </button>
        )}
        {expanded && (
          <ul id={listId} role="listbox" className="combo-list">
            {results.map((p, i) => (
              <li
                key={p.id}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === active}
                className={i === active ? "combo-option combo-active" : "combo-option"}
                onMouseDown={(e) => e.preventDefault()}
                onMouseEnter={() => setActive(i)}
                onClick={() => choose(p)}
              >
                <span className="combo-name">{p.name}</span>
                <span className="combo-meta">
                  {CLASS_LABEL[p.cls] ?? p.cls} {distance(p) && `· ${distance(p)}`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
      {!value && !query && (
        <div className="chips" aria-label="Suggestions">
          {SUGGESTED.map((name) => (
            <button key={name} type="button" className="chip-button" onClick={() => pickByName(name)}>
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
