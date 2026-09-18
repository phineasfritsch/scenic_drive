#!/usr/bin/env python3
"""Count tests in one or more JUnit XML files.

usage: junit_count.py FILE [FILE...]
prints: total=N failed=N skipped=N
exit 2 if any FILE is missing or unparsable (a missing report must never count as zero tests).
"""
import sys
import xml.etree.ElementTree as ET


def count(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.iter("testsuite")
    total = failed = skipped = 0
    for s in suites:
        cases = list(s.iter("testcase"))
        if cases:
            total += len(cases)
            failed += sum(1 for c in cases if c.find("failure") is not None or c.find("error") is not None)
            skipped += sum(1 for c in cases if c.find("skipped") is not None)
        else:  # summary-only suite
            total += int(s.get("tests", 0))
            failed += int(s.get("failures", 0)) + int(s.get("errors", 0))
            skipped += int(s.get("skipped", 0))
    return total, failed, skipped


def list_failures(path):
    """Names of the failing testcases, so a red run says WHICH test broke.

    ops/test sent each tier's output to /dev/null and printed only a count. A CI log reading
    `TESTS linux=85/76 failed=3` with no names is the runner hiding the one fact you need; working around it
    cost a debugging round of re-running every tier by hand in containers.

    It must account for every failure `count()` counts, or the two disagree and the caller prints
    "FAIL: 1 failing test(s):" with nothing under it - which is the same defect wearing a hat. `count()` has a
    summary-only branch for a <testsuite> that carries `failures=` attributes and no <testcase> children;
    this has one too. That shape is not hypothetical: `swift test --xunit-output` writes exactly it into
    .artifacts/spm-junit.xml today (reviewer-18's finding).
    """
    root = ET.parse(path).getroot()  # OSError / ParseError propagate: an unreadable report is not "no failures"
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    out = []
    for s in suites:
        cases = list(s.iter("testcase"))
        if cases:
            for case in cases:
                for child in case:
                    if child.tag in ("failure", "error"):
                        label = ".".join(x for x in (case.get("classname"), case.get("name")) if x) or "?"
                        first = (child.get("message") or "").splitlines()
                        out.append(label + (f" - {first[0][:160]}" if first else ""))
                        break
        else:
            n = int(s.get("failures", 0) or 0) + int(s.get("errors", 0) or 0)
            if n:
                name = s.get("name") or path
                out.append(f"{name}: {n} failure(s) in a summary-only suite - the report carries no per-test "
                           f"detail, look in the tier's own log")
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "--list-failures":
        # Exits 2 on an unreadable report, exactly like the counting path. Returning 0 with no output would
        # make "cannot read the report" indistinguishable from "nothing failed".
        for path in argv[2:]:
            try:
                lines = list_failures(path)
            except (OSError, ET.ParseError) as e:
                print(f"junit_count: cannot read {path}: {e}", file=sys.stderr)
                return 2
            for line in lines:
                print(line)
        return 0
    total = failed = skipped = 0
    for path in argv[1:]:
        try:
            t, f, s = count(path)
        except (OSError, ET.ParseError) as e:
            print(f"junit_count: cannot read {path}: {e}", file=sys.stderr)
            return 2
        total += t
        failed += f
        skipped += s
    print(f"total={total} failed={failed} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
