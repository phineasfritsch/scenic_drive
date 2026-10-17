# services/routing — GraphHopper with `scenic_score`

First slice of T-0031. What is here proves one property over one real extract: `scenic_score` survives the
import as a GraphHopper encoded value, and a per-request custom model referencing it moves the route in a
direction the budget search can bisect on.

    wsl -e bash -lc "cd /mnt/c/.../scenic_drive/.worktrees/T-0031 && bash services/routing/build-slice.sh"
    cd services/routing && python -m pytest tests -rs -s

`build-slice.sh` tags the manifest-pinned Vermont extract, builds both images and imports the graph into
`work/graph-cache/`. The pytest skips with a reason when that graph or the image is missing, so it is safe
on a box without docker. Everything it writes lands in `work/`, which is ignored.

T-0213 added the second, REAL input and the one import recipe both paths use:

    bash services/routing/import-graph.sh <tagged.osm.pbf> <graph-dir> [image]
    docker run ... scenic-routing:t0213 --config /app/config.yml --graph /graph --mode probe --probe-ways 74344132

`--mode probe` walks the built graph and prints `PROBE way=<osm way id> edges=<n> scenic_score=<v>`, which is
how `tests/test_scenic_score_readback.py` checks a NAMED way's real score instead of a snapped coordinate's.
It needs `osm_way_id` in `config.yml`'s `graph.encoded_values`, which is why it is there.

T-0209 added `--mode route-details` (image `scenic-routing:t0209`, same config, so the graph format is
unchanged): route's arguments, and after each `ROUTE` line one `EDGE model= seq= road_class= osm_way_id=
distance_m=` row per routed edge, from GraphHopper's own path details. `tools/route_details.py` reads it;
`tools/route_la_pairs.py` measures T(lambda) and the residential/service runs over the LA graph with it. An
unknown `--mode` is now an error instead of a silent exit 0.

**The image tag moves with `config.yml`.** A graph carries the encoded-value list it was built with, so an
image whose config names a different list cannot load it: `scenic-routing:t0031` is the T-0031 config and the
Vermont graph built under it, `scenic-routing:t0213` adds `osm_way_id`. Changing `graph.encoded_values` means
re-importing every graph and bumping the tag - never reusing one.

`ops/deploy-routing <graph-dir>` ships a built graph AND this directory as committed at HEAD (compose.yaml,
Caddyfile, Dockerfile, config.yml, profiles, plugins) to the routing box: new release dir, atomic symlink flip,
`docker compose up -d --build` in `<root>/current`, the 2 newest releases kept. It refuses without
`SCENIC_ROUTING_HOST`, `SCENIC_ROUTING_USER`, `SCENIC_ROUTING_KEY`, `SCENIC_ROUTING_ROOT`, unless HEAD is on
origin and carries `services/routing/compose.yaml`, and when the box has no non-empty `<root>/router.secret.env`.
`SCENIC_ROUTING_REHEARSE=<dir>` runs the same code against a local directory - no ssh, no rsync, no box.

## What is real and what is a stand-in

| Piece | Status |
|---|---|
| `plugins/scenic-score-parser` | Real. `scenic_score`, unsigned, 4 bits, 0..10; no tag means 0. |
| `profiles/car_scenic_base.json` | Real. Safety gates only: private/no access, the unpaved surfaces, track. Motorway and trunk are **not** gated — they carry score 0 and are penalized by the request model. |
| `config.yml` | Real, and read by the runner AND the served router, so the profile under test is the profile that ships. Its `server:` section (T-0392) is read only by `ScenicServerApplication`. |
| per-request models | Not a profile. `services/api/src/customModel.ts` builds the body per request; its output at the oracle lambdas is RECORDED in `Tests/Fixtures/custom-model/lambda-<l>.json`, held byte-equal to the builder by `services/api/test/customModelGolden.test.ts`, and `tests/request_models.py` routes those bytes unchanged (T-0190: the old template + band table had drifted to 3 clauses against the Worker's 9). |
| `tools/synthetic_scenic_tags.py` | **SYNTHETIC.** `way_id % 11` on every highway way, stamped into the output PBF's header. Not a scenic index. T-0168 owns the real writer. |
| Serving (T-0392) | Real: `ScenicServerApplication` (GraphHopper 11.0's web bundle over the imported graph) behind the Caddy front door, proven end to end over the LA graph by `tests/front_door_e2e.sh`. Not yet on any host. |

## The served router (T-0392)

    compose.yaml   graphhopper (this Dockerfile, `ScenicServerApplication server /app/config.yml`, no published
                   port, internal network only) + front (Caddy 2.10 by digest, ports 80/443)
    Caddyfile      exactly POST /route, GET /isochrone, GET /info - the three calls services/api makes - and only
                   with `x-scenic-router-secret` equal to ROUTER_SECRET (stripped before the proxy). Any other
                   request to those paths is 401, every other path 404, no access log. The placeholder below is
                   refused even if the box was started with it.

The graph is IMPORTED by the CLI (`import-graph.sh`, our ImportRegistry) and only LOADED by the server. `/info`
is GraphHopper's own answer plus `graph_hash`: the sha256 of the served graph's `properties` file, which
`import-graph.sh` prints at import - compare the two after every deploy (P-PROD-04). The server also gets our
ImportRegistry, and refuses to start when the graph has no `properties`.

Local proof (WSL docker; a throwaway secret; tears down after):

    bash services/routing/import-graph.sh <main>/services/etl/work/la/la-tagged.osm.pbf services/routing/work/graph-la scenic-routing:t0392
    bash services/routing/tests/front_door_e2e.sh services/routing/work/graph-la      # E2E 10/10
    python ops/lib/check-routing-front-door.py [--prove-red]                          # the static whitelist

### The owner's VPS steps

Nothing here has been run against a real host. On a fresh Ubuntu 24.04 box with >= 4 GB RAM:

1. **Docker.** `curl -fsSL https://get.docker.com | sudo sh`, then `sudo usermod -aG docker <deploy user>` and
   log in again. `docker compose version` must print v2. Also `sudo apt-get install -y rsync`.
