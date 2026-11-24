import { layers, namedFlavor, type Flavor } from "@protomaps/basemaps";
import type { StyleSpecification } from "maplibre-gl";

/** The LA region's bbox (services/etl/regions/la/region.json), with a margin so the edge is not a wall. */
export const LA_BOUNDS: [[number, number], [number, number]] = [
  [-119.35, 33.5],
  [-117.5, 34.65],
];

/** Glyphs and sprites published by Protomaps for its basemap flavors. */
const ASSETS = "https://protomaps.github.io/basemaps-assets";

/**
 * The tiles: VITE_PMTILES_URL when set (a hosted copy of la.pmtiles), else the copy `npm run dev` puts in
 * public/tiles (scripts/link-tiles.mjs). Never committed: 63 MB, and the root .gitignore refuses *.pmtiles.
 */
export function pmtilesUrl(): string {
  const configured = import.meta.env.VITE_PMTILES_URL as string | undefined;
  return configured && configured.length > 0 ? configured : new URL("/tiles/la.pmtiles", window.location.href).href;
}

export type Appearance = "light" | "dark";

/**
 * Calmer ground than the stock flavors. Almost all of the Santa Monica Mountains is parkland, and the stock
 * saturated park green swallowed the scenic route line. Sage and warm paper keep the map quiet so the route reads.
 */
const OVERRIDES: Record<Appearance, Partial<Flavor>> = {
  light: {
    background: "#f3eee6",
    earth: "#f5f1ea",
    park_a: "#e6ebdc",
    park_b: "#dbe5cf",
    wood_a: "#e4eadb",
    wood_b: "#d8e3cc",
    scrub_a: "#e8ecdf",
    scrub_b: "#dde6d2",
    water: "#b5d9e8",
    beach: "#f1ead6",
    sand: "#efe9dc",
  },
  dark: {
    park_a: "#1b2a27",
    park_b: "#1f302b",
    wood_a: "#1b2a27",
    wood_b: "#1f302b",
    scrub_a: "#1b2826",
    scrub_b: "#1e2d29",
  },
};

/**
 * The Protomaps basemap. `attribution` is left empty on purpose: the app draws its own credit,
 * `© OpenStreetMap contributors · Protomaps`, so it is always visible and never hidden behind a collapsed control.
 */
export function basemapStyle(appearance: Appearance): StyleSpecification {
  return {
    version: 8,
    glyphs: `${ASSETS}/fonts/{fontstack}/{range}.pbf`,
    sprite: `${ASSETS}/sprites/v4/${appearance}`,
    sources: {
      protomaps: { type: "vector", url: `pmtiles://${pmtilesUrl()}` },
    },
    layers: layers("protomaps", { ...namedFlavor(appearance), ...OVERRIDES[appearance] }, { lang: "en" }),
  };
}

export function currentAppearance(): Appearance {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
