"""Mutation population for ops/sane exit 4's corpus invariants (T-0372): ops/lib/sane_corpus.py and its ops/sane block.

    python ops/mutate/sane_corpus.py [--only 1,2,...]

Each mutation is one exact text replacement in a SUBJECT file (it must occur exactly once), applied, then every
__pycache__ under ops/lib and services/etl is purged and the driver waits 1.1 s (a mutant restored within one
second can leave a stale .pyc), then `bash ops/lib/check-sane-corpus --only <its killer rows>` runs. A mutation is
KILLED when that run exits non-zero AND every named killer row printed FAIL. The original bytes are restored and
byte-checked after every mutation, and in a finally. Before any mutation the killer rows must pass on the pristine
subjects (a killer that is red without a mutant proves nothing), and the subjects must equal HEAD.

Exit 0 every mutation killed and at least MIN_MUTATIONS ran; 1 a survivor or too few; 2 cannot tell.
Classified in ops/lib/mutate_population_table.py PROBES, not DRIVERS: check-mutate-population reads SUBJECT_MODULES
only under services/etl/etl and Sources, and these subjects live in ops/.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB = "ops/lib/sane_corpus.py"
SANE = "ops/sane"
SUBJECTS = (LIB, SANE)
MIN_MUTATIONS = 26

# (file, old, new, killer rows)
MUTATIONS = [
    (LIB, "if found != str(schema.SCHEMA_VERSION):", "if found is None:", ("open-schema-older", "open-schema-newer")),
    (LIB, "if found != str(schema.SCHEMA_VERSION):", "if found.strip() != str(schema.SCHEMA_VERSION):",
     ("open-schema-padded",)),
    (LIB, 'if meta.get("build_complete") != "1":', 'if meta.get("build_complete") == "0":',
     ("open-incomplete-absent", "open-incomplete-true")),
    (LIB, 'if meta.get("build_complete") != "1":', "if False:", ("open-incomplete-zero",)),
    (LIB, "NOT (value >= 0.0 AND value <= 1.0)", "NOT (value >= 0.0 AND value < 1.0)",
     ("clean-on-every-bound", "terms-terms_osm-one")),
    (LIB, "NOT (value >= 0.0 AND value <= 1.0)", "NOT (value > 0.0 AND value <= 1.0)",
     ("clean-on-every-bound", "terms-terms_raster-zero")),
    (LIB, "NOT (value >= 0.0 AND value <= 1.0)", "NOT (value >= 0.0 AND value <= 1.5)",
     ("terms-terms_osm-above-one", "terms-terms_raster-above-one")),
    (LIB, "NOT (value >= 0.0 AND value <= 1.0)", "NOT (value >= -0.5 AND value <= 1.0)",
     ("terms-terms_osm-below-zero", "terms-terms_raster-below-zero")),
    (LIB, "NOT (value >= 0.0 AND value <= 1.0)", "NOT (value >= 0.0 AND value <= 1.0) AND abs(value) < 1e308",
     ("terms-terms_osm-plus-inf", "terms-terms_raster-minus-inf")),
    (LIB, "    for table in TERM_TABLES:\n        try:\n            total",
     "    for table in TERM_TABLES[:1]:\n        try:\n            total", ("terms-terms_raster-above-one",)),
    (LIB, "            raise Refused(f\"cannot read {table}: {exc}\") from exc", "            continue",
     ("terms-terms_osm-missing", "terms-terms_raster-missing")),
    (LIB, "    if found < floor:", "    if found <= floor:", ("clean-on-every-bound",)),
    (LIB, "    if found < floor:", "    if found < floor - 1:", ("viewpoints-below-floor",)),
    (LIB, '"SELECT count(*) FROM places WHERE cls = ?"', '"SELECT count(*) FROM places WHERE cls = ? OR 1"',
     ("viewpoints-below-floor-many-parks",)),
    (LIB, "floor = VIEWPOINT_FLOORS.get(region) if isinstance(region, str) else None",
     "floor = VIEWPOINT_FLOORS.get(region, 76) if isinstance(region, str) else 76",
     ("viewpoints-region-sfbay", "viewpoints-region-absent")),
    (LIB, "floor = VIEWPOINT_FLOORS.get(region) if", "floor = VIEWPOINT_FLOORS.get(region.lower()) if",
     ("viewpoints-region-case",)),
    (LIB, "    bad = surfacecoverage.verdict(table)", "    bad = surfacecoverage.refusals(table)",
     ("surface-class-missing", "surface-empty-table")),
    (LIB, '        raise Refused(f"meta carries no {surfacecoverage.META_KEY}")', '        return "no table"',
     ("surface-absent",)),
    (LIB, '                    out.append(("FAIL", row, f"{path.name}: {exc}"))',
     '                    out.append(("ok", row, f"{path.name}: {exc}"))', ("viewpoints-below-floor",)),
    (LIB, '    return REFUSE if any(status == "FAIL" for status, _, _ in rows) else 0', "    return 0",
     ("d-store-below-floor",)),
    (LIB, '    named = env.get("SANE_CORPUS", "")\n    if named:', '    named = env.get("SANE_CORPUS", "")\n    if False:',
     ("d-named-beats-store",)),
    (LIB, 'pathlib.Path(store) / f"{r}-corpus.sqlite" for r in regions', 'pathlib.Path(store) / f"{r}.sqlite" for r in regions',
     ("d-store-clean",)),
    (SANE, '      FAIL) fail "$crow" "$cmsg" 4; cfail=1;;', '      FAIL) skip "$crow" "$cmsg";;', ("viewpoints-below-floor",)),
    (SANE, '      *) fail "corpus-db" "sane_corpus.py printed an unparsed line: $cst $crow $cmsg" 4; cfail=1;;',
     "      *) ;;", ("p-python-echo",)),
    (SANE, "if [[ $crc -ne 0 && $cfail -eq 0 ]]", "if [[ $crc -ne 0 && $cfail -eq 1 ]]", ("p-python-false",)),
    (SANE, 'if [[ $local_checks -eq 0 && -z "${SANE_CORPUS:-}" ]]', "if [[ $local_checks -eq 0 ]]",
     ("clean-on-every-bound",)),
]


def git_head(rel: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=ROOT).stdout


def purge() -> None:
    for base in ("ops/lib", "services/etl"):
        for cache in (ROOT / base).rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
    time.sleep(1.1)


def table(rows: tuple) -> tuple[int, str]:
    p = subprocess.run(["bash", "ops/lib/check-sane-corpus", "--only", ",".join(rows)], capture_output=True,
                       text=True, cwd=ROOT)
    return p.returncode, p.stdout


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    only = None
    if len(argv) == 3 and argv[1] == "--only":
        only = {int(x) for x in argv[2].split(",")}
    elif len(argv) != 1:
        print("MUTATE refuse  usage: python ops/mutate/sane_corpus.py [--only 1,2]")
        return 2
    pristine = {rel: (ROOT / rel).read_bytes() for rel in SUBJECTS}
    for rel, data in pristine.items():
        if data != git_head(rel):
            print(f"MUTATE refuse  {rel} differs from HEAD; commit or stash before mutating")
            return 2
    picked = [(i, m) for i, m in enumerate(MUTATIONS, 1) if only is None or i in only]
    killers = tuple(sorted({r for _, m in picked for r in m[3]}))
    purge()
    rc, out = table(killers)
    if rc != 0:
        print(f"MUTATE refuse  the killer rows are not green on the pristine subjects:\n{out}")
        return 2
    survivors = []
    try:
        for i, (rel, old, new, rows) in picked:
            text = pristine[rel].decode("utf-8")
            if text.count(old) != 1:
                print(f"MUTATE refuse  #{i}: the old text occurs {text.count(old)} times in {rel}")
                return 2
            (ROOT / rel).write_bytes(text.replace(old, new).encode("utf-8"))
            purge()
            rc, out = table(rows)
            (ROOT / rel).write_bytes(pristine[rel])
            if (ROOT / rel).read_bytes() != pristine[rel]:
                print(f"MUTATE refuse  #{i}: {rel} was not restored byte for byte")
                return 2
            red = [r for r in rows if f"SANE-CORPUS FAIL     {r}:" in out]
            if rc != 0 and len(red) == len(rows):
                print(f"MUTATE killed  #{i} {rel}: {new.strip()[:60]!r} by {', '.join(red)}")
            else:
                survivors.append(i)
                print(f"MUTATE SURVIVED #{i} {rel}: {new.strip()[:60]!r} (exit {rc}, red {red} of {list(rows)})")
    finally:
        for rel, data in pristine.items():
            (ROOT / rel).write_bytes(data)
        purge()
    if survivors or (only is None and len(picked) < MIN_MUTATIONS):
        print(f"MUTATE FAIL  survivors {survivors}; ran {len(picked)}, floor {MIN_MUTATIONS}")
        return 1
    print(f"MUTATE ok  {len(picked)}/{len(picked)} killed (floor {MIN_MUTATIONS}, population {len(MUTATIONS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
