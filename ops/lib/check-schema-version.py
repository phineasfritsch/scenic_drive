#!/usr/bin/env python3
"""P-PROD-05's assertion: the corpus's schema_version and the Worker's are ONE value.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-schema-version.py [--root DIR]
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-schema-version.py --prove-red

The plan's OTA row lets a device download a corpus only when `schema_version == PlaceStore.schemaVersion`,
and the number the device compares against arrives from the Worker. Two numbers in two languages, no
compiler between them: on 2026-09-18 they were 1 and 0 and nothing in the repository noticed.

WHY NOT ONE SHARED FILE. It was the first design and it is wrong twice over. The Worker is bundled by
wrangler out of services/api/ and cannot read services/etl/, so "shared" would mean generated or copied -
a third place to be stale in. Worse, it would delete the property that matters: the Worker's value is
pinned ON THE WIRE by services/api/test/routes.test.ts, a literal a human typed, and a test that imports
the same constant the handler imports asserts nothing. So both literals stay typed at their own site, this
check reads them as TEXT, and the pin is the anchor. (T-0173, ruling R6.)

IT ALSO REFUSES WHEN ITS OWN PIN IS GONE. This repository's recurring defect is a check nothing runs
(P-OPS-06, P-OPS-05). The only thing that runs this one is P-PROD-05, so deleting the pin would silence it
with every gate green. Deleting the pin is therefore a refusal, exit 2.

EXITS. 0 the two agree. 1 they disagree. 2 fail-closed - a file missing, a literal missing or ambiguous,
or the pin gone. Never "ok" on something it could not read.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import pathlib
import re
import shutil
import tempfile

CORPUS_FILE = "services/etl/etl/schema.py"
WORKER_FILE = "services/api/src/index.ts"
PINS_FILE = "pins/PINS.yaml"
PIN_ID = "P-PROD-05"

CORPUS_RE = re.compile(r"^SCHEMA_VERSION\s*=\s*(\d+)\s*(?:#.*)?$", re.M)
WORKER_RE = re.compile(r"^export const SCHEMA_VERSION\s*=\s*(\d+)\s*;\s*(?://.*)?$", re.M)
PIN_RE = re.compile(r"^-\s+id:\s*%s\s*$" % re.escape(PIN_ID), re.M)

# Read from this file's own location, never from the caller's cwd: ops/lib/<this> -> repo root (T-0055).
DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Refusal(Exception):
    """Something could not be read. Exit 2, never a verdict."""


def _read(root: pathlib.Path, rel: str) -> str:
    path = root / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Refusal(f"cannot read {rel}: {exc}") from exc


def _one(pattern: re.Pattern, text: str, rel: str, shape: str) -> int:
    found = pattern.findall(text)
    if not found:
        raise Refusal(f"{rel}: no line matching `{shape}`; this check cannot read the version it guards")
    if len(found) > 1:
        raise Refusal(f"{rel}: {len(found)} lines match `{shape}` ({', '.join(found)}); which one ships?")
    return int(found[0])


def versions(root: pathlib.Path) -> tuple[int, int]:
    corpus = _one(CORPUS_RE, _read(root, CORPUS_FILE), CORPUS_FILE, "SCHEMA_VERSION = <n>")
    worker = _one(WORKER_RE, _read(root, WORKER_FILE), WORKER_FILE, "export const SCHEMA_VERSION = <n>;")
    return corpus, worker


def check(root: pathlib.Path) -> int:
    if not PIN_RE.search(_read(root, PINS_FILE)):
        raise Refusal(f"{PINS_FILE} has no `- id: {PIN_ID}`: the only thing that runs this check is gone")
    corpus, worker = versions(root)
    if corpus != worker:
        print(f"{PIN_ID}: schema_version disagrees - {CORPUS_FILE} says {corpus}, "
              f"{WORKER_FILE} says {worker}.")
        print("  A device downloads a corpus only when the two agree (plan, Runtime lifecycles / OTA).")
        print("  Fix: bump both in one commit, and type the new value into "
              "services/api/test/routes.test.ts.")
        return 1
    print(f"{PIN_ID}: schema_version={corpus} in {CORPUS_FILE} and {WORKER_FILE}")
    return 0


# --------------------------------------------------------------------------------- --prove-red

def _mutate(text: str, pattern: re.Pattern, value: str) -> str:
    return pattern.sub(value, text, count=1)


CASES = (
    ("control: the tree as committed", {}, 0),
    ("corpus bumped alone", {CORPUS_FILE: ("corpus", "SCHEMA_VERSION = 99")}, 1),
    ("Worker bumped alone", {WORKER_FILE: ("worker", "export const SCHEMA_VERSION = 99;")}, 1),
    (f"{PIN_ID} deleted from PINS.yaml", {PINS_FILE: ("pin", "- id: P-PROD-05-RETIRED")}, 2),
    ("corpus literal deleted", {CORPUS_FILE: ("corpus", "# SCHEMA_VERSION was here")}, 2),
    ("Worker literal deleted", {WORKER_FILE: ("worker", "// SCHEMA_VERSION was here")}, 2),
    ("corpus literal duplicated",
     {CORPUS_FILE: ("corpus", "SCHEMA_VERSION = 2\nSCHEMA_VERSION = 3")}, 2),
)
PATTERNS = {"corpus": CORPUS_RE, "worker": WORKER_RE, "pin": PIN_RE}


def prove_red(root: pathlib.Path) -> int:
    """Run the check against a throwaway copy of the three files, once per mutation.

    A check that has never been seen red is untested (CLAUDE.md, Verification). These are the mutations that
    matter: each one is a way the two versions come apart, or a way this check stops being able to tell.
    """
    bad = 0
    print(f"{PIN_ID} --prove-red: {len(CASES)} cases against a copy of the tree at {root}")
    print(f"  {'case':<38} {'expect':>6} {'got':>4}  verdict")
    for name, edits, expected in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = pathlib.Path(tmp)
            for rel in (CORPUS_FILE, WORKER_FILE, PINS_FILE):
                (sandbox / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / rel, sandbox / rel)
            for rel, (kind, replacement) in edits.items():
                target = sandbox / rel
                target.write_text(
                    _mutate(target.read_text(encoding="utf-8"), PATTERNS[kind], replacement),
                    encoding="utf-8")
            sink = io.StringIO()
            with contextlib.redirect_stdout(sink):
                got = main(["--root", str(sandbox)])
        ok = got == expected
        bad += 0 if ok else 1
        print(f"  {name:<38} {expected:>6} {got:>4}  {'ok' if ok else 'NOT DISCRIMINATING'}")
    if bad:
        print(f"{PIN_ID} --prove-red: {bad} case(s) did not behave as stated. The check is not a check.")
        return 1
    print(f"{PIN_ID} --prove-red: all {len(CASES)} cases behaved as stated")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ops/lib/check-schema-version.py", add_help=True)
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="repository root (default: this file's)")
    parser.add_argument("--prove-red", action="store_true",
                        help="run the check against mutations of the tree and print the table")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root)
    try:
        return prove_red(root) if args.prove_red else check(root)
    except Refusal as exc:
        print(f"{PIN_ID}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