2. **Firewall** (ufw): `sudo ufw default deny incoming`, `sudo ufw allow from <your IP> to any port 22 proto tcp`,
   and for every range in https://www.cloudflare.com/ips-v4 (and ips-v6):
   `sudo ufw allow from <range> to any port 80,443 proto tcp`; also allow 80/443 from your IP for a direct probe.
   `sudo ufw enable`. Docker publishes ports past ufw's INPUT chain, so ALSO restrict them in DOCKER-USER, e.g.
   `sudo iptables -I DOCKER-USER -p tcp -m multiport --dports 80,443 -j DROP` preceded by one
   `-I DOCKER-USER -s <range> -p tcp -m multiport --dports 80,443 -j RETURN` per Cloudflare range and your IP
   (persist with iptables-persistent). The front door refuses without the secret either way; the firewall makes a
   direct probe from anywhere else time out.
3. **Root and secret.** `mkdir -p /srv/scenic-routing` (owned by the deploy user). Generate the secret ONCE,
   locally: `openssl rand -hex 32` (hex only - Caddy's header matcher treats `*` specially). Put it in the Worker
   with `wrangler secret put ROUTER_SECRET`, and on the box in `/srv/scenic-routing/router.secret.env`, mode 600,
   one line `ROUTER_SECRET=<that value>` - never the placeholder `REPLACE_WITH_THE_WORKER_ROUTER_SECRET`, which
   the front door refuses. If Cloudflare proxies the hostname, add a second line `ROUTER_SITE=<router hostname>`
   so Caddy obtains a certificate for it (Cloudflare SSL mode Full (strict)). This file never enters the tree.
4. **Graph.** Import on a workstation with `import-graph.sh` (above); note the `properties` sha256 it prints.
5. **Deploy and compose up**, from the workstation, with HEAD pushed:
   `SCENIC_ROUTING_HOST=<ip> SCENIC_ROUTING_USER=<deploy user> SCENIC_ROUTING_KEY=~/.ssh/<key>
   SCENIC_ROUTING_ROOT=/srv/scenic-routing ops/deploy-routing services/routing/work/graph-la`.
   It uploads the release, flips `current`, and runs
   `cd /srv/scenic-routing/current && docker compose -p scenic-routing --env-file /srv/scenic-routing/router.secret.env up -d --build --remove-orphans`.
6. **Check.** `curl -s -H "x-scenic-router-secret: <secret>" https://<router hostname>/info` shows `graph_hash` equal
   to step 4's sha256; the same request without the header answers 401. Then set the Worker's `ROUTER_URL` to
   `https://<router hostname>` and `GRAPH_VERSION` to that hash.
