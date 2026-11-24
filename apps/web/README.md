# Scenic Drive: web demo

The web-first version of Scenic Drive (owner decision, 2026-11-24). You pick a drive and how much extra time you'll
give it, and the app shows the most scenic route whose ETA fits within fastest + budget.

```
cd apps/web
npm install
npm run dev        # http://localhost:5173; copies services/tiles/work/la.pmtiles into public/tiles first
npm test           # planning logic + demo-data checks (vitest)
npm run typecheck
npm run build
npm run data       # rebuild src/data/demo.json from the recorded router answers
```

On Windows, run these from the correctly cased path (`C:\Users\...\GitHub\scenic_drive\apps\web`). From a
lower-cased `c:\users\...` path, vitest loads two copies of itself and fails with "Cannot read properties of
undefined (reading 'config')".

## Where the data comes from

- **Routes**: `Tests/Fixtures/t0239/*`. These are real answers from the scenic router (GraphHopper 11 over the LA
  graph): the fastest route plus alternatives at lambda 0 to 8. `scripts/build-demo-data.ts` decodes and scores them
  with the Worker's own code (`services/api/src/routeScore.ts`, `planWaypoints.ts`, `routePath.ts`), so the demo
  ranks routes the way live `/plan` does. CI rebuilds the file and fails if it has drifted.
- **Scenic stops**: `services/etl/regions/la/curated.yaml`.
- **Basemap**: the Protomaps LA extract `la.pmtiles` (63 MB, never committed), plus Protomaps' public glyphs and
  sprites. For a hosted deploy, upload it somewhere that supports range requests and set `VITE_PMTILES_URL`.

The live router (`scenic-router.phineasfritsch.com`) and search were offline on 2026-11-24. When they're back, a
`PlanSource` that calls `/plan` can replace the recorded data without changing the UI (`src/plan/types.ts` is the
contract).

## Product invariants this app keeps

- The budget is a ceiling. `choose()` never recommends a route over fastest + budget. Picking an over-budget route
  in the list raises the budget instead (`src/plan/choose.test.ts`).
- `© OpenStreetMap contributors · Protomaps` is visible on the map at every width.
- The safety disclaimer gates the first plan, and a safety line stays on the route screen.
- ETAs carry the *estimate · no traffic data* badge.
- Nothing is sent to a server. "Open in Google Maps" is a link the user clicks, carrying the route's decision points.

## Process

This app uses a lightweight process: a branch, small commits, a PR and the `web` CI job. Queue tasks, pins and
mutation floors don't apply here. Keep files under 300 lines and keep secrets out. See the root `CLAUDE.md`.
