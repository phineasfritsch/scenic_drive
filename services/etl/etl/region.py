"""A region is a bbox, a name, and the recorded shape of what came out of it last time.

The recorded counts are the point. An extract that silently stops emitting viewpoints, or a tag filter edited
to "clean up" motorways, produces a perfectly valid PBF that is simply missing things - and nothing downstream
notices until a route is wrong. Bounds turn that into a failing check at the stage that caused it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "regions"

# The world, as coordinates. Anything outside this is a typo, not a region.
LON_RANGE = (-180.0, 180.0)
LAT_RANGE = (-90.0, 90.0)
# A region smaller than this is a mistake (a swapped pair, a truncated literal); larger than this is not an
# extract, it is the planet, and the 15-minute build promise stops being true.
MIN_SPAN_DEG = 0.1
MAX_SPAN_DEG = 12.0


@dataclass(frozen=True)
class BBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def problems(self) -> list[str]:
        out = []
        for name, value, (lo, hi) in (
            ("min_lon", self.min_lon, LON_RANGE), ("max_lon", self.max_lon, LON_RANGE),
            ("min_lat", self.min_lat, LAT_RANGE), ("max_lat", self.max_lat, LAT_RANGE),
        ):
            if not isinstance(value, (int, float)) or value != value:  # NaN is not a coordinate
                out.append(f"{name} is not a number: {value!r}")
            elif not lo <= value <= hi:
                out.append(f"{name}={value} is outside {lo}..{hi}")
        if out:
            return out
        if self.min_lon >= self.max_lon:
            out.append(f"min_lon {self.min_lon} is not west of max_lon {self.max_lon}")
        if self.min_lat >= self.max_lat:
            out.append(f"min_lat {self.min_lat} is not south of max_lat {self.max_lat}")
        if out:
            return out
        for axis, span in (("lon", self.max_lon - self.min_lon), ("lat", self.max_lat - self.min_lat)):
            if span < MIN_SPAN_DEG:
                out.append(f"{axis} span {span:.4f} deg is below the {MIN_SPAN_DEG} deg floor")
            elif span > MAX_SPAN_DEG:
                out.append(f"{axis} span {span:.4f} deg is above the {MAX_SPAN_DEG} deg ceiling")
        return out

    def as_osmium(self) -> str:
        """osmium extract's --bbox form: left,bottom,right,top."""
        return f"{self.min_lon},{self.min_lat},{self.max_lon},{self.max_lat}"


@dataclass(frozen=True)
class CountsFrom:
    """Which extract produced `counts`. A baseline nobody can trace is a number, not a baseline.

    `bbox` is the killer field. On 2026-09-08 sfbay's first real extract came in 18-26% low across every
    class, and the cause was that its bbox had been corrected from -121.20 to -121.55 - removing Tracy and
    Stockton - while the recorded counts were left describing the old, larger region. Every class low by
    roughly the same fraction, which is the signature of a bbox change and not of a filter defect. The
    baseline had silently become a measurement of a region the code no longer cuts.

    Recording the bbox the counts were measured over turns that into a load-bearing check: if the region's
    bbox is edited and the counts are not re-recorded, the two disagree and `problems()` says so, at the
    stage that caused it, instead of surfacing as a 20% bounds failure weeks later that reads like a broken
    tag filter.
    """
    source: str
    source_bytes: int
    built_at: str
    bbox: str

    def problems(self, region_bbox: BBox) -> list[str]:
        out = []
        if not self.source:
            out.append("counts_from.source is empty - name the PBF the counts were measured from")
        if not isinstance(self.source_bytes, int) or isinstance(self.source_bytes, bool) \
                or self.source_bytes <= 0:
            out.append(f"counts_from.source_bytes is not a size: {self.source_bytes!r}")
        if not self.built_at:
            out.append("counts_from.built_at is empty - say when the extract ran")
        try:
            measured = tuple(float(v) for v in str(self.bbox).split(","))
        except ValueError:
            out.append(f"counts_from.bbox is not four numbers: {self.bbox!r}")
            return out
        if len(measured) != 4:
            out.append(f"counts_from.bbox is not four numbers: {self.bbox!r}")
            return out
        here = (region_bbox.min_lon, region_bbox.min_lat, region_bbox.max_lon, region_bbox.max_lat)
        if measured != here:
            out.append(
                f"counts were measured over {self.bbox} but the region's bbox is now "
                f"{region_bbox.as_osmium()} - the baseline describes a different region than the code cuts. "
                f"Re-record with ops/etl-extract --region <id> --record-counts.")
        return out


@dataclass(frozen=True)
class Region:
    id: str
    name: str
    counties: tuple[str, ...]
    bbox: BBox
    counts: dict[str, int] = field(default_factory=dict)
    counts_from: CountsFrom | None = None

    def problems(self) -> list[str]:
        out = [f"bbox: {p}" for p in self.bbox.problems()]
        if not self.id or not self.id.replace("-", "").replace("_", "").isalnum():
            out.append(f"id is not a usable directory name: {self.id!r}")
        if not self.name:
            out.append("name is empty")
        if not self.counties:
            out.append("counties is empty - name what the bbox is meant to cover, so it can be argued with")
        for cls, n in self.counts.items():
            if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                out.append(f"counts[{cls}] is not a count: {n!r}")
        # Counts without provenance are the defect above, one step earlier. No counts is fine - checkbounds
        # reports "cannot tell" and nothing pretends otherwise - but a baseline that exists must be traceable.
        if self.counts and self.counts_from is None:
            out.append("counts are recorded but counts_from is absent - a baseline nobody can trace to an "
                       "extract cannot be checked against one")
        if self.counts_from is not None:
            out.extend(self.counts_from.problems(self.bbox))
        return out


def load(region_id: str, root: Path | None = None) -> Region:
    """Read regions/<id>/region.json. Raises ValueError listing every problem, not just the first."""
    path = (root or REGIONS) / region_id / "region.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    # Keys beginning with _ are prose for humans reading the file; they are never read back as data.
    unknown = [k for k in data if not k.startswith("_") and k not in
               {"id", "name", "counties", "bbox", "counts", "counts_from"}]
    if unknown:
        raise ValueError(f"{path}: unknown field(s): {unknown}")
    b = data.get("bbox") or {}
    cf = data.get("counts_from")
    region = Region(
        id=data.get("id", ""),
        name=data.get("name", ""),
        counties=tuple(data.get("counties") or ()),
        bbox=BBox(b.get("min_lon", float("nan")), b.get("min_lat", float("nan")),
                  b.get("max_lon", float("nan")), b.get("max_lat", float("nan"))),
        counts=dict(data.get("counts") or {}),
        counts_from=None if not isinstance(cf, dict) else CountsFrom(
            source=cf.get("source", ""),
            source_bytes=cf.get("source_bytes", 0),
            built_at=cf.get("built_at", ""),
            bbox=cf.get("bbox", ""),
        ),
    )
    problems = region.problems()
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return region
