#!/usr/bin/env python3
"""Load-bearing properties: run every assertion in pins/PINS.yaml.

  pins.py [--source-only] [--tier linux|mac] [--verbose]

Prints `PINS ok=N skipped=M pending=P expired=K failed=F`. Exit 0 only when the run proved it ran: exit 1 when
failed > 0, expired > 0, or a floor below was breached; exit 2 when the arguments themselves were refused.

Rules (each one exists because an agent will otherwise satisfy the letter of the check):
  * the run must prove it executed something - see the floors below. failed=0 over an empty list is not a pass.
  * an unrecognised argument or --tier is refused, not silently honoured as "nothing matched".
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

# ----------------------------------------------------------------------------- the run must prove it ran
# Third instance of one bug. `test -z "$(...)"` over an empty file list passed vacuously in P-OPS-01's
# assertion (reviewer-5 -> ops/lib/check-exec-bits got MIN_FILES + REQUIRED) and again in P-SRC-02's
# (reviewer-10 -> ops/lib/check-line-cap got MIN_FILES). The runner that executes both never got the guard:
# `ok=0 ... failed=0` exit 0 was reachable three ways, none of them touching an assertion -
#   (a) empty pins/PINS.yaml            -> load() returns [], nothing iterates       -> MIN_PINS
#   (b) `anchor: source` -> `sources`   -> --source-only skips all 12, push gate green -> MIN_RAN_SOURCE_ONLY
#                                          with the import ban and 300-line cap dead   + REQUIRED_SOURCE
#   (c) `--tier bogus`, no file edit    -> `tier in runs_on` never true               -> TIERS
# Floors sit below the current counts so a deliberate removal has headroom; REQUIRED carries the precision.
# None of this touches the runs_on skip logic: skipping is correct, reporting success after skipping
# everything is not.
TIERS = ("linux", "mac")
MIN_PINS = 10            # 12 today
MIN_RAN = 6              # 9 assertions execute on tier=linux today
MIN_RAN_SOURCE_ONLY = 2  # 3 execute under --source-only today
REQUIRED = ("P-SRC-01", "P-SRC-02", "P-OPS-01", "P-GIT-01", "P-DATA-02", "P-TEST-01", "P-PROC-01",
            "P-ATTR-02", "P-PROD-01", "P-COST-02", "P-SAFE-05", "P-HUMAN-01")
# The two pins the `pins-source-only` job in .github/workflows/linux-core.yml exists for. Anchored on the id
# and the anchor field, never on the job's comment.
REQUIRED_SOURCE = ("P-SRC-01", "P-SRC-02")


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


# ----------------------------------------------------------------------------- argv
def parse_args(argv):
    """Strict. Returns (opts, error). A typo must refuse, never quietly select an empty set of pins."""
    usage = f"accepted: --tier <{'|'.join(TIERS)}>, --source-only, --verbose"
    source_only = verbose = False
    tier = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--tier":
            if i + 1 >= len(argv):
                return None, f"--tier needs a value; {usage}"
            tier, i = argv[i + 1], i + 2
            continue
        if a == "--source-only":
            source_only = True
        elif a == "--verbose":
            verbose = True
        else:
            return None, f"unrecognised argument {a!r}; {usage}"
        i += 1
    if tier is None:
        tier = host_tier()
    elif tier not in TIERS:
        return None, (f"unknown --tier {tier!r}; {usage}. An unknown tier matches no runs_on, "
                      "so every pin would skip and the run would report failed=0")
    return (source_only, verbose, tier), None


# ----------------------------------------------------------------------------- structural guards
def check_population(pins):
    """Floors on the list being checked, before any assertion runs. Returns a list of failure lines."""
    rel = PINS.relative_to(ROOT).as_posix()
    if len(pins) < MIN_PINS:
        return [f"only {len(pins)} pin(s) loaded from {rel} (expected >= {MIN_PINS}).",
                "  An empty or truncated pin list must never read as 'every load-bearing property holds'."]
    by_id = {p.get("id"): p for p in pins}
    missing = [pid for pid in REQUIRED if pid not in by_id]
    if missing:
        return [f"required pin id(s) absent from {rel}: {' '.join(missing)}.",
                "  A pin that silently disappears is the same failure as one that never ran."]
    wrong = [f"{pid} (anchor: {by_id[pid].get('anchor')!r})" for pid in REQUIRED_SOURCE
             if by_id[pid].get("anchor") != "source"]
    if wrong:
        return [f"pin(s) the --source-only push gate exists for are not anchor: source: {' '.join(wrong)}.",
                "  The import ban and the 300-line cap would stop running on every push with nothing red."]
    return []


# ----------------------------------------------------------------------------- main
def main(argv):
    opts, err = parse_args(argv)
    if err:
        print(f"PINS FAIL: {err}")
        return 2
    source_only, verbose, tier = opts
    if not PINS.exists():
        print(f"PINS FAIL: {PINS.relative_to(ROOT).as_posix()} missing")
        return 1
    pins = load(PINS)
    bad = check_population(pins)
    if bad:
        print(f"PINS FAIL: {bad[0]}")
        for line in bad[1:]:
            print(line)
        return 1
    ok = skipped = pending = expired = failed = ran = 0
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
            ran += 1
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
    floor = MIN_RAN_SOURCE_ONLY if source_only else MIN_RAN
    if ran < floor:
        mode = f"tier={tier}{' --source-only' if source_only else ''}"
        problems.append(f"only {ran} assertion(s) actually ran for {mode} (expected >= {floor})\n"
                        "      Skipping is correct; reporting success after skipping everything is not.")
    for pr in problems:
        print(" -", pr)
    return 1 if (failed or expired or ran < floor) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
