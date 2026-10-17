#!/usr/bin/env bash
# Drives ops/deploy-routing through its three refusals and three rehearsed deploys inside a THROWAWAY git
# repository under mktemp, on a filesystem that has real symbolic links (the Windows checkout does not, so
# test_deploy_routing_rehearsal.py runs this through WSL). Nothing here touches this repository.
#
#   bash deploy_rehearsal_driver.sh <path to ops/deploy-routing> [<services/routing to ship>]
#
# T-0392: the throwaway repository also commits services/routing's compose.yaml and Caddyfile (the second
# argument's, default the directory beside this script), because a release now ships the compose bundle at HEAD.
#
# It prints a marked transcript; the pytest beside it makes the assertions. Exit 0 means the driver itself
# ran, never that the script under test behaved - a refusal that stopped refusing prints its way into the
# transcript and fails there.
set -euo pipefail

DEPLOY_SRC="$1"
ROUTING_SRC="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

REPO="$TMP/repo"
GRAPH="$TMP/graph"
BOX="$TMP/box"
mkdir -p "$REPO/ops" "$GRAPH"
printf 'edges\n' >"$GRAPH/edges"
printf 'nodes\n' >"$GRAPH/nodes"

cp "$DEPLOY_SRC" "$REPO/ops/deploy-routing"
chmod +x "$REPO/ops/deploy-routing"
mkdir -p "$REPO/services/routing"
cp "$ROUTING_SRC/compose.yaml" "$ROUTING_SRC/Caddyfile" "$REPO/services/routing/"
cd "$REPO"
git init -q -b main .
git config user.email "rehearsal@example.invalid"
git config user.name "T-0213 rehearsal"
git add ops/deploy-routing services/routing/compose.yaml services/routing/Caddyfile
git commit -q -m "the script under test"
git init -q --bare "$TMP/origin.git"
git remote add origin "$TMP/origin.git"
git push -q -u origin main

run() {  # run(<graph dir>, <VAR=value>...) bare, echo its exit status, never abort this driver
  local graph="$1"
  shift
  set +e
  env -u SCENIC_ROUTING_HOST -u SCENIC_ROUTING_USER -u SCENIC_ROUTING_KEY -u SCENIC_ROUTING_ROOT \
    -u SCENIC_ROUTING_REHEARSE "$@" bash ops/deploy-routing "$graph" 2>&1
  echo "exit=$?"
  set -e
}

echo "=== refusal 1: not a built graph ==="
run "$TMP/not-a-graph"

echo "=== refusal 2: credentials missing (HEAD is on origin) ==="
run "$GRAPH"

echo "=== refusal 3: HEAD not on origin ==="
git commit -q --allow-empty -m "unpushed"
run "$GRAPH"
git push -q origin main

echo "=== refusal 4: the box has no secret file ==="
run "$GRAPH" SCENIC_ROUTING_REHEARSE="$BOX" SCENIC_ROUTING_RESTART_CMD="echo [stub] docker compose up"
mkdir -p "$BOX"
printf 'ROUTER_SECRET=rehearsal-not-a-secret
' >"$BOX/router.secret.env"

for attempt in 1 2 3; do
  echo "=== rehearsed deploy $attempt ==="
  run "$GRAPH" SCENIC_ROUTING_REHEARSE="$BOX" SCENIC_ROUTING_RESTART_CMD="echo [stub] docker compose up"
  sleep 1  # the release directory is named to the second
done

echo "=== current is a symlink ==="
if [[ -L "$BOX/current" ]]; then echo "SYMLINK yes"; else echo "SYMLINK no"; fi
echo "=== current resolves to ==="
basename "$(readlink "$BOX/current")"
echo "=== releases on disk ==="
ls -1 "$BOX/releases"
echo "=== the graph under current ==="
ls -1 "$BOX/current/graph"
echo "=== the bundle under current ==="
ls -1 "$BOX/current" | grep -v '^graph$'
echo "=== the default restart command ==="
grep -o 'docker compose -p scenic-routing --env-file [^ ]* up -d --build --remove-orphans' "$REPO/ops/deploy-routing"
echo "=== driver done ==="
