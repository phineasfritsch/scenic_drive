#!/usr/bin/env bash
# Build everything services/routing/tests needs, inside WSL, where docker is:
#
#   wsl -e bash -lc "cd /mnt/c/.../scenic_drive/.worktrees/T-0031 && bash services/routing/build-slice.sh"
#
# 1. the SYNTHETIC scenic_score tagger image, and the tagged Vermont PBF it writes
# 2. the router image (GraphHopper 11.0 + our scenic_score encoded value)
# 3. the graph import, whose way and edge counts are the evidence that the tag survived
#
# Nothing here writes into the repository: every output lands in services/routing/work/, which is ignored.
set -euo pipefail

ROUTING="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$ROUTING/../.." && pwd)"
WORK="$ROUTING/work"

# The manifest-pinned Vermont extract, 45,880,330 bytes, fetched by T-0025 and read where it lies: it is an
# ETL input, not an artifact of this task, and copying it into another worktree would be a second copy to
# keep honest.
INPUT="${1:-$ROOT/../T-0025/services/etl/inputs/vermont-osm.pbf}"
TAGGED="$WORK/vermont-scenic.osm.pbf"
GRAPH="$WORK/graph-cache"

mkdir -p "$WORK"
echo "== input =="
ls -l "$INPUT"

echo "== 1. tagger image =="
docker build -f "$ROUTING/Dockerfile.tagger" -t scenic-tagger:t0031 "$ROUTING"

echo "== 2. SYNTHETIC tagging =="
# Kept if it is already there: tagging 434,265 ways takes minutes and the rule is deterministic. Delete
# work/vermont-scenic.osm.pbf to retag after changing tools/synthetic_scenic_tags.py.
if [ -f "$TAGGED" ]; then
  echo "kept existing $TAGGED"
else
  docker run --rm \
    -v "$(dirname "$INPUT")":/in:ro -v "$WORK":/out \
    scenic-tagger:t0031 --input "/in/$(basename "$INPUT")" --output "/out/$(basename "$TAGGED")"
fi
ls -l "$TAGGED"

echo "== 3. the stamp in the artifact's own header =="
docker run --rm -v "$WORK":/w -w /w scenic-etl:latest osmium fileinfo "$(basename "$TAGGED")"

echo "== 4. router image =="
docker build -t scenic-routing:t0213 "$ROUTING"

echo "== 5. import =="
# T-0213 extracted the import command line into import-graph.sh so the LA window and Vermont share one
# recipe. This step is that script with Vermont's two arguments.
bash "$ROUTING/import-graph.sh" "$TAGGED" "$GRAPH"
