"""T-0224 MEASUREMENT: the way-length distribution per highway class over the LA clip.

NUMBERS ONLY. This script asserts nothing and carries no threshold; T-0209's anti-rat-run ruling is
written AFTER reading what it prints (CLAUDE.md: a predicate over a population nobody has looked at is
filed as a measurement task, not an acceptance).

It reads a GeoJSON text sequence on stdin - one GeoJSON Feature per line, as `osmium export` writes it -
and prints, per `highway` value: count, median m, p90 m, max m, the number and share of ways over 800 m,
and the id of the longest way. `residential`, `living_street` and `service` first, then every other class
by descending count.

WAY LENGTH is the haversine sum over the way's own node sequence, R = 6_371_008.8 m - the mean Earth
radius ScenicKit uses, so a length measured here and a length measured on the device are the same number.
Median is the mean of the two middle values at even n; p90 is NEAREST-RANK (the ceil(0.9*n)-th smallest),
which is the only percentile that is always a value the population actually contains.

EXACT COMMAND that produced T-0224's table (repo root; docker lives inside WSL on this box, the read-only
PBF lives in the MAIN checkout, this script lives in the T-0224 worktree). Single line, quoted for git-bash:

    wsl -e bash -lc "docker run --rm -v /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/work/la:/data:ro -v /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0224/services/etl/tests:/scripts:ro scenic-etl bash -lc 'osmium export /data/la-filtered.osm.pbf -f geojsonseq --geometry-types=linestring --add-unique-id=type_id | python3 /scripts/measure_way_lengths.py --source la-filtered.osm.pbf'"

`-f geojsonseq` prefixes every record with the RS control character (0x1e) and this script strips it;
osmium refuses `-f geojsonseq,print_record_separator=false`, so the separator is dealt with here.

The input is services/etl/work/la/la-filtered.osm.pbf (the T-0107 extract, meta.json counts summing to
560,208 filtered ways). osmium and python3 both come out of the pinned `scenic-etl` image
(services/etl/Dockerfile), never a host toolchain, for the reason etl/extract.py gives.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

EARTH_RADIUS_M = 6_371_008.8
LONG_WAY_M = 800.0  # the length the table reports a share over; T-0209/T-0221's clause names this number
FIRST = ("residential", "living_street", "service")
NO_HIGHWAY = "(no highway tag)"
RECORD_SEPARATOR = "\x1e"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle metres between two WGS84 points on a sphere of radius EARTH_RADIUS_M."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def line_length_m(coordinates: list) -> float:
    """Haversine sum over a GeoJSON LineString's [lon, lat] pairs."""
    total = 0.0
    previous = None
    for point in coordinates:
        lon, lat = float(point[0]), float(point[1])
        if previous is not None:
            total += haversine_m(previous[0], previous[1], lat, lon)
        previous = (lat, lon)
    return total


def median_m(sorted_lengths: list) -> float:
    n = len(sorted_lengths)
    middle = n // 2
    if n % 2:
        return sorted_lengths[middle]
    return (sorted_lengths[middle - 1] + sorted_lengths[middle]) / 2.0


def nearest_rank(sorted_lengths: list, fraction: float) -> float:
    """The ceil(fraction*n)-th smallest value - a member of the population, never an interpolation."""
    n = len(sorted_lengths)
    rank = max(1, math.ceil(fraction * n))
    return sorted_lengths[rank - 1]


def read_features(stream):
    """Yield (highway class, way id, LineString coordinates) per GeoJSON Feature line."""
    for line in stream:
        line = line.strip().lstrip(RECORD_SEPARATOR).strip()
        if not line:
            continue
        feature = json.loads(line)
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "LineString":
            yield (None, None, None)
            continue
        properties = feature.get("properties") or {}
        # `--add-unique-id=type_id` writes the id at the Feature's top level ("id":"w4049801"), not into
        # properties; the properties fallbacks cover an export configured the other way.
        way_id = feature.get("id") or properties.get("@id") or properties.get("id") or ""
        yield (properties.get("highway") or NO_HIGHWAY, str(way_id), geometry.get("coordinates") or [])


def collect(stream):
    """{class -> [lengths]}, {class -> (longest length, its way id)}, and the feature tallies."""
    lengths: dict = {}
    longest: dict = {}
    read = 0
    skipped_geometry = 0
    degenerate = 0
    for highway, way_id, coordinates in read_features(stream):
        read += 1
        if highway is None:
            skipped_geometry += 1
            continue
        if len(coordinates) < 2:
            degenerate += 1
            continue
        metres = line_length_m(coordinates)
        lengths.setdefault(highway, []).append(metres)
        if metres > longest.get(highway, (-1.0, ""))[0]:
            longest[highway] = (metres, way_id)
    return lengths, longest, read, skipped_geometry, degenerate


def ordered_classes(lengths: dict) -> list:
    head = [name for name in FIRST if name in lengths]
    tail = sorted((name for name in lengths if name not in FIRST), key=lambda n: (-len(lengths[n]), n))
    return head + tail


def print_table(lengths: dict, longest: dict) -> None:
    header = (
        f"{'highway class':<18}{'count':>9}{'median m':>11}{'p90 m':>11}{'max m':>12}"
        f"{'n>800m':>9}{'share>800m':>12}  longest way"
    )
    print(header)
    print("-" * (len(header) + 12))
    for name in ordered_classes(lengths):
        values = sorted(lengths[name])
        n = len(values)
        over = sum(1 for value in values if value > LONG_WAY_M)
        top_m, top_id = longest[name]
        print(
            f"{name:<18}{n:>9,}{median_m(values):>11.1f}{nearest_rank(values, 0.90):>11.1f}"
            f"{values[-1]:>12.1f}{over:>9,}{over / n:>11.2%}  {top_id} ({top_m:.1f} m)"
        )


def print_totals(lengths: dict, read: int, skipped_geometry: int, degenerate: int) -> None:
    every = sorted(value for values in lengths.values() for value in values)
    n = len(every)
    over = sum(1 for value in every if value > LONG_WAY_M)
    print()
    print(
        f"ALL CLASSES        {n:>9,}{median_m(every):>11.1f}{nearest_rank(every, 0.90):>11.1f}"
        f"{every[-1]:>12.1f}{over:>9,}{over / n:>11.2%}"
    )
    print(
        f"FEATURES read={read:,} measured={n:,} non-linestring={skipped_geometry:,} "
        f"under-2-nodes={degenerate:,}"
    )
    residential_family = [
        value for name in FIRST for value in lengths.get(name, [])
    ]
    if residential_family:
        family = sorted(residential_family)
        family_over = sum(1 for value in family if value > LONG_WAY_M)
        print(
            f"residential+living_street+service combined: n={len(family):,} "
            f"median={median_m(family):.1f} m p90={nearest_rank(family, 0.90):.1f} m "
            f"max={family[-1]:.1f} m over-800m={family_over:,} ({family_over / len(family):.2%})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", default="(stdin)", help="the PBF these features were exported from")
    arguments = parser.parse_args()
    print(f"WAY LENGTHS source={arguments.source} radius_m={EARTH_RADIUS_M} metric=haversine-sum")
    print(f"percentile=nearest-rank median=mean-of-two-middle long_way_threshold_m={LONG_WAY_M:.0f}")
    lengths, longest, read, skipped_geometry, degenerate = collect(sys.stdin)
    if not lengths:
        print("no LineString feature reached this script - check the osmium export command", file=sys.stderr)
        return 2
    print_table(lengths, longest)
    print_totals(lengths, read, skipped_geometry, degenerate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
