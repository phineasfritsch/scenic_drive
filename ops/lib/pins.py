#!/usr/bin/env python3
"""Load-bearing properties: run every assertion in pins/PINS.yaml.

  pins.py [--source-only] [--tier linux|mac] [--verbose]

Prints `PINS ok=N skipped=M pending=P expired=K failed=F` and exits 1 when failed > 0 or expired > 0.

Rules (each one exists because an agent will otherwise satisfy the letter of the check):
  * an assertion equal to TODO (or empty) FAILS - an unenforced pin is worse than none.
  * a pin not runnable on this host (runs_on excludes the tier) is SKIPPED, but if it has expires_days and
    last_verified is missing or older than that, it is EXPIRED and fails the run. Human/device pins therefore
    force a human to re-verify on a schedule instead of silently rotting.
  * verifier must differ from owner for last_verified to count.
  * `pending: T-XXXX` marks a pin whose assertion cannot exist yet. It is reported as PENDING and does not fail -
    UNLESS the named task is already in queue/done/ (then the debt is due) or does not exist at all.
  * --source-only runs only pins with anchor: source (the cheap CI gate on every push).

pins/PINS.yaml is a list of mappings. Values are scalars, "quoted strings" or [flow, lists]. No PyYAML needed.
"""
import datetime as dt
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = ROOT / "pins" / "PINS.yaml"
QUEUE = ROOT / "queue"
DEFAULT_EXPIRY = {"human": 30, "device": 30}


# ----------------------------------------------------------------------------- yaml subset
def _scalar(v):
    v = v.strip()
    if v in ("", "null", "~"):
        return None
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    if len(v) >= 2 and v[0] == v[-1] and v[0] == '"':
        # double-quoted: honour \" and \\ so assertions can carry quotes and regex backslashes
        return re.sub(r'\\(["\\])', r"\1", v[1:-1])
    if len(v) >= 2 and v[0] == v[-1] and v[0] == "'":
        return v[1:-1]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def load(path):
    """Parse a top-level list of flat mappings. Lines: `- key: value` starts an item, `  key: value` continues it."""
    items, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^-\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            cur = {m.group(1): _scalar(m.group(2))}
            items.append(cur)
            continue
        m = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m and cur is not None:
            cur[m.group(1)] = _scalar(m.group(2))
            continue
        raise ValueError(f"PINS.yaml: cannot parse line: {raw!r}")
    return items


# ----------------------------------------------------------------------------- helpers
def host_tier():
    return "mac" if platform.system() == "Darwin" else "linux"


def task_state(tid):
    for state in ("backlog", "ready", "claimed", "review", "blocked", "done"):
        if list((QUEUE / state).glob(f"{tid}-*.md")):
            return state
    return None


