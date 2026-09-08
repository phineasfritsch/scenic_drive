#!/usr/bin/env python3
"""Classify a GitHub statusCheckRollup into pending / passed / failed. Fail-CLOSED by construction.

Reads the rollup JSON on argv[1], prints three lines:

    total=<n>
    pending=<n>
    failed=<comma-separated names, empty if none>

WHY THIS EXISTS. The first version of ops/merge inlined three python one-liners and asked "is the conclusion
in my list of bad ones?". That is fail-OPEN: SKIPPED, NEUTRAL, STALE, a lowercase "success", or any status
GitHub invents next year is neither pending nor failed, so the gate proceeds. reviewer-11 also found that a
check record with no `name` crashed the one-liner with KeyError, and because the crash was swallowed by the
shell substitution the result was `failed=""` - a genuine FAILURE printing "every gate passed".

So: SUCCESS is the ONLY passing conclusion. Everything not explicitly pending is failed. An unrecognised
conclusion is failed, a malformed record is failed, and a parse error exits non-zero rather than printing an
empty answer that reads like good news.
"""
import json
import sys

PENDING = {"PENDING", "IN_PROGRESS", "QUEUED", "WAITING", "REQUESTED", "EXPECTED", ""}
PASSING = {"SUCCESS"}  # deliberately the only one


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: classify-checks.py '<rollup json>'", file=sys.stderr)
        return 2
    try:
        rollup = json.loads(argv[1])
    except Exception as e:
        print(f"classify-checks: cannot parse rollup ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    if not isinstance(rollup, list):
        print("classify-checks: rollup is not a list", file=sys.stderr)
        return 2

    pending = 0
    failed: list[str] = []
    for i, entry in enumerate(rollup):
        if not isinstance(entry, dict):
            failed.append(f"<malformed check #{i}>")
            continue
        # A check with no usable name is still a check. Never drop it, and never let the lookup raise:
        # a nameless FAILURE that vanishes is worse than one with an ugly label.
        name = entry.get("name") or entry.get("context") or f"<unnamed check #{i}>"
        conclusion = (entry.get("c") or entry.get("conclusion") or entry.get("state") or "")
        conclusion = str(conclusion).strip().upper()
        if conclusion in PENDING:
            pending += 1
        elif conclusion in PASSING:
            continue
        else:
            failed.append(f"{name}({conclusion or 'NO_CONCLUSION'})")

    print(f"total={len(rollup)}")
    print(f"pending={pending}")
    print(f"failed={','.join(failed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
