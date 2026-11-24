import maplibregl, { type GeoJSONSource, type LngLatBoundsLike, type Map as MlMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import { useEffect, useRef } from "react";
import type { Corridor, RouteOption, ScenicStop } from "../plan/types";
import { MapControls } from "../ui/MapControls";
import { basemapStyle, currentAppearance, LA_BOUNDS, type Appearance } from "./basemap";
import { EMPTY, endpoints, otherRoutes, overlayLayers, selectedRuns, SOURCES, stopsCollection } from "./routeLayers";

maplibregl.addProtocol("pmtiles", new Protocol().tile);

interface Props {
  corridor: Corridor;
  selected: RouteOption;
  /** False until the safety disclaimer is accepted: the gate comes before the first plan, on the map too. */
  planned: boolean;
  stops: ScenicStop[];
  onSelect: (routeId: string) => void;
}

const DESKTOP = "(min-width: 900px)";

/** Camera moves follow prefers-reduced-motion (ux-principles P20): they jump instead of flying. */
function ms(duration: number): number {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : duration;
}

function boundsOf(corridor: Corridor): LngLatBoundsLike {
  const b = new maplibregl.LngLatBounds();
  for (const r of [corridor.fastest, ...corridor.alternatives]) for (const c of r.coordinates) b.extend(c);
  return b;
}

function padding() {
  return window.matchMedia(DESKTOP).matches
    ? { top: 56, bottom: 56, left: 456, right: 88 }
    : { top: 32, bottom: 64, left: 24, right: 64 };
}

export function MapView({ corridor, selected, planned, stops, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const latest = useRef({ corridor, selected, planned, stops, onSelect });
  latest.current = { corridor, selected, planned, stops, onSelect };

  useEffect(() => {
    let appearance: Appearance = currentAppearance();
    const map = new maplibregl.Map({
      container: container.current!,
      style: basemapStyle(appearance),
      bounds: boundsOf(latest.current.corridor),
      fitBoundsOptions: { padding: padding() },
      maxBounds: LA_BOUNDS,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.touchZoomRotate.disableRotation();
    mapRef.current = map;

    const install = () => {
      for (const id of SOURCES) if (!map.getSource(id)) map.addSource(id, structuredClone(EMPTY));
      for (const layer of overlayLayers(appearance)) if (!map.getLayer(layer.id)) map.addLayer(layer);
      draw(map, latest.current);
    };
    map.on("style.load", install);

    const popup = new maplibregl.Popup({ closeButton: false, offset: 12, className: "stop-popup", maxWidth: "260px" });
    const showStop = (e: maplibregl.MapLayerMouseEvent) => {
      const f = e.features?.[0];
      if (!f || f.geometry.type !== "Point") return;
      const { name, hook } = f.properties as { name: string; hook: string };
      const content = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = name;
      const body = document.createElement("p");
      body.textContent = hook;
      content.append(title, body);
      popup.setLngLat(f.geometry.coordinates as [number, number]).setDOMContent(content).addTo(map);
    };
    map.on("mouseenter", "stops", (e) => {
      map.getCanvas().style.cursor = "pointer";
      showStop(e);
    });
    map.on("click", "stops", showStop);
    map.on("mouseleave", "stops", () => {
      map.getCanvas().style.cursor = "";
      popup.remove();
    });
    map.on("mouseenter", "others-hit", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "others-hit", () => (map.getCanvas().style.cursor = ""));
    map.on("click", "others-hit", (e) => {
      const id = e.features?.[0]?.properties?.id;
      if (typeof id === "string") latest.current.onSelect(id);
    });

    const scheme = window.matchMedia("(prefers-color-scheme: dark)");
    const onScheme = () => {
      appearance = currentAppearance();
      map.setStyle(basemapStyle(appearance));
    };
    scheme.addEventListener("change", onScheme);
    return () => {
      scheme.removeEventListener("change", onScheme);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (map?.isStyleLoaded()) draw(map, latest.current);
  }, [corridor, selected, planned, stops]);

  useEffect(() => {
    mapRef.current?.fitBounds(boundsOf(corridor), { padding: padding(), duration: ms(450) });
  }, [corridor]);

  return (
    <div className="map">
      <div ref={container} className="map-canvas" aria-label={`Map of ${corridor.title}`} role="region" />
      <MapControls
        onZoomIn={() => mapRef.current?.zoomIn({ duration: ms(200) })}
        onZoomOut={() => mapRef.current?.zoomOut({ duration: ms(200) })}
        onFit={() => mapRef.current?.fitBounds(boundsOf(corridor), { padding: padding(), duration: ms(350) })}
      />
      <p className="attribution">
        © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a>
        {" · "}
        <a href="https://protomaps.com" target="_blank" rel="noreferrer">Protomaps</a>
      </p>
    </div>
  );
}

interface DrawState {
  corridor: Corridor;
  selected: RouteOption;
  planned: boolean;
  stops: ScenicStop[];
}

function draw(map: MlMap, { corridor, selected, planned, stops }: DrawState) {
  const set = (id: string, data: GeoJSON.FeatureCollection) => (map.getSource(id) as GeoJSONSource | undefined)?.setData(data);
  const none: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
  set("others", planned ? otherRoutes(corridor, selected.id) : none);
  set("selected", planned ? selectedRuns(selected) : none);
  set("endpoints", endpoints(corridor));
  set("stops", stopsCollection(stops));
}
