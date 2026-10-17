#!/usr/bin/env bash
# T-0392 A3: the served router behind its front door, end to end, in WSL docker. Brings services/routing's
# compose.yaml up against an IMPORTED graph with a throwaway secret, sends the two request shapes the Worker sends
# (services/api/src scenicPlanner.ts `route`, isochronePlanner.ts `isochroneUrl`) through Caddy, and prints one
# PASS/FAIL line per named check and `E2E passed/total`. Exit 0 only when every check passed. Tears down after.
#
#   bash services/routing/tests/front_door_e2e.sh services/routing/work/graph-la
#
# Nothing here is a secret: the value is random per run and dies with the containers.
set -uo pipefail

GRAPH="$(cd "$1" && pwd)"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="scenic-routing-e2e"
BASE="http://127.0.0.1:80"
SECRET="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
PLACEHOLDER="REPLACE_WITH_THE_WORKER_ROUTER_SECRET"
OUT="$(mktemp -d)"
pass=0
total=0

compose() { (cd "$HERE" && ROUTER_GRAPH="$GRAPH" docker compose -p "$PROJECT" -f compose.yaml "$@"); }
teardown() { ROUTER_SECRET="$SECRET" compose down -v >/dev/null 2>&1; rm -rf "$OUT"; }
trap teardown EXIT

check() {  # check <name> <command...>: the command's exit status is the verdict
  local name="$1"
  shift
  total=$((total + 1))
  if "$@"; then pass=$((pass + 1)); echo "PASS $name"; else echo "FAIL $name"; fi
}

# The Worker's body: points [lon,lat], points_encoded false, instructions false, ch.disable, the details list.
route_body() {  # route_body <profile> <with custom model 0|1>
  python3 - "$1" "$2" <<'PY'
import json, sys
body = {"points": [[-118.49, 34.02], [-118.60, 34.09]], "profile": sys.argv[1], "points_encoded": False,
        "instructions": False, "ch.disable": True,
        "details": ["scenic_score", "road_class", "osm_way_id", "surface", "road_access", "time"]}
if sys.argv[2] == "1":
    body["custom_model"] = {"priority": [{"if": "scenic_score < 5", "multiply_by": "0.5"}]}
print(json.dumps(body))
PY
}

status() {  # status <method> <path> <header value or -> [body]: prints the HTTP status, body to $OUT/last
  local args=(-s -o "$OUT/last" -w "%{http_code}" -X "$1" "$BASE$2")
  [[ "$3" != "-" ]] && args+=(-H "x-scenic-router-secret: $3")
  [[ $# -ge 4 ]] && args+=(-H "content-type: application/json" --data "$4")
  curl "${args[@]}"
}

route_ok() {  # route_ok <profile> <model>: 200 and a path with distance, time and every requested detail
  [[ "$(status POST /route "$SECRET" "$(route_body "$1" "$2")")" == 200 ]] || return 1
  python3 - "$OUT/last" <<'PY'
import json, sys
path = json.load(open(sys.argv[1]))["paths"][0]
need = {"scenic_score", "road_class", "osm_way_id", "surface", "road_access", "time"}
ok = path["distance"] > 0 and path["time"] > 0 and need <= set(path["details"]) and len(path["points"]["coordinates"]) > 1
print("  route distance=%.0f m time=%.0f s points=%d" % (path["distance"], path["time"] / 1000, len(path["points"]["coordinates"])))
sys.exit(0 if ok else 1)
PY
}

isochrone_ok() {
  local q="point=34.09,-118.60&profile=car_fast&time_limit=900&buckets=1&reverse_flow=false"
  [[ "$(status GET "/isochrone?$q" "$SECRET")" == 200 ]] || return 1
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1]))["polygons"]; print("  isochrone polygons=%d" % len(p)); sys.exit(0 if p else 1)' "$OUT/last"
}

info_hash_ok() {
  [[ "$(status GET /info "$SECRET")" == 200 ]] || return 1
  local want
  want="$(sha256sum "$GRAPH/properties" | cut -d' ' -f1)"
  python3 - "$OUT/last" "$want" <<'PY'
import json, sys
info = json.load(open(sys.argv[1]))
names = sorted(p["name"] for p in info["profiles"])
print("  info graph_hash=%s properties_sha256=%s profiles=%s" % (info.get("graph_hash"), sys.argv[2], names))
sys.exit(0 if info.get("graph_hash") == sys.argv[2] and names == ["car_fast", "car_scenic"] else 1)
PY
}

refused() {  # refused <want status> <method> <path> <header or -> [body]
  local want="$1"
  shift
  local got
  got="$(status "$@")"
  echo "  $1 $2 -> $got"
  [[ "$got" == "$want" ]]
}

unpublished() {
  local id
  id="$(ROUTER_SECRET="$SECRET" compose ps -q graphhopper)"
  [[ -n "$id" && -z "$(docker port "$id")" ]]
}

echo "== up: graph $GRAPH =="
ls -l "$GRAPH" | head -20
if ! ROUTER_SECRET="$SECRET" compose up -d --build; then echo "E2E 0/10 (compose up failed)"; exit 1; fi
ready=0
for _ in $(seq 1 120); do
  if [[ "$(status GET /info "$SECRET")" == 200 ]]; then ready=1; break; fi
  sleep 2
done
[[ $ready == 1 ]] || { compose logs --tail 60; echo "E2E 0/10 (never ready)"; exit 1; }

check route_fast_with_secret route_ok car_fast 0
check route_scenic_custom_model_with_secret route_ok car_scenic 1
check isochrone_with_secret isochrone_ok
check info_graph_hash_equals_properties_sha256 info_hash_ok
check route_without_secret_401 refused 401 POST /route - "$(route_body car_fast 0)"
check route_wrong_secret_401 refused 401 POST /route "${SECRET}x" "$(route_body car_fast 0)"
check info_without_secret_401 refused 401 GET /info -
check unlisted_path_404 refused 404 GET /maps/ "$SECRET"
check graphhopper_port_unpublished unpublished

echo "== the front door restarted with the README's placeholder as its secret =="
ROUTER_SECRET="$PLACEHOLDER" compose up -d --force-recreate --no-deps front >/dev/null 2>&1
python3 -c "import time; time.sleep(3)"
check placeholder_secret_401_when_box_started_with_it refused 401 POST /route "$PLACEHOLDER" "$(route_body car_fast 0)"

echo "E2E $pass/$total"
[[ $pass == "$total" && $total == 10 ]]
