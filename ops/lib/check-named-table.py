#!/usr/bin/env python3
"""Bind one pin's entry of ops/lib/named-tests.json to an approved digest and name count.

usage: check-named-table.py [--prove-red] PIN SHA256 COUNT

run-named-tests.py refuses only a pin that names ZERO tests: a row dropped from the
table (with the filter that ran it), a row swapped for another name, or a row repeated
so the count still adds up all stay green, because the table is the gate's own input.
This guard holds the whole entry - every runner, file, filter and name - to SHA256, the
sha256 of its canonical JSON (keys sorted, no whitespace, UTF-8), and to COUNT distinct
names. Any edit of the entry is red until the digest and count beside the pin's
assertion in pins/PINS.yaml are re-approved in the same diff.

--prove-red runs mutants of the live entry (in memory, nothing written) and requires
each to be refused BY NAME, and two controls (the entry as is; its keys reordered) green.
Exits 0 when the entry matches (or, with --prove-red, every row is red by name).
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "ops" / "lib" / "named-tests.json"


def names_of(entry):
    """Every name the runner would require for this entry, in table order."""
    out = []
    for f, names in (entry.get("vitest") or {}).items():
        out += [f"{f} :: {n}" for n in names]
    out += list((entry.get("swift") or {}).get("tests") or [])
    return out


def digest(entry):
    canon = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def refusals(table, pin, want_sha, want_count):
    """[str] - empty when the pin's entry is exactly the approved one."""
    entry = table.get(pin)
    if not isinstance(entry, dict) or not entry:
        return [f"{pin} has no entry in {TABLE.name}"]
    out = []
    names = names_of(entry)
    seen = set()
    for n in names:
        if n in seen:
            out.append(f"duplicate name {n}")
        seen.add(n)
    if len(seen) != want_count:
        out.append(f"count {len(seen)} distinct names != approved {want_count}")
    got = digest(entry)
    if got != want_sha:
        out.append(f"digest {got} != approved {want_sha}")
    return out


def _swift(e):
    return e.setdefault("swift", {})


def m_drop_suite_with_filter(e):
    sw = _swift(e)
    last = sw["tests"][-1].split("/")[0]
    short = last.split(".")[-1]
    sw["tests"] = [t for t in sw["tests"] if not t.startswith(last + "/")]
    f = sw["filter"].replace("|" + short, "").replace(short + "|", "")
    sw["filter"] = re.sub(r"\(([^|()]*)\)", r"\1", f)


def m_drop_vitest_row(e):
    f = sorted(e["vitest"])[-1]
    e["vitest"][f] = e["vitest"][f][:-1]


def m_repeat_row(e):
    sw = _swift(e)
    sw["tests"][-1] = sw["tests"][0]


def m_rename_row(e):
    sw = _swift(e)
    sw["tests"][-1] = sw["tests"][-1] + "Renamed"


def m_narrow_filter(e):
    sw = _swift(e)
    sw["filter"] = sw["filter"] + "X"


def m_add_row(e):
    sw = _swift(e)
    sw["tests"].append(sw["tests"][0].split("/")[0] + "/added()")


def m_drop_file(e):
    del e["vitest"][sorted(e["vitest"])[0]]


def m_drop_entry(e):
    e.clear()


ROWS = [
    ("a swift suite dropped with its filter (T-0323 M3b)", m_drop_suite_with_filter,
     ["count", "digest"]),
    ("a vitest row dropped", m_drop_vitest_row, ["count", "digest"]),
    ("a row replaced by a repeat of another", m_repeat_row, ["duplicate name", "count", "digest"]),
    ("a row replaced by another name", m_rename_row, ["digest"]),
    ("the swift filter changed alone", m_narrow_filter, ["digest"]),
    ("a row added", m_add_row, ["count", "digest"]),
    ("a whole vitest file dropped", m_drop_file, ["count", "digest"]),
    ("the entry emptied", m_drop_entry, ["has no entry"]),
]


def prove_red(table, pin, want_sha, want_count):
    entry = table.get(pin)
    if not isinstance(entry, dict) or not entry.get("vitest") or not entry.get("swift"):
        print(f"PROVE-RED REFUSED: {pin} needs a vitest and a swift runner to mutate")
        return 1
    ok = True
    if refusals(table, pin, want_sha, want_count):
        print("  CONTROL the entry as is: RED (expected green)")
        ok = False
    else:
        print("  CONTROL the entry as is: green")
    shuffled = copy.deepcopy(table)
    shuffled[pin] = dict(reversed(list(entry.items())))
    if refusals(shuffled, pin, want_sha, want_count):
        print("  CONTROL keys reordered: RED (expected green)")
        ok = False
    else:
        print("  CONTROL keys reordered: green")
    red = 0
    for label, mutate, expect in ROWS:
        t = copy.deepcopy(table)
        mutate(t[pin])
        got = refusals(t, pin, want_sha, want_count)
        missing = [x for x in expect if not any(x in r for r in got)]
        if got and not missing:
            red += 1
            print(f"  RED {label}: {'; '.join(got)}")
        else:
            print(f"  GREEN {label}: NOT NAMED {missing or expect}")
    if ok and red == len(ROWS):
        print(f"PROVE-RED OK: {red} of {len(ROWS)} rows red by name, controls green")
        return 0
    print(f"PROVE-RED FAILED: {red} of {len(ROWS)} rows red by name, controls {'green' if ok else 'NOT GREEN'}")
    return 1


def main(argv):
    prove = argv[:1] == ["--prove-red"]
    args = argv[1:] if prove else argv
    if len(args) != 3 or not re.fullmatch(r"[0-9a-f]{64}", args[1]) or not args[2].isdigit():
        print(__doc__.strip().splitlines()[2])
        return 2
    pin, want_sha, want_count = args[0], args[1], int(args[2])
    try:
        table = json.loads(TABLE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"NAMED-TABLE {pin} REFUSED: {TABLE.name} unreadable: {e}")
        return 1
    if prove:
        return prove_red(table, pin, want_sha, want_count)
    got = refusals(table, pin, want_sha, want_count)
    if got:
        for r in got:
            print(f"  REFUSED {r}")
        print(f"NAMED-TABLE {pin} FAILED - re-approve the digest and count beside the assertion")
        return 1
    print(f"NAMED-TABLE {pin} ok - {want_count} distinct names, sha256 {want_sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
