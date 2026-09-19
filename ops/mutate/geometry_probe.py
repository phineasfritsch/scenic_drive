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

THE FIRST LINE IS THE ROOT THAT WAS MEASURED, and it is hashed with the values (rv1-pr107 on PR #107).
Refusing the no-argument call was never enough: pointed at `services/etl` this program printed the pristine
values and the BASELINE digest with no complaint, so a runner handed the worktree instead of the copy would
read every mutant as IDENTICAL and every EQUIVALENT entry would pass over a tree with no mutation in it. With
the root inside the digest that arm fails CLOSED - a fingerprint taken over `services/etl` cannot equal a
baseline taken over `.build-mutate-geometry/etl` whatever the module answers, so it reads DIFFERS and the
witness refuses rather than agreeing.

Every value is written with `repr`, at full precision, never rounded: the comparison is on BYTES. A refusal
is a value too - `ValueError: way_sinuosity: needs at least 2 coordinates, got 1` is as much a fact about
the module as a number is, and a mutant that turns a refusal into a default must not read as equivalent.

THE REPORTING BOUNDARY IS NOT A FIXTURE COORDINATE. `meters_to_nearest_motorway` ends on `nearest if
nearest <= radius_m else math.inf`, and no fixture case's nearest approach sits at MOTORWAY_SEARCH_RADIUS_M,
so for one release of this harness the `<=`-for-`<` mutant printed `(IDENTICAL)`: the witness could not see
the module's boundary at all, and a false equivalence wrong ONLY there would have passed it. A fixture case
tuned to land on 1000.0 exactly IS reachable - the projection quantises `px - ax` at ~1.9e-9 m, so 8191
consecutive doubles of one longitude offset give exactly 1000.0 - and is the wrong fix: it buys ONE value in
ONE case, and it decays silently the day the rounding moves. `at_its_own_radius` below asks instead for each
case's own answer back at its own answer, where `nearest <= radius_m` is the identity `x <= x`: the boundary
is exercised BY CONSTRUCTION on every proximity case, on every run, with no literal anywhere.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys


def value(fn) -> str:
    """The answer, or the refusal. Both are facts about the module and both go into the digest."""
    try:
        return repr(fn())
    except Exception as exc:                                  # noqa: BLE001 - a refusal is a value here
        return "%s: %s" % (type(exc).__name__, exc)


def root_identity(root: pathlib.Path) -> str:
    """Line one: WHICH tree these values came from, written relative to the repository root.

    Not a digest of the three subject sources. A content digest is the wrong instrument for this: the tree
    this line exists to catch is `services/etl`, which is PRISTINE by construction, so its content digest IS
    the baseline's - it would fold in exactly the bytes that make a worktree-pointed probe read IDENTICAL,
    and a witness that agrees with the mistake it is meant to expose is not a witness. A location cannot be
    confused that way.

    Relative, with forward slashes, never the absolute path: the digest has to be the same number in every
    checkout, because a reviewer quoting this table line for line from their own worktree is how round 1 was
    reviewed. A root outside the repository keeps its full path - it is a different tree and says so.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    try:
        name = root.relative_to(repo).as_posix()
    except ValueError:
        name = root.as_posix()
    return "%-64s %-28s %s" % ("MEASURED ROOT", "tree", name)


def coords_of(case, key="coordinates"):
    return [(lat, lon) for lat, lon in case.get(key, [])]


def emit(out: list[str], name: str, label: str, fn) -> None:
    out.append("%-64s %-28s %s" % (name, label, value(fn)))


def at_its_own_radius(proximity, coords, lines) -> float:
    """`meters_to_nearest_motorway` asked a second time with its OWN unbounded answer as the radius.

    The first call passes `math.inf`, which no radius test can reject, so the answer is the nearest approach
    itself; the second passes that answer back as `radius_m`. In a pristine tree the comparison is the
    identity `x <= x` and the distance is reported; under a mutant that makes the radius EXCLUSIVE it is
    `x < x`, which is false for every float, and the same case reports `math.inf`. Neither call depends on
    a coordinate landing on a particular number, so this holds for every case in every fixture - and for
    any case added later - rather than for one tuned literal.

    The unbounded call is unaffected by that mutation (`x < inf` and `x <= inf` agree for every non-inf x,
    and both answer inf when there is no candidate at all), so the radius handed to the second call is the
    same number in both trees and the two digests are compared over the same question.
    """
    answer = proximity.meters_to_nearest_motorway(coords, lines, radius_m=math.inf)
    return proximity.meters_to_nearest_motorway(coords, lines, radius_m=answer)


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
                    emit(out, name, "meters_at_its_own_radius",
                         lambda c=coords, m=lines: at_its_own_radius(proximity, c, m))
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
    sys.stdout.write("\n".join([root_identity(root)] + measure(root)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