def run(assertion):
    """Run one assertion under bash from the repo root. Returns (ok, output)."""
    p = subprocess.run(["bash", "-o", "pipefail", "-c", assertion], cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def days_since(date_str):
    if not date_str:
        return None
    d = dt.date.fromisoformat(str(date_str)[:10])
    return (dt.date.today() - d).days


# ----------------------------------------------------------------------------- main
USAGE = ("usage: check-pins [--source-only] [--verbose] [--tier <tier>]\n"
         "  --tier takes a value and it must be a tier some pin declares in runs_on.")


def _argv(argv, declared):
    """(options, None) or (None, why). Every wrong invocation is refused, with exit 2.

    Exit 2, not 1: `1` is what this tool returns for "a pin FAILED", and an agent or a CI step that reads
    only the status could not tell "you typed the flag wrong" apart from "a load-bearing property of this
    repository is broken". Every other ops/* entry point answers a bad invocation with 2.
    """
    opts = {"source_only": False, "verbose": False, "tier": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--source-only":
            opts["source_only"] = True
        elif a == "--verbose":
            opts["verbose"] = True
        elif a == "--tier":
            i += 1
            if i >= len(argv):
                return None, "--tier needs a value; it was the last word on the line."
            opts["tier"] = argv[i]
        elif a.startswith("--tier="):
            opts["tier"] = a.split("=", 1)[1]
        elif a.startswith("-"):
            return None, f"{a} is not an option of check-pins."
        else:
            return None, f"{a!r} is not an option. check-pins takes no operands."
        i += 1
    tier = opts["tier"]
    if tier is not None:
        if tier == "":
            return None, "--tier was given an empty value."
        if tier not in declared:
            # THE ONE THAT MATTERS. `--tier linx` skipped every pin, ran no assertion, printed a summary
            # that reads like success and exited 0. A tier nothing declares cannot be a tier anything runs.
            return None, (f"--tier {tier!r} is a tier no pin declares. Declared: "
                          f"{', '.join(sorted(declared)) or '(none)'}.")
    return opts, None


def main(argv):
    if not PINS.exists():
        print(f"PINS FAIL: {PINS.relative_to(ROOT).as_posix()} missing")
        return 1
    pins = load(PINS)
    # The set of tiers is DERIVED from the pins, never a literal list here. A hard-coded
    # {linux, mac, device, human} would keep accepting `--tier device` long after the last device pin was
    # deleted, and would reject a tier somebody legitimately adds - both of which are the check disagreeing
    # with the file it exists to enforce.
    declared = set()
    for _p in pins:
        _r = _p.get("runs_on") or []
        for _x in ([_r] if isinstance(_r, str) else _r):
            declared.add(str(_x).strip())
    opts, why = _argv(argv, declared)
    if why:
        print(f"check-pins: {why}")
        print(USAGE)
        return 2
    source_only = opts["source_only"]
    verbose = opts["verbose"]
    tier = opts["tier"] or host_tier()
    ok = skipped = pending = expired = failed = 0
    problems = []
    seen = set()
    for p in pins:
        pid = p.get("id") or "?"
        if pid in seen:
            problems.append(f"{pid}: duplicate id")
            failed += 1
        seen.add(pid)
        if source_only and p.get("anchor") != "source":
            skipped += 1
            continue
        assertion = p.get("assertion")
        runs_on = p.get("runs_on") or []
        if isinstance(runs_on, str):
            runs_on = [runs_on]

        # pending debt
        pend = p.get("pending")
        if pend:
            st = task_state(str(pend))
            if st is None:
                problems.append(f"{pid}: pending on {pend}, which does not exist in queue/")
                failed += 1
            elif st == "done":
                problems.append(f"{pid}: pending on {pend} but that task is done - the pin must be real now")
                failed += 1
            else:
                pending += 1
                if verbose:
                    print(f"  pending {pid} (until {pend} in {st}/)")
            continue

        if not assertion or str(assertion).strip().upper() == "TODO":
            problems.append(f"{pid}: assertion is TODO/empty - an unenforced pin is false confidence")
            failed += 1
            continue

        if tier in runs_on:
            good, out = run(str(assertion))
            if good:
                ok += 1
                if verbose:
                    print(f"  ok      {pid}")
            else:
                failed += 1
                problems.append(f"{pid}: {p.get('statement')}\n      assertion: {assertion}\n      output: {out[:400] or '(none)'}")
            continue

        # not runnable here: skipped, unless its verification is stale
        skipped += 1
        expiry = p.get("expires_days")
        if expiry is None:
            expiry = next((DEFAULT_EXPIRY[t] for t in runs_on if t in DEFAULT_EXPIRY), None)
        if expiry is not None:
            age = days_since(p.get("last_verified"))
            verifier, owner = p.get("verifier"), p.get("owner")
            if age is None:
                expired += 1
                problems.append(f"{pid}: never verified (runs_on {runs_on}); needs a verifier != owner to run it and set last_verified")
            elif verifier and owner and verifier == owner:
                expired += 1
                problems.append(f"{pid}: last_verified by its own owner ({owner}) does not count")
            elif age > int(expiry):
                expired += 1
                problems.append(f"{pid}: verified {age} days ago, limit {expiry}")
            elif verbose:
                print(f"  skipped {pid} (runs_on {runs_on}, verified {age}d ago)")
    print(f"PINS ok={ok} skipped={skipped} pending={pending} expired={expired} failed={failed} tier={tier}{' source-only' if source_only else ''}")
    for pr in problems:
        print(" -", pr)
    if ok == 0 and failed == 0 and expired == 0:
        # A run that executed no assertion is not a passing run. `--tier human` reaches this honestly -
        # its one pin is pending - and that is exactly the state that must not be reported as success,
        # because "nothing ran" and "everything passed" print the same summary otherwise. The counts above
        # already say WHY (skipped / pending); this makes the exit code say it too.
        print(" - no assertion ran: every pin was skipped or is pending, so this run proves nothing. "
              "That is P-PROC-01 passing on an empty set, which is the shape this repository refuses.")
        return 1
    return 1 if (failed or expired) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
