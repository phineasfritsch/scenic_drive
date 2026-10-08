#!/usr/bin/env python3
"""P-NAV-02 (T-0321): NavAdapter is the ONLY importer of Ferrostar (CLAUDE.md), as a WHITELIST of whole lines.

    python ops/lib/check-ferrostar-imports.py [repo-root]

The population is every line that can hold code - trailing CR stripped, trimmed; a line is dropped only when it
STARTS with `//` and holds no backslash (memory source-guards-fail-closed: nothing is cut inside a line) - of every
.swift file under apps/ios, Sources and Tests and the root Package.swift that names `ferrostar` in any case,
OUTSIDE NavAdapter's own source directory. Each such line must be one of the APPROVED lines below, compared whole
with its file, and each approved line must occur exactly once. So `import FerrostarCore`, `@preconcurrency import
FerrostarCoreFFI`, `import struct FerrostarCore.Route` or a second `.product(... "ferrostar")` anywhere but
NavAdapter is refused by name, whatever its spelling. A Ferrostar import split across lines still names the module
on a line of its own, which is in the population.

Then the manifest: the one `.product(name: "FerrostarCore", package: "ferrostar")` line sits in the target whose
`name:` is "NavAdapter" (the nearest `name:` above it after the nearest `.target(`), and NavAdapter's directory
holds at least one `import FerrostarCore` line - a guard over an adapter that imports nothing proves nothing.
Not checked here: whether the code compiles (ios-compile.yml), or a module reached through some re-export.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2])
MANIFEST = "apps/ios/Packages/ScenicApp/Package.swift"
ADAPTER = "apps/ios/Packages/ScenicApp/Sources/NavAdapter/"
PRODUCT = '.product(name: "FerrostarCore", package: "ferrostar"),'
APPROVED = [
    (MANIFEST, '.package(url: "https://github.com/stadiamaps/ferrostar", exact: "0.57.0"),'),
    (MANIFEST, PRODUCT),
]


def code_lines(path: pathlib.Path):
    for number, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        line = raw.rstrip("\r").strip()
        if line.startswith("//") and "\\" not in line:
            continue
        yield number, line


def swift_files():
    files = [ROOT / "Package.swift"]
    for top in ("apps/ios", "Sources", "Tests"):
        files += sorted((ROOT / top).rglob("*.swift"))
    return [f for f in files if f.is_file()]


def main() -> int:
    failures = []
    seen = []
    adapter_imports = 0
    for path in swift_files():
        rel = path.relative_to(ROOT).as_posix()
        for number, line in code_lines(path):
            if rel.startswith(ADAPTER):
                if line == "import FerrostarCore":
                    adapter_imports += 1
                continue
            if "ferrostar" not in line.lower():
                continue
            seen.append((rel, line))
            if (rel, line) not in APPROVED:
                failures.append("%s:%d names Ferrostar outside NavAdapter and is not an approved line: %s"
                                % (rel, number, line))
    for site in APPROVED:
        if seen.count(site) != 1:
            failures.append("approved line occurs %d time(s), expected 1: %s: %s" % (seen.count(site), *site))
    manifest = [line for _n, line in code_lines(ROOT / MANIFEST)]
    if PRODUCT in manifest:
        at = manifest.index(PRODUCT)
        target = max((i for i in range(at) if manifest[i].startswith(".target(")), default=-1)
        names = [line for line in manifest[target + 1:at] if line.startswith("name: ")]
        if target < 0 or not names or names[0] != 'name: "NavAdapter",':
            failures.append("the FerrostarCore product is a dependency of %s, not of NavAdapter"
                            % (names[0] if names else "no named target"))
    if adapter_imports == 0:
        failures.append("%s holds no `import FerrostarCore` line - the adapter this guard protects is gone" % ADAPTER)
    if failures:
        print("P-NAV-02 REFUSED:")
        for f in failures:
            print("  " + f)
        return 1
    print("P-NAV-02: %d line(s) naming Ferrostar outside %s, each one of the %d approved whole lines, once;"
          % (len(seen), ADAPTER, len(APPROVED)))
    print("  the FerrostarCore product is NavAdapter's dependency; NavAdapter imports FerrostarCore (%d line(s))."
          % adapter_imports)
    print("  Not checked here: compilation (ios-compile.yml) or a module reached through a re-export.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
