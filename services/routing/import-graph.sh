#!/usr/bin/env bash
# THE import recipe - one command line, two arguments, so a second input never grows a second recipe:
#
#   wsl -e bash -lc "cd /mnt/c/.../scenic_drive/.worktrees/T-0213 && \
#     bash services/routing/import-graph.sh services/etl/work/la/window-tagged-1.osm.pbf services/routing/work/graph-la-window"
#
#   $1  the tagged PBF to import (read-only; it may live in another checkout)
#   $2  the graph directory to build (deleted and rebuilt; keep it under a gitignored work/)
#   $3  the image tag, default scenic-routing:t0213 (the RED demonstration passes its own)
#
# build-slice.sh's Vermont path calls this too, so the lines the LA window exercises are the lines Vermont
# exercises. Nothing here writes into the repository.
set -euo pipefail

INPUT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
GRAPH_PARENT="$(cd "$(dirname "$2")" && pwd)"
GRAPH="$GRAPH_PARENT/$(basename "$2")"
IMAGE="${3:-scenic-routing:t0213}"

echo "== input =="
ls -l "$INPUT"
sha256sum "$INPUT"

echo "== import: $IMAGE -> $GRAPH =="
rm -rf "$GRAPH"
mkdir -p "$GRAPH"
docker run --rm -e JAVA_TOOL_OPTIONS=-Xmx6g \
  -v "$(dirname "$INPUT")":/data:ro -v "$GRAPH":/graph \
  "$IMAGE" --config /app/config.yml --graph /graph --mode import \
  --osm "/data/$(basename "$INPUT")"

echo "== graph =="
ls -l "$GRAPH"
echo "== properties (what /info would report about this graph) =="
cat "$GRAPH/properties"
sha256sum "$GRAPH/properties"
