import { useMemo, useState } from "react";
import demo from "./data/demo.json";
import { googleMapsUrl } from "./format";
import { MapView } from "./map/MapView";
import { budgetForBest, choose } from "./plan/choose";
import type { DemoData } from "./plan/types";
import { BudgetSlider } from "./ui/BudgetSlider";
import { DisclaimerGate, readAccepted } from "./ui/DisclaimerGate";
import { DrivePicker } from "./ui/DrivePicker";
import { ArrowOut, Logo, Shield } from "./ui/Icons";
import { Recommendation } from "./ui/Recommendation";
import { RouteList } from "./ui/RouteList";

const data = demo as unknown as DemoData;
const DEFAULT_BUDGET = 15;

export function App() {
  const [corridorId, setCorridorId] = useState(data.corridors[0]!.id);
  const [budget, setBudget] = useState(DEFAULT_BUDGET);
  const [pickedId, setPickedId] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(() => readAccepted());

  const corridor = data.corridors.find((c) => c.id === corridorId)!;
  const choice = useMemo(() => choose(corridor, budget), [corridor, budget]);
  const picked = choice.options.find((o) => o.route.id === pickedId && o.fitsBudget)?.route;
  const selected = picked ?? choice.recommended;

  const changeBudget = (minutes: number) => {
    setBudget(minutes);
    setPickedId(null);
  };

  return (
    <div className="app">
      <MapView corridor={corridor} selected={selected} planned={accepted} stops={data.stops} onSelect={(id) => {
        const option = choice.options.find((o) => o.route.id === id);
        if (option?.fitsBudget) setPickedId(id);
        else if (option) changeBudget(Math.ceil(option.extraS / 60));
      }} />

      <aside className="panel" aria-label="Plan a drive">
        <header className="brand">
          <Logo />
          <span className="brand-name">Scenic Drive</span>
          <span className="chip">Demo · Los Angeles</span>
        </header>

        <div className="intro">
          <h1>Take the long way.</h1>
          <p>The most scenic route that fits the time you can spare.</p>
        </div>

        <DrivePicker
          corridors={data.corridors}
          value={corridorId}
          onChange={(id) => {
            setCorridorId(id);
            setPickedId(null);
          }}
        />
        <BudgetSlider value={budget} fastestS={corridor.fastest.timeS} onChange={changeBudget} />

        {accepted && (
          <>
            <Recommendation
              corridor={corridor}
              choice={choice}
              selected={selected}
              bestBudget={budgetForBest(corridor)}
              onBudget={changeBudget}
            />
            <RouteList
              corridor={corridor}
              choice={choice}
              selectedId={selected.id}
              onSelect={setPickedId}
              onBudget={changeBudget}
            />
          </>
        )}

        <p className="provenance">
          Demo data: routes recorded from the Scenic Drive router ({corridor.provenance}). Live planning comes back
          when the router is online again.
        </p>

        {accepted && (
          <div className="panel-cta">
            <p className="safety">
              <Shield /> Conditions change. Check closures before you go.
            </p>
            <a className="button-primary" href={googleMapsUrl(selected)} target="_blank" rel="noreferrer">
              Open in Google Maps <ArrowOut />
            </a>
          </div>
        )}
      </aside>

      {!accepted && <DisclaimerGate onAccept={() => setAccepted(true)} />}
    </div>
  );
}
