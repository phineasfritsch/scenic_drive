import { Fit, Minus, Plus } from "./Icons";

interface Props {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFit: () => void;
}

/** Round floating controls, top right (Airbnb's map pattern): 44 px targets (P12). */
export function MapControls({ onZoomIn, onZoomOut, onFit }: Props) {
  return (
    <div className="map-controls">
      <div className="control-stack">
        <button type="button" className="control" onClick={onZoomIn} aria-label="Zoom in">
          <Plus />
        </button>
        <span className="control-divider" />
        <button type="button" className="control" onClick={onZoomOut} aria-label="Zoom out">
          <Minus />
        </button>
      </div>
      <button type="button" className="control control-single" onClick={onFit} aria-label="Show the whole drive">
        <Fit />
      </button>
    </div>
  );
}
