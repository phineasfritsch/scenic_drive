"""Per-class object counts, and the bounds that make a silent drop loud.

`osmium fileinfo --extended --json` is the source. Parsing it is separated from running it so the parsing and
the bounds arithmetic - the parts most likely to be wrong - are testable without a 1.2 GB download and a
container.
"""
from __future__ import annotations

import json

# The plan's data gate: counts within +/-15% of what was recorded, or the extract changed and somebody has to
# say why. Wide enough to absorb a weekly Geofabrik rebuild, narrow enough that a dropped class is caught.
DEFAULT_TOLERANCE = 0.15

# Below this, percentage bounds are noise: 3 waterfalls becoming 2 is a -33% swing and means nothing. Small
# classes get an absolute floor instead, so the check stays honest at both ends.
SMALL_CLASS = 20


def parse_fileinfo(text: str) -> dict[str, int]:
    """Object counts out of `osmium fileinfo -e -j` output.

    Raises ValueError rather than returning zeros: a fileinfo output we cannot read must never be reported as
    "this class is empty", which is indistinguishable from the failure this whole module exists to catch.
    """
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"fileinfo output is not JSON ({e})") from e
    if not isinstance(doc, dict):
        raise ValueError(f"fileinfo output is not an object: {type(doc).__name__}")
    counts = (doc.get("data") or {}).get("count") or doc.get("count")
    if not isinstance(counts, dict):
        raise ValueError("fileinfo output has no data.count - was --extended passed?")
    out = {}
    for kind in ("nodes", "ways", "relations"):
        v = counts.get(kind, 0)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(f"fileinfo count.{kind} is not a count: {v!r}")
        out[kind] = v
    return out


def total(counts: dict[str, int]) -> int:
    return counts.get("nodes", 0) + counts.get("ways", 0) + counts.get("relations", 0)


def check_bounds(actual: dict[str, int], recorded: dict[str, int],
                 tolerance: float = DEFAULT_TOLERANCE) -> list[str]:
    """Every way `actual` disagrees with `recorded`, as sentences. Empty means in bounds.

    A class that was recorded and is now absent is the headline case, and it is reported as missing rather
    than as a 100% drop, because "viewpoint is gone" is the sentence that gets acted on.
    """
    problems = []
    for cls, want in sorted(recorded.items()):
        if cls not in actual:
            problems.append(f"{cls}: recorded {want}, not present in this extract at all")
            continue
        got = actual[cls]
        if want <= SMALL_CLASS:
            # Absolute band for small classes: +/-tolerance of a handful is not a signal.
            slack = max(1, int(round(want * tolerance)))
            if abs(got - want) > slack:
                problems.append(f"{cls}: {got} vs recorded {want} (+/-{slack} allowed on a small class)")
            continue
        lo, hi = want * (1 - tolerance), want * (1 + tolerance)
        if not lo <= got <= hi:
            pct = (got - want) / want * 100
            problems.append(f"{cls}: {got} vs recorded {want} ({pct:+.1f}%, +/-{tolerance:.0%} allowed)")
    for cls in sorted(set(actual) - set(recorded)):
        problems.append(f"{cls}: {actual[cls]} present but never recorded - re-record deliberately")
    return problems
