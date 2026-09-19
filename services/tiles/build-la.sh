#!/usr/bin/env bash
# The Greater Los Angeles Protomaps PMTiles extract. Docker lives in WSL on this box, so:
#
#   wsl -e bash -lc "bash /mnt/c/Users/.../scenic_drive/.worktrees/T-0165/services/tiles/build-la.sh"
#
# In order: probe the pinned planet build, cut the region bbox out of it over HTTP range requests (no planet
# download), stamp region/built_at into the archive's own JSON metadata, measure, refuse if over budget, write
# the sidecar, print the header.
#
# Nothing lands in the repository. The default --out is the MAIN checkout's services/tiles/work/, never a
# worktree's: `git worktree remove` deletes a worktree's ignored files with it, and a 64 MB artifact that dies
# with the task's worktree is not an artifact. services/routing/work/ is the precedent.
set -euo pipefail

# The Protomaps daily planet build this recipe is pinned to. build.protomaps.com keeps only the last few days
# (measured 2026-09-19: 20260913 live, 20260912 gone), so this pin EXPIRES - see the refusal below.
PLANET_BUILD=20260915
# go-pmtiles by RepoDigest, never :latest. pmtiles v1.31.2.
#   docker pull protomaps/go-pmtiles:latest
#   docker inspect --format '{{index .RepoDigests 0}}' protomaps/go-pmtiles:latest
PMTILES_IMAGE=protomaps/go-pmtiles@sha256:06574f01f55a78f78f887bc7ebf729a5c093c0d6e17d9876300cfcb0758b59d3
# Ruled by measurement against the 120 MB M2 exit ceiling: z15 would be 197 MB, z14 is 64 MB, z13 is 20 MB.
MAXZOOM=14
# 120 MB as the plan writes it: 120 * 1024 * 1024.
BUDGET_BYTES=125829120
REGION_ID=la

usage() {
  echo "usage: build-la.sh [--out PATH] [--build YYYYMMDD] [--maxzoom N]"
  echo "  --out      output .pmtiles path (default: <main checkout>/services/tiles/work/$REGION_ID.pmtiles)"
  echo "  --build    Protomaps planet build date (default: $PLANET_BUILD)"
  echo "  --maxzoom  max zoom (default: $MAXZOOM; above 14 the LA bbox exceeds the 120 MB budget)"
}

OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --build) PLANET_BUILD="$2"; shift 2 ;;
    --maxzoom) MAXZOOM="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "BUILD REFUSED: unknown argument $1"; usage; exit 2 ;;
  esac
done

TILES="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$TILES/../.." && pwd)"
REGION_JSON="$ROOT/services/etl/regions/$REGION_ID/region.json"

# The main checkout, derived from this script's own path rather than from git: `git rev-parse` is unreliable
# against the Windows worktree from inside WSL, and this substitution needs no tooling at all.
case "$ROOT" in
  */.worktrees/*) MAIN="${ROOT%%/.worktrees/*}" ;;
  *) MAIN="$ROOT" ;;
esac
[ -n "$OUT" ] || OUT="$MAIN/services/tiles/work/$REGION_ID.pmtiles"

[ -f "$REGION_JSON" ] || { echo "BUILD REFUSED: no region file at $REGION_JSON"; exit 1; }

# The bbox is READ from the region file, never typed here: region.json is the one place the bbox is argued.
num() { sed -n "s/.*\"$1\": *\(-\{0,1\}[0-9.]*\).*/\1/p" "$REGION_JSON" | head -1; }
MIN_LON="$(num min_lon)"; MIN_LAT="$(num min_lat)"
MAX_LON="$(num max_lon)"; MAX_LAT="$(num max_lat)"
for v in "$MIN_LON" "$MIN_LAT" "$MAX_LON" "$MAX_LAT"; do
  [ -n "$v" ] || { echo "BUILD REFUSED: could not read the bbox out of $REGION_JSON"; exit 1; }
done
BBOX="$MIN_LON,$MIN_LAT,$MAX_LON,$MAX_LAT"

PLANET_URL="https://build.protomaps.com/$PLANET_BUILD.pmtiles"
WORK="$(dirname "$OUT")"
BASE="$(basename "$OUT")"
mkdir -p "$WORK"

echo "== 0. the pinned planet build =="
code="$(curl -s -o /dev/null -w '%{http_code}' -r 0-0 "$PLANET_URL")"
echo "$PLANET_URL -> HTTP $code"
if [ "$code" != "206" ] && [ "$code" != "200" ]; then
  echo "BUILD REFUSED: planet build $PLANET_BUILD is gone (HTTP $code)."
  echo "  build.protomaps.com keeps only the last few days. Re-pin PLANET_BUILD to a live date, re-run, and"
  echo "  re-measure the bytes - the zoom ladder is a property of the build, not a constant."
  exit 1
fi

BUILT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== 1. extract $BBOX maxzoom=$MAXZOOM =="
docker run --rm -v "$WORK":/w -w /w "$PMTILES_IMAGE" \
  extract "$PLANET_URL" "/w/$BASE" --bbox="$BBOX" --maxzoom="$MAXZOOM"

echo "== 2. region and built_at into the archive's own metadata =="
docker run --rm -v "$WORK":/w "$PMTILES_IMAGE" show --metadata "/w/$BASE" > "$WORK/$BASE.src-meta.json"
python3 "$TILES/tile_meta.py" merge \
  --src-meta "$WORK/$BASE.src-meta.json" --out "$WORK/$BASE.meta.json" \
  --region "$REGION_ID" --bbox="$BBOX" --maxzoom "$MAXZOOM" \
  --build "$PLANET_BUILD" --source-url "$PLANET_URL" --built-at "$BUILT_AT"
docker run --rm -v "$WORK":/w "$PMTILES_IMAGE" edit "/w/$BASE" --metadata="/w/$BASE.meta.json"

echo "== 3. measure =="
BYTES="$(stat -c %s "$OUT")"
echo "BYTES $BYTES $OUT"
echo "BUDGET $BUDGET_BYTES (120 MB)"
if [ "$BYTES" -gt "$BUDGET_BYTES" ]; then
  echo "BUILD REFUSED: $BYTES bytes is over the 120 MB M2 ceiling. Step --maxzoom down and rebuild."
  exit 1
fi

echo "== 4. sidecar =="
python3 "$TILES/tile_meta.py" sidecar \
  --archive "$OUT" --out "$OUT.json" \
  --region "$REGION_ID" --bbox="$BBOX" --maxzoom "$MAXZOOM" \
  --build "$PLANET_BUILD" --source-url "$PLANET_URL" --built-at "$BUILT_AT"
cat "$OUT.json"

echo "== 5. header =="
docker run --rm -v "$WORK":/w "$PMTILES_IMAGE" show "/w/$BASE"

echo "== 6. the check =="
python3 "$TILES/check_pmtiles.py" "$OUT" --region-json "$REGION_JSON"
