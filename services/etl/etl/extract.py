"""Cut the region out of the state extract, keep the tags we route and curate on, and report what came out.

  python -m etl.extract --region sfbay              extract, filter, count, compare to region.json
  python -m etl.extract --region sfbay --record-counts   ... and write the counts back into region.json

The counts are the deliverable as much as the PBF is. An extract that runs to completion and quietly contains
40% fewer residential ways is indistinguishable from a good one by every downstream stage; the per-class count
plus a recorded bound is what makes that loud at the step that caused it.

osmium runs in services/etl/Dockerfile's image (T-0038) when docker is available, so the toolchain is the
pinned one rather than whatever is on the box. --no-docker uses a local osmium, which is fine for a one-off
but is not what a recorded count should ever be produced by.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import counts as ct
from . import region as rg
from . import tagfilter as tf

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
WORK = ROOT / "work"
IMAGE = "scenic-etl"
SOURCE_PBF = "california-osm.pbf"


class OsmiumError(RuntimeError):
    pass


class Osmium:
    """osmium, in the pinned image or on the host. Every path it is given is inside `mount`."""

    def __init__(self, mount: Path, use_docker: bool, image: str = IMAGE):
        self.mount = mount.resolve()
        self.use_docker = use_docker
        self.image = image

    def argv(self, args: list[str]) -> list[str]:
        if not self.use_docker:
            return ["osmium", *args]
        return ["docker", "run", "--rm", "-v", f"{self.mount}:/w", "-w", "/w", self.image, "osmium", *args]

    def rel(self, path: Path) -> str:
        """A path as osmium will see it - relative to the mount, so host and container agree."""
        return path.resolve().relative_to(self.mount).as_posix()

    def run(self, args: list[str], capture: bool = False) -> str:
        argv = self.argv(args)
        p = subprocess.run(argv, capture_output=True, text=True)
        if p.returncode != 0:
            raise OsmiumError(f"{' '.join(argv[:6])}... exited {p.returncode}: {(p.stderr or '').strip()[:400]}")
        return p.stdout if capture else ""


def count_class(osmium: Osmium, src: Path, cls: str, scratch: Path) -> int:
    """Objects of one reporting class in `src`, via filter-then-fileinfo.

    Counting by filtering is slower than a single pass, but it uses the SAME expressions the keep-pass uses.
    A count computed a different way than the filter is a count that can agree with itself while both are
    wrong about the file.
    """
    out = scratch / f"count-{cls}.osm.pbf"
    if out.exists():
        out.unlink()
    osmium.run(["tags-filter", "-q", "--overwrite", "-o", osmium.rel(out), osmium.rel(src),
                tf.class_expression(cls)])
    info = osmium.run(["fileinfo", "--extended", "--json", osmium.rel(out)], capture=True)
    out.unlink(missing_ok=True)
    return ct.total(ct.parse_fileinfo(info))


def extract(region_id: str, use_docker: bool, source: Path, work: Path) -> tuple[rg.Region, dict[str, int]]:
    region = rg.load(region_id)
    problems = tf.problems()
    if problems:
        raise OsmiumError("the tag filter is not structurally sound: " + "; ".join(problems))

    work.mkdir(parents=True, exist_ok=True)
    # One mount covering both the source and the work dir, so container paths resolve for both.
    osmium = Osmium(ROOT, use_docker)
    regional = work / f"{region_id}.osm.pbf"
    filtered = work / f"{region_id}-filtered.osm.pbf"

    t0 = time.time()
    print(f"extract   {source.name} -> {regional.name}  bbox {region.bbox.as_osmium()}", flush=True)
    osmium.run(["extract", "-q", "--overwrite", "--bbox", region.bbox.as_osmium(),
                "-o", osmium.rel(regional), osmium.rel(source)])
    print(f"          {regional.stat().st_size / 1e6:.0f} MB in {time.time() - t0:.0f}s", flush=True)

    t1 = time.time()
    print(f"filter    {regional.name} -> {filtered.name}  {len(tf.keep_expressions())} expressions", flush=True)
    osmium.run(["tags-filter", "-q", "--overwrite", "-o", osmium.rel(filtered), osmium.rel(regional),
                *tf.keep_expressions()])
    print(f"          {filtered.stat().st_size / 1e6:.0f} MB in {time.time() - t1:.0f}s", flush=True)

    found: dict[str, int] = {}
    for cls in tf.all_classes():
        found[cls] = count_class(osmium, filtered, cls, work)
        print(f"  {cls:<16} {found[cls]:>9,}", flush=True)
    return region, found


def write_meta(region: rg.Region, found: dict[str, int], source: Path, work: Path) -> Path:
    meta = work / "meta.json"
    meta.write_text(json.dumps({
        "region": region.id,
        "bbox": region.bbox.as_osmium(),
        "source": source.name,
        "source_bytes": source.stat().st_size,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": found,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return meta


def record_counts(region_id: str, found: dict[str, int]) -> Path:
    """Write the counts into region.json. Deliberate, never automatic: a bound that re-records itself on every
    run is not a bound, it is a diary."""
    path = rg.REGIONS / region_id / "region.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["counts"] = {k: found[k] for k in sorted(found)}
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="etl.extract", description=__doc__)
    ap.add_argument("--region", default="sfbay")
    ap.add_argument("--input", type=Path, default=None, help=f"defaults to inputs/{SOURCE_PBF}")
    ap.add_argument("--work", type=Path, default=None, help="defaults to work/<region>")
    ap.add_argument("--record-counts", action="store_true",
                    help="write the counts into region.json instead of checking against them")
    ap.add_argument("--no-docker", action="store_true", help="use a local osmium instead of the pinned image")
    args = ap.parse_args(argv)

    source = args.input or (INPUTS / SOURCE_PBF)
    if not source.is_file():
        print(f"extract: {source} is missing - run ops/etl-fetch-inputs first", file=sys.stderr)
        return 2
    use_docker = not args.no_docker
    if use_docker and shutil.which("docker") is None:
        print("extract: docker is not on PATH; re-run with --no-docker to use a local osmium, knowing that a "
              "count recorded from an unpinned toolchain is not a bound", file=sys.stderr)
        return 2

    work = args.work or (WORK / args.region)
    try:
        region, found = extract(args.region, use_docker, source, work)
    except (OsmiumError, ValueError) as e:
        print(f"extract: {e}", file=sys.stderr)
        return 2

    meta = write_meta(region, found, source, work)
    print(f"meta      {meta}")

    if args.record_counts:
        path = record_counts(args.region, found)
        print(f"recorded  {path} - review the diff before committing it")
        return 0

    problems = ct.check_bounds(found, region.counts)
    if problems:
        print("BOUNDS FAIL")
        for p in problems:
            print(f"  {p}")
        return 4
    print(f"BOUNDS OK  {len(region.counts)} class(es) within {ct.DEFAULT_TOLERANCE:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
