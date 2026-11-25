import maplibregl, { type GeoJSONSource, type LngLatBoundsLike, type Map as MlMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";
import { useEffect, useRef } from "react";
import type { ScenicStop } from "../plan/types";
import { MapControls } from "../ui/MapControls";
import { basemapStyle, currentAppearance, LA_BOUNDS, type Appearance } from "./basemap";
import { EMPTY, endpoints, otherRoutes, overlayLayers, selectedRuns, SOURCES, stopsCollection } from "./routeLayers";
import type { MapScene } from "./scene";

maplibregl.addProtocol("pmtiles", new Protocol().tile);

interface Props {
  scene: MapScene;
  stops: ScenicStop[];
  label: string;
  onSelectOther?: (routeId: string) => void;
  /** A click on empty map (not a route or a stop), e.g. to set a live plan's start. */
  onMapClick?: (lon: number, lat: number) => void;
}

const DESKTOP = "(min-width: 900px)";
const INTERACTIVE = ["others-hit", "stops"];

/** Camera moves follow prefers-reduced-motion (ux-principles P20): they jump instead of flying. */
function ms(duration: number): number {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : duration;
}

function boundsOf(points: [number, number][]): LngLatBoundsLike | null {
  if (points.length === 0) return null;
  const b = new maplibregl.LngLatBounds();
  for (const c of points) b.extend(c);
  return b;
}

function padding() {
  return window.matchMedia(DESKTOP).matches
    ? { top: 56, bottom: 56, left: 456, right: 88 }
    : { top: 32, bottom: 64, left: 24, right: 64 };
}

function fit(map: MlMap | null, points: [number, number][], duration: number) {
  const bounds = boundsOf(points);
  if (!map || !bounds) return;
  map.fitBounds(bounds, { padding: padding(), duration: ms(duration), maxZoom: 13 });
}

export function MapView({ scene, stops, label, onSelectOther, onMapClick }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const latest = useRef({ scene, stops, onSelectOther, onMapClick });
  latest.current = { scene, stops, onSelectOther, onMapClick };

  useEffect(() => {
    let appearance: Appearance = currentAppearance();
    const initial = boundsOf(latest.current.scene.fitTo);
    const map = new maplibregl.Map({
      container: container.current!,
      style: basemapStyle(appearance),
      ...(initial ? { bounds: initial, fitBoundsOptions: { padding: padding(), maxZoom: 13 } } : { center: [-118.45, 34.07], zoom: 9 }),
      maxBounds: LA_BOUNDS,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.touchZoomRotate.disableRotation();
    mapRef.current = map;

    map.on("style.load", () => {
      for (const id of SOURCES) if (!map.getSource(id)) map.addSource(id, structuredClone(EMPTY));
      for (const layer of overlayLayers(appearance)) if (!map.getLayer(layer.id)) map.addLayer(layer);
      draw(map, latest.current);
    });

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
      if (typeof id === "string") latest.current.onSelectOther?.(id);
    });
    map.on("click", (e) => {
      const layers = INTERACTIVE.filter((id) => map.getLayer(id));
      if (layers.length > 0 && map.queryRenderedFeatures(e.point, { layers }).length > 0) return;
      latest.current.onMapClick?.(e.lngLat.lng, e.lngLat.lat);
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
  }, [scene, stops]);

  useEffect(() => {
    fit(mapRef.current, latest.current.scene.fitTo, 450);
  }, [scene.fitKey]);

  return (
    <div className="map">
      <div ref={container} className="map-canvas" aria-label={label} role="region" />
      <MapControls
        onZoomIn={() => mapRef.current?.zoomIn({ duration: ms(200) })}
        onZoomOut={() => mapRef.current?.zoomOut({ duration: ms(200) })}
        onFit={() => fit(mapRef.current, scene.fitTo, 350)}
      />
      <p className="attribution">
        © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a>
        {" · "}
        <a href="https://protomaps.com" target="_blank" rel="noreferrer">Protomaps</a>
      </p>
    </div>
  );
}

function draw(map: MlMap, { scene, stops }: { scene: MapScene; stops: ScenicStop[] }) {
  const set = (id: string, data: GeoJSON.FeatureCollection) => (map.getSource(id) as GeoJSONSource | undefined)?.setData(data);
  set("others", otherRoutes(scene.others));
  set("selected", selectedRuns(scene.selected));
  set("endpoints", endpoints(scene.endpoints));
  set("stops", stopsCollection(stops));
}
