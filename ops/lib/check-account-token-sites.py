#!/usr/bin/env python3
"""P-STORE-02's app side (T-0323 R1, R2): the paid-tier header is named at ONE site - IdentityHeaders - so every
plan-family client sends it through the shared IdentityHeaders.json and a fourth client cannot inline it.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-account-token-sites.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-account-token-sites.py --root DIR
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-account-token-sites.py --prove-red
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-account-token-sites.py --print-sites

A WHITELIST over SITES, never a blacklist of spellings (CLAUDE.md): every line of every *.swift under Sources/ and
apps/ that matches NAMES - `account-token` or `accountheader`, case-insensitively, since HTTP header names are
case-insensitive - must be, WHOLE (trailing whitespace dropped), one of APPROVED's (file, line) pairs, as many times
as it is listed. Only a line whose first non-blank characters are `//` is skipped (memory
source-guards-fail-closed). So the header inlined in a new client, spelled in another case, split at its prefix
(`"x-scenic-" + "account-token"`), or IdentityHeaders.accountHeader written by a client beside the shared json(),
is a new line - red, by name. An approved site that is gone is red too: APPROVED is re-approved in the diff that
moves it. Tests/ is not scanned (T-0323 R1): a test spells the header as its own literal oracle and sends nothing.

WHAT IT CANNOT SEE. A split inside `account-token` itself (`"x-scenic-acc" + "ount-token"`), unicode escapes, a name
built at runtime, non-Swift files, and the Worker (services/api, TypeScript). `/* */` block comments are read as
code, so a line inside one can only fail closed.

EXITS. 0 every site approved and every approved site present. 1 a site refused or an approved site missing.
2 fail-closed: a root missing, or no site found at all.
"""
from __future__ import annotations

import collections
import io
import os
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCANNED = ("Sources", "apps")
SKIP_DIRS = {".build", "DerivedData", ".swiftpm"}
NAMES = re.compile(r"account-token|accountheader", re.IGNORECASE)
IDENTITY = "Sources/ScenicAPIClient/IdentityHeaders.swift"
APPROVED = collections.Counter({
    IDENTITY + "\t" + '    public static let accountHeader = "x-scenic-account-token"': 1,
    IDENTITY + "\t" + "        if let account { headers[accountHeader] = account.uuidString.lowercased() }": 1,
})
PIN = "P-STORE-02 account-token sites"


def sites(root: pathlib.Path) -> collections.Counter:
    found = collections.Counter()
    for top in SCANNED:
        for dirpath, dirnames, filenames in os.walk(root / top):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if not name.endswith(".swift"):
                    continue
                path = pathlib.Path(dirpath) / name
                rel = path.relative_to(root).as_posix()
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.lstrip().startswith("//") or not NAMES.search(line):
                        continue
                    found[rel + "\t" + line.rstrip()] += 1
    return found


def check(root: pathlib.Path, out=sys.stdout) -> int:
    missing = [top for top in SCANNED if not (root / top).is_dir()]
    if missing:
        out.write("%s: REFUSING - %s missing under %s\n" % (PIN, ", ".join(missing), root))
        return 2
    found = sites(root)
    if not found:
        out.write("%s: REFUSING - no line matches %s; the check would examine nothing\n" % (PIN, NAMES.pattern))
        return 2
    refused = sorted((found - APPROVED).elements())
    gone = sorted((APPROVED - found).elements())
    for row in refused:
        out.write("REFUSED  site not on the whitelist: %s\n" % row.replace("\t", ": "))
    for row in gone:
        out.write("REFUSED  approved site missing: %s\n" % row.replace("\t", ": "))
    if refused or gone:
        out.write("%s: FAILED - %d unapproved, %d missing of %d approved\n"
                  % (PIN, len(refused), len(gone), sum(APPROVED.values())))
        return 1
    out.write("%s: ok - %d sites, every one approved, in %d file(s)\n"
              % (PIN, sum(found.values()), len({r.split("\t")[0] for r in found})))
    return 0


