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

## Live planning ("Plan any drive")

The second mode calls the deployed Worker's `/plan`.
- **Start:** a preset or a map tap, rounded to 2 decimals.
- **Destination:** chosen from the 1,334-place corpus (`src/data/places.json`, built from
  `apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite`). The search runs in the browser, so no keystroke leaves the device.
- **Budget:** the extra-time slider.

How it fits together:
- **Dev only, through a proxy.** The Worker sends no CORS headers, so `npm run dev` proxies `/api` to it
  (`vite.config.ts`). Set `SCENIC_API_URL` to point the proxy at a `wrangler dev` instead. A plain build has no
  proxy and shows "Live planning runs in dev" unless `VITE_API_BASE` names an API that allows the origin.
- **The router must be up.** It is the WSL docker project `scenic-routing-pilot` behind the Cloudflare Tunnel
  `scenic-router`. The tunnel is started by hand, never automatically (owner, 2026-11-25):
  `cloudflared.exe tunnel --config C:\Users\phineasf\.cloudflared\scenic-router.yml run`.
  Without it the app says "The live planner is offline".
- **Quota.** Each browser gets a random device UUID. The free tier allows 3 plans a day per device, so the app
  plans only when you press "Plan this drive", never on input changes. It never offers to repeat a plan that just
  failed for the same inputs.
- **Privacy.** `planBody()` in `src/live/api.ts` is the only place a request body is built. It rounds the origin to
  2 decimals, and `live.test.ts` holds it there (seen red with the rounding removed).
- **What live answers lack:** live answers have no per-stretch scenic scores, so the route draws in one colour.
  Featured drives keep the scored colouring.

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
