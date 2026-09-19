"""The FINGERPRINT program: every answer `etl.sinuosity` and `etl.proximity` give over the fixtures.

This is the witness an EQUIVALENT entry in ops/mutate/geometry_arms.py rests on. `budget_arms.py` states
its witnesses as prose - *"compiled STANDALONE, pristine against mutant, over 5891 cases ... all three came
back byte-identical"* - which is a fact about a sweep nobody can re-run. Here the sweep IS the harness: the
runner executes this file once over the pristine copy and once over each mutated copy, and compares the two
digests. An equivalence claim that stops being true stops passing on the next run instead of on the next
review.

It runs INSIDE the mutated COPY and never in the worktree: argv[0] is the copy's `services/etl` and it is
what goes on `sys.path`, so `from etl import proximity` resolves there. Run it with no argument and it
measures nothing - it refuses, because a fingerprint taken over the wrong tree would compare a mutant
against itself and call every mutation equivalent.

Every value is written with `repr`, at full precision, never rounded: the comparison is on BYTES. A refusal
is a value too - `ValueError: way_sinuosity: needs at least 2 coordinates, got 1` is as much a fact about
the module as a number is, and a mutant that turns a refusal into a default must not read as equivalent.
"""
from __future__ import annotations

import json
import pathlib
import sys


def value(fn) -> str:
    """The answer, or the refusal. Both are facts about the module and both go into the digest."""
    try:
        return repr(fn())
    except Exception as exc:                                  # noqa: BLE001 - a refusal is a value here
        return "%s: %s" % (type(exc).__name__, exc)


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case.get(key, [])]


def emit(out: list[str], name: str, label: str, fn) -> None:
    out.append("%-64s %-28s %s" % (name, label, value(fn)))


def measure(root: pathlib.Path) -> list[str]:
    """Every case in every geometry fixture, in a fixed order, through the module's public names."""
    sys.path.insert(0, str(root))
    from etl import proximity, sinuosity                      # noqa: E402 - after the path is set

    out: list[str] = []
    fixtures = sorted((root / "tests" / "fixtures").glob("geometry_*.json"))
    if not fixtures:
        raise SystemExit("REFUSED: no geometry fixtures under %s - nothing to fingerprint" % root)
    for path in fixtures:
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in sorted(k for k, v in data.items() if isinstance(v, list)):
            for case in data[key]:
                name = "%s:%s:%s" % (path.name, key, case.get("name", "?"))
                coords = coords_of(case)
                emit(out, name, "way_sinuosity", lambda c=coords: sinuosity.way_sinuosity(c))
                emit(out, name, "endpoint_gap_m", lambda c=coords: sinuosity.endpoint_gap_m(c))
                emit(out, name, "is_closed_way", lambda c=coords: sinuosity.is_closed_way(c))
                if "tags" in case:
                    tags = case["tags"]
                    emit(out, name, "is_tunnel", lambda t=tags: proximity.is_tunnel(t))
                    emit(out, name, "tunnel_meters",
                         lambda c=coords, t=tags: proximity.tunnel_meters(c, t))
                if "motorways" in case:
                    lines = [[(lat, lon) for lat, lon in line] for line in case["motorways"]]
                    emit(out, name, "meters_to_nearest_motorway",
                         lambda c=coords, m=lines: proximity.meters_to_nearest_motorway(c, m))
                    for i, line in enumerate(lines):
                        emit(out, name, "line_distance_m[%d]" % i,
                             lambda c=coords, ln=line: proximity.line_distance_m(c, ln))
    return out


def main(argv) -> int:
    if len(argv) != 1:
        sys.stdout.write("REFUSED: usage: geometry_probe.py <services/etl to measure>\n")
        return 2
    root = pathlib.Path(argv[0]).resolve()
    if not (root / "etl" / "proximity.py").exists():
        sys.stdout.write("REFUSED: %s is not a services/etl tree\n" % root)
        return 2
    sys.stdout.write("\n".join(measure(root)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
