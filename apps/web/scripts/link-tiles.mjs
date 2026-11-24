// Copies the locally built LA basemap (services/tiles/work/la.pmtiles, never committed) into public/tiles/ so
// `npm run dev` serves it. Without it the map falls back to VITE_PMTILES_URL, or shows no basemap.
import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, "../../../services/tiles/work/la.pmtiles");
const target = resolve(here, "../public/tiles/la.pmtiles");

if (!existsSync(source)) {
  console.warn(`link-tiles: ${source} not found - build it with services/tiles/build-la.sh, or set VITE_PMTILES_URL`);
} else if (existsSync(target) && statSync(target).size === statSync(source).size) {
  console.log("link-tiles: public/tiles/la.pmtiles is current");
} else {
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
  console.log(`link-tiles: copied ${statSync(target).size} bytes to public/tiles/la.pmtiles`);
}
