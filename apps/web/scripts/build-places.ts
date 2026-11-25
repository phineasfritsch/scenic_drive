/**
 * Builds src/data/places.json: the destination list for live /plan, from the place corpus the app ships
 * (apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite, the same rows the Worker's D1 `places` was seeded from).
 * Place ids are 64-bit, so they stay strings: a JS number would round them and name a different place.
 *
 *     npm run data
 */
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";
import type { LivePlace } from "../src/live/types.ts";

const here = dirname(fileURLToPath(import.meta.url));
const corpus = resolve(here, "../../ios/ScenicDrive/Corpus/corpus-fallback.sqlite");
const db = new DatabaseSync(corpus, { readOnly: true });
db.exec("PRAGMA query_only = 1");
const rows = db
  .prepare("SELECT CAST(place_id AS TEXT) AS id, cls, name, lon_e7, lat_e7 FROM places WHERE name IS NOT NULL ORDER BY name, place_id")
  .all() as { id: string; cls: string; name: string; lon_e7: number; lat_e7: number }[];

const round5 = (e7: number) => Math.round(e7 / 100) / 1e5;
const places: LivePlace[] = rows.map((r) => ({ id: r.id, name: r.name, cls: r.cls, at: [round5(r.lon_e7), round5(r.lat_e7)] }));
writeFileSync(resolve(here, "../src/data/places.json"), `${JSON.stringify(places)}\n`);
console.log(`places: ${places.length}`);
