#!/usr/bin/env python3
"""Count tests in one or more JUnit XML files.

usage: junit_count.py FILE [FILE...]
prints: total=N failed=N skipped=N
exit 2 if any FILE is missing or unparsable (a missing report must never count as zero tests).
"""
import sys
import xml.etree.ElementTree as ET


class UnreadableReport(Exception):
    """A report attribute cannot be trusted as a count.

    Raised for the same reason OSError/ParseError are: a summary-only <testsuite> that carries a
    tests=/failures=/errors=/skipped= attribute which is missing its value, non-numeric, negative, or
    implausibly large is not a parse failure at the XML level, but it is exactly as unreadable - int() on it
    would either raise a bare ValueError (a traceback, not the documented exit 2) or, for a negative or huge
    value, succeed and hand back a count that cannot exist (or that overflows a caller's arithmetic; ops/test
    accumulates these in bash `$(( ))`, which silently wraps well before Python's int would). All of these
    are corrupt-report shapes, not "zero tests".
    """


# A generous ceiling, comfortably below every shell's 32- and 64-bit signed integer range and far beyond any
# real report's test count, so a single suite can never carry a total that overflows ops/test's bash
# arithmetic accumulation into a silently wrong (and possibly negative) number.
_MAX_COUNT = 1_000_000_000


def _count_attr(el, name):
    """Read a non-negative integer count attribute (tests=, failures=, errors=, skipped=).

    An absent attribute defaults to 0 - a terse summary suite may simply omit an empty count. A present
    attribute that is not a valid, plausible non-negative integer (non-numeric, empty, negative, or larger
    than _MAX_COUNT) is not a count at all, so it is treated the same as malformed XML rather than coerced
    into one. Surrounding whitespace and a leading '+' (int("  3  ") == int("+3") == 3) are accepted: both
    are unambiguously the same non-negative integer, Python's own grammar for one, and rejecting them would
    invent a stricter format than anything a real writer has been seen to violate - unlike a negative or
    absurdly large value, there is no corruption story for them.
    """
    raw = el.get(name)
    if raw is None:
        return 0
    try:
        n = int(raw)
    except ValueError:
        raise UnreadableReport(f"{name}={raw!r} is not an integer") from None
    if n < 0:
        raise UnreadableReport(f"{name}={raw!r} is negative")
    if n > _MAX_COUNT:
        raise UnreadableReport(f"{name}={raw!r} is implausibly large (> {_MAX_COUNT})")
    return n


def _suite_counts(s):
    """Validate and read every count a summary-only <testsuite> (no <testcase> children) may carry.

    The one place count() and list_failures() both read tests=/failures=/errors=/skipped= from such a suite,
    so the two can never validate a different subset of attributes and disagree about whether the report is
    readable (T-0042: list_failures() once validated only failures=/errors=, so a bad tests= or skipped=
    made count() exit 2 while --list-failures exited 0 with no output on the identical file).

    Returns (tests, failed, skipped); failed is failures + errors.
    """
    tests = _count_attr(s, "tests")
    failed = _count_attr(s, "failures") + _count_attr(s, "errors")
    skipped = _count_attr(s, "skipped")
    return tests, failed, skipped


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
            t, f, sk = _suite_counts(s)
            total += t
            failed += f
            skipped += sk
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
            # _suite_counts() validates tests=/skipped= too, even though only the failed count is used here:
            # a bad tests= or skipped= must make this path exit 2 exactly like count() does, not silently
            # skip past unvalidated attributes and print no failures for an unreadable report (T-0042).
            _, n, _ = _suite_counts(s)
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
            except (OSError, ET.ParseError, UnreadableReport) as e:
                print(f"junit_count: cannot read {path}: {e}", file=sys.stderr)
                return 2
            for line in lines:
                print(line)
        return 0
    total = failed = skipped = 0
    for path in argv[1:]:
        try:
            t, f, s = count(path)
        except (OSError, ET.ParseError, UnreadableReport) as e:
            print(f"junit_count: cannot read {path}: {e}", file=sys.stderr)
            return 2
        total += t
        failed += f
        skipped += s
    print(f"total={total} failed={failed} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
