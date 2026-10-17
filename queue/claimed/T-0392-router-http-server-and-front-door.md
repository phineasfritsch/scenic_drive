---
id: T-0392
title: The router is not servable over HTTP - a GraphHopper web image for the LA graph (with the scenic-score and T-0381 gate plugins) behind a Caddy front door that refuses requests without x-scenic-router-secret
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T07:57:30Z
lease_expires_at: 2026-10-18T07:57:30Z
worktree: .worktrees/T-0392
branch: task/T-0392
exclusive: [routing-profiles]
touches: [services/routing/, ops/deploy-routing, ops/lib/, ops/sane, pins/PINS.yaml]
pins_affected: [P-COST-03, P-PROD-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that services/routing builds only a command-line jar (graphhopper-core; modes import/probe/route/route-details). config.yml has no server: section, and nothing serves /route, /isochrone or /info over HTTP. Nothing checks the Worker's x-scenic-router-secret either: the plan's P-COST-03 says 'VPS refuses requests without the Worker secret'. Until this exists the Worker's /plan answers 503 routingOffline.

Build, following the pattern services/search already uses:
- a GraphHopper web server image pinned by digest that loads the same plugins (scenic-score parser, T-0381 GateFactParser) and serves the LA graph built from the same config.yml and profiles;
- a docker compose service;
- a Caddy front door that returns 401/403 without the secret header, and also 401 for the literal placeholder. The secret comes from the environment and is never committed;
- /info exposing the graph hash (P-PROD-04).

The Worker's routerClient must work against it unchanged: measure the exact paths and headers it sends and match them. Prove locally in WSL docker:
- the LA graph imports;
- a /route through Caddy with the header returns a route;
- the same request without the header is refused;
- /info carries the hash.
Quote each container stage's count lines into the Log as the stage lands.

ops/deploy-routing must deploy this compose to a host given by environment variables. Do not run it against any real host: the owner provides the VPS. Write the owner's exact VPS steps (docker install, firewall to Cloudflare ranges plus owner IP, compose up, secret env) in services/routing/README.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).
- 2026-10-17T07:57:30Z claimed by agent/claude-opus-5; lease until 2026-10-18T07:57:30Z
- 2026-10-17T08:17:38Z MEASURED (before any code).
  * What the Worker sends (services/api/src, unchanged by this task): every request goes through routerDeps.ts
    `routerDepsFromEnv`'s fetchImpl, which sets header `x-scenic-router-secret` (ROUTER_SECRET_HEADER) to
    env.ROUTER_SECRET on every call. ROUTER_URL must be https and not under .invalid (`routerBase`), and `/route`
    or `/isochrone` is appended to it with no path prefix. Two request shapes exist, nothing else:
    (1) `POST ${routerBase}/route`, `content-type: application/json`, body `{points:[[lon,lat],..], profile,
    points_encoded:false, instructions:false, "ch.disable":true, details:["scenic_score","road_class",
    "osm_way_id","surface","road_access","time"], custom_model?}` - scenicPlanner.ts `route`, the same call in
    tripPlanner.ts, loopPlanner.ts and reroutePlanner.ts; profiles `car_fast` / `car_scenic`.
    (2) `GET ${routerBase}/isochrone?point=<lat 2dp>,<lon 2dp>&profile=car_fast&time_limit=<s>&buckets=<n>&reverse_flow=false`
    - isochronePlanner.ts `isochroneUrl`. Nothing in the Worker calls /info.
  * services/routing today: the image builds one shaded jar from graphhopper-core 11.0 whose manifest main is
    ScenicRouterMain (modes import/probe/route/route-details). config.yml has a `graphhopper:` node only, no
    `server:`. No compose file, no Caddyfile. ops/deploy-routing uploads a graph into <root>/releases/<utc>-<sha7>,
    flips <root>/current atomically and runs `sudo systemctl restart scenic-routing` - a unit nothing writes.
  * GraphHopper 11.0 web (graphhopper-web-bundle-11.0-sources.jar, fetched in the pinned maven image):
    GraphHopperManaged's constructor does `new GraphHopper()` + `init(config)` and gives NO hook for an
    ImportRegistry; GraphHopperBundle constructs it itself. GraphHopper.java uses `importRegistry` only in
    `prepareImport()` (lines 862, 902) - i.e. at IMPORT, never in init() or load(). InfoResource.Info has the
    public fields bbox, profiles, version, elevation, encoded_values, import_date, data_date - no hash of any kind.
  * The LA input on this box: services/etl/work/la/la-tagged.osm.pbf in the main checkout, 45,914,107 bytes
    (2026-09-19); the window graph-cache under services/routing/work is 27 MB.
  * services/search (the pattern): Caddy 2.10-alpine pinned by digest, one `@authorized` matcher (secret header
    from {env.SEARCH_SECRET} + method + path whitelist), 401 on the API path otherwise, 404 for everything else,
    no access log, the backend on an `internal: true` network with no published port.
  * P-COST-03 and P-PROD-04 are NOT registered in pins/PINS.yaml (the plan lists both as `ops/sane` live probes);
    P-COST-01's text records P-COST-03's VPS half as "unregistered".
- 2026-10-17T08:17:38Z RULINGS.
  * R1 (plugins in the server): the served graph is IMPORTED by the existing CLI (`--mode import`, our
    ScenicScoreImportRegistry) and only LOADED by the server - GraphHopper's registry is consulted only at import,
    and every encoded value we add is a stock GraphHopper class (IntEncodedValueImpl, SimpleBooleanEncodedValue)
    that load() rebuilds from the graph's properties. The server is still given our registry, so that a server
    that ever imports imports with it: ScenicServerApplication runs GraphHopperBundle and then, before the
    lifecycle starts, finds the bundle's GraphHopperManaged among the managed objects and calls
    setImportRegistry on it - and REFUSES TO START if it does not find exactly one. No upstream class is shadowed.
  * R2 (graph hash, P-PROD-04): the hash is sha256 of the loaded graph's `properties` file - the convention
    import-graph.sh already prints as "what /info would report about this graph"; it moves with every import
    (import date, data date, encoded values, profile hashes). /info carries it as the JSON field `graph_hash`,
    added by a response filter to GraphHopper's own Info (every upstream field kept).
  * R3 (front door): Caddy, the search pattern. Whitelist exactly POST /route, GET /isochrone, GET /info with the
    header equal to {env.ROUTER_SECRET}; the header is stripped before the proxy. The literal placeholder the
    README shows (REPLACE_WITH_THE_WORKER_ROUTER_SECRET) is refused 401 even when the box was started with it.
    Any other request to a whitelisted path is 401; every other path is 404. No access log. GraphHopper publishes
    no port. Site address from env ROUTER_SITE (default `:8080` = plain HTTP for the local proof; the owner sets
    the hostname and Caddy terminates TLS).
  * R4 (config.yml is serial-only): this task declared `exclusive: [routing-profiles]`; the server reads the SAME
    config.yml - a `server:` section is added (application connector 8989, admin on 127.0.0.1 only, request log
    off). ScenicRouterMain reads only the `graphhopper:` node, so the CLI is unaffected. Profiles untouched.
  * R5 (deploy): ops/deploy-routing keeps its refusals, release dirs, atomic flip and prune; each release now
    also carries the compose bundle (compose.yaml, Caddyfile, Dockerfile, config.yml, profiles, plugins) and the
    default restart is `docker compose up -d --build` in <root>/current with the box-local secret file
    <root>/router.secret.env (owner-created, never in the tree). The rehearsal driver is extended accordingly.
  * R6 (pins): P-COST-03's source half is registered as a pin over a static checker
    ops/lib/check-routing-front-door.py (whitelist of matchers/paths, secret from env only, placeholder refusal,
    images by digest, no published GraphHopper port) with --prove-red; pins/PINS.yaml is added to touches for
    that. The LIVE halves (P-COST-03 direct probe 401, P-PROD-04 /info == config == goldens) are ops/sane probes
    of a host that does not exist yet: NOT done here (ops/sane's exit-order pin and prod fake are a task of their
    own); recorded as still open.
  * R7: Brief says "401/403"; this box answers 401 (search's choice). The Worker treats any non-2xx as
    router_refused, so the code does not matter to it.
- 2026-10-17T08:17:38Z ACCEPTANCE (all run on the final merged head; WSL docker for A1-A3).
  * A1 `docker build -t scenic-routing:t0392 services/routing` exits 0 (maven runs the plugin tests).
  * A2 import-graph.sh <main>/services/etl/work/la/la-tagged.osm.pbf services/routing/work/graph-la scenic-routing:t0392
    prints `SCENIC_EV present=true` and a `GRAPH nodes=N edges=M` line with N, M > 0 (quoted).
  * A3 `bash services/routing/tests/front_door_e2e.sh services/routing/work/graph-la` prints `PASS <name>` for every
    check and `E2E 10/10`: route_fast_with_secret, route_scenic_custom_model_with_secret,
    isochrone_with_secret, info_graph_hash_equals_properties_sha256, route_without_secret_401,
    route_wrong_secret_401, info_without_secret_401, unlisted_path_404, graphhopper_port_unpublished,
    placeholder_secret_401_when_box_started_with_it.
  * A4 `python ops/lib/check-routing-front-door.py` exits 0; `--prove-red` exits 0 (every mutant refused).
  * A5 services/routing/tests/test_deploy_routing_rehearsal.py passes (via WSL), including the release carrying
    compose.yaml and the compose restart.
  * A6 `ops/check-pins` row P-COST-03 green; check-pins-yaml green.
  * A7 bare gates: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-pins-yaml,
    check-exec-bits, queue-check.
  * A8 `git grep -nI` over the diff finds no secret value; ROUTER_SECRET appears only as an env reference.
- 2026-10-17T08:24:59Z RED: `python ops/lib/check-routing-front-door.py` before the Caddyfile/compose existed:
  `ROUTING FRONT DOOR UNREADABLE: [Errno 2] No such file or directory: ...services\routing\Caddyfile` exit=2.
  With the files: `ROUTING FRONT DOOR OK: 3 proxied calls, all behind the secret` exit 0; `--prove-red`:
  REFUSED placeholder refusal dropped / route opened to GET / secret header line dropped / catch-all proxies /
  secret forwarded upstream / access log on / graphhopper port published / secret literal in compose / caddy by
  tag only - `PROVE-RED OK: 9/9 mutants refused` exit 0.
- 2026-10-17T08:32:54Z STAGE A1 (WSL docker): `docker build -t scenic-routing:t0392 services/routing` exit=0;
  maven in the builder: `Tests run: 32, Failures: 0, Errors: 0, Skipped: 0`.
- 2026-10-17T08:32:54Z STAGE A2: import-graph.sh of la-tagged.osm.pbf (45914107 bytes, sha256
  648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39): `Finished reading OSM file: nodes: 951,816,
  edges: 1,194,924, zero distance edges: 70,743`; `SCENIC_EV present=true bits=4 max=10`;
  `GRAPH nodes=951816 edges=1194924`; graph-la 79M on disk. The CLI now logs through logback (stderr, INFO).
- 2026-10-17T08:44:32Z STAGE A3 GREEN (WSL docker, compose up --build against graph-la, throwaway secret):
  `route distance=17935 m time=1162 s points=548` PASS route_fast_with_secret; PASS
  route_scenic_custom_model_with_secret (same 17935 m path - the check proves the custom model is accepted and
  answered, NOT that it moves the route); `isochrone polygons=1` PASS isochrone_with_secret; `info
  graph_hash=64d2c75e...9863f0 properties_sha256=64d2c75e...9863f0 profiles=['car_fast', 'car_scenic']` PASS
  info_graph_hash_equals_properties_sha256; `POST /route -> 401` PASS route_without_secret_401; `POST /route ->
  401` PASS route_wrong_secret_401; `GET /info -> 401` PASS info_without_secret_401; `GET /maps/ -> 404` PASS
  unlisted_path_404; PASS graphhopper_port_unpublished; `POST /route -> 401` PASS
  placeholder_secret_401_when_box_started_with_it; `E2E 10/10` exit=0. (A first run printed `E2E 9/10`:
  graphhopper_port_unpublished FAILED because the driver's `compose ps` lacked ROUTER_SECRET - a driver bug, fixed.)
- 2026-10-17T08:44:32Z RED BY NAME, e2e: Caddyfile with its three `not header ... REPLACE_WITH_THE_WORKER_ROUTER_SECRET`
  lines removed -> `FAIL placeholder_secret_401_when_box_started_with_it`, `E2E 9/10` exit=1; restored.
- 2026-10-17T08:47:21Z RED BY NAME, e2e: ScenicServerApplication with the GraphHashInfoFilter registration disabled
  (`if (false)`) -> `info graph_hash=None` `FAIL info_graph_hash_equals_properties_sha256`, `E2E 9/10` exit=1; restored.