PLAN = "Sources/ScenicAPIClient/PlanClient.swift"
NEW_CLIENT = "Sources/ScenicAPIClient/WeatherClient.swift"
APP_FILE = "apps/ios/Packages/ScenicApp/Sources/PlanAdapter/ProbeClient.swift"
# (name, file, old or None to append/create, new, expected exit). A red row must exit 1 with its file refused.
RED_ROWS = (
    ("the header inlined in a new client file", NEW_CLIENT, None,
     'func send(_ r: inout URLRequest, _ t: String) { r.setValue(t, forHTTPHeaderField: "x-scenic-account-token") }\n'),
    ("the header split across a concatenation", NEW_CLIENT, None,
     'let header = "x-scenic-" + "account-token"\n'),
    ("the header in another case, in the app", APP_FILE, None,
     'let header = "X-Scenic-Account-Token"\n'),
    ("a new client writes IdentityHeaders.accountHeader", NEW_CLIENT, None,
     "func tag(_ h: inout [String: String], _ t: String) { h[IdentityHeaders.accountHeader] = t }\n"),
    ("a code line with a trailing comment", PLAN, None,
     'let inlined = "x-scenic-account-token" // fine\n'),
    ("a block comment line fails closed", APP_FILE, None,
     '/* "x-scenic-account-token" */\n'),
    ("an approved line repeated", IDENTITY, None,
     "        if let account { headers[accountHeader] = account.uuidString.lowercased() }\n"),
    ("the approved constant changed", IDENTITY, 'accountHeader = "x-scenic-account-token"',
     'accountHeader = "x-scenic-account-tokens"'),
)
CONTROLS = (
    ("a //-comment naming the header is not a site", APP_FILE, None,
     '/// sends x-scenic-account-token through IdentityHeaders.json\n'),
)


def copy_tree(dest: pathlib.Path) -> None:
    for top in SCANNED:
        for dirpath, dirnames, filenames in os.walk(ROOT / top):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith(".swift"):
                    src = pathlib.Path(dirpath) / name
                    to = dest / src.relative_to(ROOT)
                    to.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, to)


def apply_row(work: pathlib.Path, rel: str, old, new):
    """Edit one copied file; return (code, refused-by-name, restore) or None when the anchor is stale."""
    path = work / rel
    pristine = path.read_bytes() if path.exists() else None
    text = pristine.decode("utf-8") if pristine is not None else ""
    if old is not None and text.count(old) != 1:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(old, new, 1) if old else text + new, encoding="utf-8", newline="\n")
    buf = io.StringIO()
    code = check(work, buf)
    named = any(line.startswith("REFUSED") and rel in line for line in buf.getvalue().splitlines())
    if pristine is None:
        path.unlink()
    else:
        path.write_bytes(pristine)
    return code, named


def prove_red() -> int:
    work = pathlib.Path(tempfile.mkdtemp(prefix="account-token-sites-"))
    try:
        copy_tree(work)
        control = check(work, io.StringIO())
        sys.stdout.write("CONTROL  %-50s exit=%d (need 0)\n" % ("unmodified copy", control))
        controls_ok = control == 0
        for name, rel, old, new in CONTROLS:
            got = apply_row(work, rel, old, new)
            code = got[0] if got else -1
            controls_ok = controls_ok and code == 0
            sys.stdout.write("CONTROL  %-50s exit=%d (need 0)\n" % (name, code))
        red = 0
        for name, rel, old, new in RED_ROWS:
            got = apply_row(work, rel, old, new)
            if got is None:
                sys.stdout.write("STALE    %-50s anchor not found exactly once\n" % name)
                continue
            code, named = got
            ok = code == 1 and named
            red += ok
            sys.stdout.write("%-8s %-50s exit=%d %s\n" % ("red" if ok else "GREEN", name, code,
                                                          "refused by name" if named else "NOT NAMED"))
        ok = controls_ok and red == len(RED_ROWS)
        sys.stdout.write("PROVE-RED %s: %d of %d rows red by name, controls %s\n"
                         % ("OK" if ok else "FAILED", red, len(RED_ROWS), "green" if controls_ok else "NOT GREEN"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv) -> int:
    if "--prove-red" in argv:
        return prove_red()
    if "--print-sites" in argv:
        for row in sorted(sites(ROOT).elements()):
            sys.stdout.write(row + "\n")
        return 0
    root = pathlib.Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
