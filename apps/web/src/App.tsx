import { useMemo, useState } from "react";
import demo from "./data/demo.json";
import { googleMapsUrl } from "./format";
import { LiveAction } from "./live/LiveAction";
import { LivePanel } from "./live/LivePanel";
import { mapPointOrigin } from "./live/places";
import { useLivePlanner } from "./live/useLivePlanner";
import { MapView } from "./map/MapView";
import { corridorScene, liveScene } from "./map/scene";
import { budgetForBest, choose } from "./plan/choose";
import type { DemoData } from "./plan/types";
import { BudgetSlider } from "./ui/BudgetSlider";
import { DisclaimerGate, readAccepted } from "./ui/DisclaimerGate";
import { DrivePicker } from "./ui/DrivePicker";
import { ArrowOut, Logo, Shield } from "./ui/Icons";
import { ModeSwitch, type Mode } from "./ui/ModeSwitch";
import { Recommendation } from "./ui/Recommendation";
import { RouteList } from "./ui/RouteList";

const data = demo as unknown as DemoData;
const DEFAULT_BUDGET = 15;

export function App() {
  const [mode, setMode] = useState<Mode>("featured");
  const [corridorId, setCorridorId] = useState(data.corridors[0]!.id);
  const [budget, setBudget] = useState(DEFAULT_BUDGET);
  const [pickedId, setPickedId] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(() => readAccepted());
  const live = useLivePlanner();

  const corridor = data.corridors.find((c) => c.id === corridorId)!;
  const choice = useMemo(() => choose(corridor, budget), [corridor, budget]);
  const picked = choice.options.find((o) => o.route.id === pickedId && o.fitsBudget)?.route;
  const selected = picked ?? choice.recommended;
  const livePlan = live.current?.state === "done" ? live.current.plan : null;

  const changeBudget = (minutes: number) => {
    setBudget(minutes);
    setPickedId(null);
  };

  const scene = useMemo(
    () => (mode === "featured" ? corridorScene(corridor, selected, accepted) : liveScene(live.origin, live.destination, accepted ? livePlan : null)),
    [mode, corridor, selected, accepted, live.origin, live.destination, livePlan],
  );

  return (
    <div className="app">
      <MapView
        scene={scene}
        stops={data.stops}
        label={mode === "featured" ? `Map of ${corridor.title}` : "Map: tap to set the start"}
        onSelectOther={(id) => {
          const option = choice.options.find((o) => o.route.id === id);
          if (option?.fitsBudget) setPickedId(id);
          else if (option) changeBudget(Math.ceil(option.extraS / 60));
        }}
        onMapClick={mode === "live" ? (lon, lat) => live.setOrigin(mapPointOrigin(lon, lat)) : undefined}
      />

      <aside className="panel" aria-label="Plan a drive">
        <header className="brand">
          <Logo />
          <span className="brand-name">Scenic Drive</span>
          <span className="chip">Los Angeles</span>
        </header>

        <div className="intro">
          <h1>Take the long way.</h1>
          <p>The most scenic route that fits the time you can spare.</p>
        </div>

        <ModeSwitch value={mode} onChange={setMode} />

        {mode === "featured" ? (
          <>
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
                <Recommendation corridor={corridor} choice={choice} selected={selected}
                  bestBudget={budgetForBest(corridor)} onBudget={changeBudget} />
                <RouteList corridor={corridor} choice={choice} selectedId={selected.id}
                  onSelect={setPickedId} onBudget={changeBudget} />
              </>
            )}
            <p className="provenance">Featured drives are recorded from the Scenic Drive router ({corridor.provenance}).</p>
          </>
        ) : (
          <>
            <LivePanel live={live} />
            <p className="provenance">
              Live plans come from the Scenic Drive router
              {live.allowance !== null ? `, ${live.allowance} a day per device on the free tier` : ""}.
            </p>
          </>
        )}

        {accepted && (
          <div className="panel-cta">
            <p className="safety">
              <Shield /> Conditions change. Check closures before you go.
            </p>
            {mode === "featured" ? (
              <a className="button-primary" href={googleMapsUrl(selected)} target="_blank" rel="noreferrer">
                Open in Google Maps <ArrowOut />
              </a>
            ) : (
              <LiveAction live={live} />
            )}
          </div>
        )}
      </aside>

      {!accepted && <DisclaimerGate onAccept={() => setAccepted(true)} />}
    </div>
  );
}
