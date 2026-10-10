"""check-sane-prod's c- rows (T-0345 rv1 B1): the checkout-side readers of sane_prod.tiles, on TEMP files.

Every t-/xt-/b- row reads this checkout's one real region.json and BasemapResolver.swift, so the readers that turn
them into (region, file) were never handed anything else. A c-<region>.<resolver> row writes one region.json variant
and one BasemapResolver variant to a temp directory and calls the SHIPPED sane_prod.tiles - the function ops/sane's
`sane_prod.py tiles` runs - with a fixed clock and a good manifest body. The rows are the whole cross product; the
expected (accepted, line) is a function of the pair, compared by FULL equality:
  region variant has no string id   -> (False, "cannot tell: <region> has no string id")   [region is read first]
  resolver's typed file is None     -> (False, "cannot tell: <resolver> does not hold exactly one ... line")
  resolver's typed file la.pmtiles  -> (True,  "tiles <version> region la file la.pmtiles == checkout, ...")
  resolver's typed file other.pmtiles -> (False, "tiles manifest: file is 'la.pmtiles', BasemapResolver reads ...")
The expected ids and files are typed here, never read back through the checker's own readers.
"""
from __future__ import annotations

import json
import os
import tempfile

from sane_prod_tiles_cases import NOW, good

REAL = '    public static let applicationSupportPath = "tiles/{}"'
COMMENTED = '    // public static let applicationSupportPath = "tiles/{}"'
HEAD = "import Foundation\n\npublic enum BasemapResolver {\n"
TAIL = "    public static let minimumArchiveBytes = 1_048_576\n}\n"

# name -> (region.json text or None for absent, the id the checker must read or None)
REGIONS = {
    "id-la": ('{"id": "la", "name": "Greater Los Angeles"}', "la"),
    "no-id": ('{"name": "Greater Los Angeles"}', None),
    "id-int": ('{"id": 7}', None),
    "id-empty": ('{"id": ""}', None),
    "id-null": ('{"id": null}', None),
    "not-json": ("not json", None),
    "not-object": ('["la"]', None),
    "absent": (None, None),
}


def swift(*lines: str, eol: str = "\n") -> str:
    return (HEAD + "".join(line + "\n" for line in lines) + TAIL).replace("\n", eol)


# name -> (BasemapResolver.swift text or None for absent, the file the checker must read or None)
RESOLVERS = {
    "one-la": (swift(REAL.format("la.pmtiles")), "la.pmtiles"),
    "one-la-crlf": (swift(REAL.format("la.pmtiles"), eol="\r\n"), "la.pmtiles"),
    "if-else": (swift("#if DEBUG", REAL.format("la.pmtiles"), "#else", REAL.format("other.pmtiles"), "#endif"), None),
    "two-la": (swift(REAL.format("la.pmtiles"), REAL.format("la.pmtiles")), None),
    "comment-only": (swift(COMMENTED.format("la.pmtiles")), None),
    "comment-other-real-la": (swift(COMMENTED.format("other.pmtiles"), REAL.format("la.pmtiles")), "la.pmtiles"),
    "comment-la-real-other": (swift(COMMENTED.format("la.pmtiles"), REAL.format("other.pmtiles")), "other.pmtiles"),
    "no-line": (swift('    public static let bundledName = "la.pmtiles"'), None),
    "absent": (None, None),
}


def checkout_rows() -> list[str]:
    return [f"c-{r}.{s}" for r in REGIONS for s in RESOLVERS]


def expected(region: str, resolver: str, region_path: str, resolver_path: str, body: dict) -> tuple[bool, str]:
    if REGIONS[region][1] is None:
        return False, f"cannot tell: {region_path} has no string id"
    file = RESOLVERS[resolver][1]
    if file is None:
        return False, f"cannot tell: {resolver_path} does not hold exactly one applicationSupportPath line"
    if file == "la.pmtiles":
        return True, (f"tiles {body['version']} region la file la.pmtiles == checkout, built_at {body['built_at']}, "
                      f"{body['bytes']} bytes")
    return False, f"tiles manifest: file is 'la.pmtiles', BasemapResolver reads {file!r}"


def write(path: str, text: str | None) -> None:
    if text is not None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)


def checkout_problems(sane_prod, only: set | None) -> tuple[int, list[str]]:
    """Run the selected c- rows through sane_prod.tiles at NOW on temp files; (rows run, failures)."""
    ran, failed = 0, []
    body = good(NOW)
    for region in REGIONS:
        for resolver in RESOLVERS:
            name = f"c-{region}.{resolver}"
            if only is not None and name not in only:
                continue
            ran += 1
            with tempfile.TemporaryDirectory(prefix="t0345-c-") as d:
                region_path, resolver_path = os.path.join(d, "region.json"), os.path.join(d, "BasemapResolver.swift")
                write(region_path, REGIONS[region][0])
                write(resolver_path, RESOLVERS[resolver][0])
                got = sane_prod.tiles(json.dumps(body), region_path, resolver_path, now=NOW)
                want = expected(region, resolver, region_path, resolver_path, body)
            if got != want:
                failed.append(f"{name}: got {got!r}, want {want!r}")
    return ran, failed


def checkout_meta_problems() -> list[str]:
    out = []
    names = checkout_rows()
    if len(set(names)) != len(REGIONS) * len(RESOLVERS):
        out.append(f"c- rows {len(set(names))} != {len(REGIONS)} regions x {len(RESOLVERS)} resolvers")
    outcomes = {(REGIONS[r][1] is None, RESOLVERS[s][1]) for r in REGIONS for s in RESOLVERS}
    kinds = {"region" if bad else ("resolver" if f is None else f) for bad, f in outcomes}
    if kinds != {"region", "resolver", "la.pmtiles", "other.pmtiles"}:
        out.append(f"c- rows reach outcomes {sorted(kinds)}, not all four")
    return out
