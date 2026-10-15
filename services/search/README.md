# services/search - Photon address search (T-0359)

Typed address search for the plan sheet: the Worker's `POST /search` (services/api/src/search.ts) forwards the typed
text, at most one 2-decimal bias coordinate and a fixed California bbox to this box, and reads Photon's answer
fail-closed. This directory is everything but the deploy, which is the owner's.

## What is pinned (measured 2026-10-10, T-0359 Log)

| Piece | Pin |
|---|---|
| Photon | 1.3.0 jar, `ADD --checksum=sha256:a89707c0...` (the digest GitHub publishes for the release asset) |
| JRE | `eclipse-temurin:21-jre@sha256:cff19e62...` (Photon 1.3.0 requires Java 21+) |
| Front door | `caddy:2.10-alpine@sha256:4c6e91c6...` |
| Data | `photon-db-usa-1.0-latest.tar.bz2` from download1.graphhopper.com - 10,501,884,940 bytes on 2026-10-06, md5 published beside it |

`python ops/lib/check-search-pins.py` refuses a tag-only image or a jar without its checksum.

There is no California extract: the US db is served and California is enforced at query time by the Worker's
`CALIFORNIA` bbox (services/api/src/searchRequest.ts) - one value, in one place.

## The API the Worker uses (docs/api-v1.md at tag 1.3.0)

`GET /api?q=<text>&limit=8&lang=en&bbox=-124.48,32.53,-114.13,42.01[&lat=<2dp>&lon=<2dp>]`, answered as GeoJSON
features with `geometry.coordinates = [lon, lat]` and `properties` {name, housenumber, street, city, state, ...}.

## Owner deploy steps

1. On the search VPS (SSD, about 4x the compressed db free for the unpack and a later atomic swap), in a checkout of
   this directory:

   ```
   mkdir -p data && cd data
   wget https://download1.graphhopper.com/public/north-america/usa/photon-db-usa-1.0-latest.tar.bz2
   wget https://download1.graphhopper.com/public/north-america/usa/photon-db-usa-1.0-latest.tar.bz2.md5
   md5sum -c photon-db-usa-1.0-latest.tar.bz2.md5
   pbzip2 -cd photon-db-usa-1.0-latest.tar.bz2 | tar x     # leaves data/photon_data/
   rm photon-db-usa-1.0-latest.tar.bz2 && cd ..
   ```

   Record the md5 you verified in the deploy note. Never unpack over a live `photon_data` (Photon's README): unpack
   beside it, swap the directories, restart.
2. Pick a long random secret and start the box with it in the environment only:
   `SEARCH_SECRET=<secret> docker compose up -d --build`. Caddy listens on 127.0.0.1:8080; Photon publishes nothing.
3. Expose 127.0.0.1:8080 over HTTPS (the owner's tunnel or reverse proxy - the same way the router is exposed).
4. Check: `curl -H "x-scenic-search-secret: <secret>" "https://<host>/api?q=Topanga&limit=1"` returns a feature;
   without the header it is 401.
5. Bind the Worker: `wrangler secret put SEARCH_SECRET` (same value) and set `SEARCH_URL=https://<host>` in the
   Worker's vars. Until both are set, `/search` answers 503 `search_unavailable` and calls nothing.
6. Kill switch: the Worker's `KILL=1` (or the KV `KILL_SWITCH` key) pauses `/search` with the planning routes.

Nothing here holds a secret. The Caddyfile writes no access log, so typed queries are not kept on the box.
