#!/usr/bin/env python3
"""Classify every services/*/pyproject.toml for ops/test's python tier (T-0198).

usage: python_suites.py [--table FILE] [--root DIR]

The table (default ops/lib/python-suites.txt) is a WHITELIST: one row per pyproject on disk,
    run <dir>
    exclude <dir> <reason...>
Blank lines and lines whose first non-blank character is '#' are ignored.

prints, one per line:
    RUN <dir>                  for every run row, in table order
    EXCLUDE <dir> <reason>     for every exclude row
    FAIL: <what>               for every refusal, each naming the pyproject or row it is about
exit 0 when nothing is refused, 1 when anything is, 2 when the table cannot be read.

Before this, ops/test ran pytest only when services/etl/pyproject.toml existed, so services/tiles and
services/routing ran in no job and a regression there left the one command green. Discovery is anchored on the
files on disk: a new pyproject is refused until someone classifies it, and nothing is skipped silently.
"""
import argparse
import glob
import os
import sys

TABLE_DEFAULT = "ops/lib/python-suites.txt"
PATTERN = "services/*/pyproject.toml"


def on_disk(root):
    found = glob.glob(os.path.join(root, PATTERN))
    return sorted(os.path.relpath(os.path.dirname(p), root).replace(os.sep, "/") for p in found)


def parse(lines, table):
    rows, fails = [], []
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        kind = parts[0]
        where = f"{table}:{n}"
        if kind == "run" and len(parts) == 2:
            rows.append(("run", parts[1], ""))
        elif kind == "exclude" and len(parts) == 3 and parts[2].strip():
            rows.append(("exclude", parts[1], parts[2].strip()))
        elif kind == "exclude" and len(parts) == 2:
            fails.append(f"{where}: exclude {parts[1]} has no reason - an exclusion must say why")
        else:
            fails.append(f"{where}: malformed row {line!r} - expected `run <dir>` or `exclude <dir> <reason>`")
    return rows, fails


def classify(root, table_path, lines):
    rows, fails = parse(lines, table_path)
    disk = on_disk(root)
    seen = set()
    for _, d, _ in rows:
        if d in seen:
            fails.append(f"{table_path}: {d} has more than one row")
        seen.add(d)
        if d not in disk:
            fails.append(f"STALE row in {table_path}: {d}/pyproject.toml does not exist")
    excluded = {d for kind, d, _ in rows if kind == "exclude"}
    for d in disk:
        if d not in seen:
            fails.append(f"UNCLASSIFIED {d}/pyproject.toml: add `run {d}` or `exclude {d} <reason>` to {table_path}")
    out = []
    emitted = set()
    for kind, d, reason in rows:
        if d in emitted or d not in disk:
            continue
        emitted.add(d)
        if kind == "run" and d not in excluded:
            out.append(f"RUN {d}")
        elif kind == "exclude":
            out.append(f"EXCLUDE {d} {reason}")
    return out, fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=TABLE_DEFAULT)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    table = os.path.join(args.root, args.table)
    try:
        with open(table, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        print(f"FAIL: cannot read {args.table}: {exc}")
        return 2
    out, fails = classify(args.root, args.table, lines)
    for line in out:
        print(line)
    for f in fails:
        print(f"FAIL: {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
