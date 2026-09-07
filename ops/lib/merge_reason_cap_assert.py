#!/usr/bin/env python3
"""P-OPS-02's assertion, part 2 of 2. Driven by ops/lib/check-merge-reason-cap; see that file for the why.

Reads NUL-separated (label, reason, ops/merge stdout) triples on stdin as raw bytes and checks, for each one,
that the reason ops/merge echoed between its >>> <<< delimiters is exactly

    reason                          if len(reason) <= cap
    reason[:cap] + "...[truncated]" if len(reason) >  cap

where len() and the slice are in CHARACTERS. Nothing is duplicated from the driver: the expectation is derived
from the input, so a case cannot drift away from what it claims to test.

Four things fail here, and each one is a real defect rather than a style rule:
  * ops/merge emitted bytes that are not valid UTF-8   (the T-0049 defect itself)
  * the kept prefix is not the character-slice of the reason  (a byte cap, or a byte cap that backs off to a
    character boundary, both keep too little and both fail here)
  * a reason at or under the cap was altered at all     (over-eager truncation)
  * the override line is not exactly one line, or is not delimited  (regression guard on T-0044's sanitizer)

A case whose label starts with `forgery-` is checked differently: its reason is meant to be rewritten by the
sanitizer, so instead of comparing content this asserts that the `T-FAKE` sentinel it carries never became a
standalone line. That is T-0044's property, kept here because T-0049 puts python into the same pipeline.

Anti-vacuity, because each of these was found by mutating this file and watching nothing happen:
  * at least MIN_CASES cases must have run
  * at least one case where a BYTE cap would have produced invalid UTF-8 - otherwise the whole check passes on
    ASCII-only input while the defect it exists to catch is still present
  * at least one forgery- case - otherwise the "always one line" half passes with the newline collapse removed
"""
import re
import sys

# Diagnostics quote the reason, which is deliberately full of emoji and han. On Windows this script's stdout is
# cp1252 and printing those raises UnicodeEncodeError, which turned a clear failure message into a traceback
# (found by mutating away ops/merge's >>> <<< delimiters). Every message below stays ASCII by construction;
# this is the belt for the braces, and it keeps the encoding ops/lib/pins.py decodes with unchanged.
sys.stdout.reconfigure(errors="backslashreplace")

MARK = "...[truncated]"
OVERRIDE = "review gate overridden on record:"
FORGED_PREFIX = "task     T-FAKE"
# A floor, in the spirit of pins/floor_linux.txt: the driver ships 8 cases, and this refuses to certify a run
# that has quietly lost a third of them. Raise it with the suite; lowering it is a reviewer's decision.
MIN_CASES = 6


def records(blob):
    """Split the NUL-separated stream into (label, reason_bytes, stdout_bytes) triples."""
    parts = blob.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    if not parts or len(parts) % 3 != 0:
        raise SystemExit(f"P-OPS-02: driver produced {len(parts)} NUL-separated fields, expected a multiple of 3")
    return [(parts[i].decode("ascii"), parts[i + 1], parts[i + 2]) for i in range(0, len(parts), 3)]


def echoed_reason(label, out, problems):
    """The reason ops/merge actually printed, as text. None (with a problem recorded) if it cannot be read."""
    try:
        text = out.decode("utf-8")
    except UnicodeDecodeError as e:
        near = out[max(0, e.start - 4):e.start + 4].hex(" ")
        problems.append(f"{label}: ops/merge emitted invalid UTF-8 ({e.reason} at byte {e.start}); "
                        f"bytes around the split: {near}")
        return None
    hits = [ln for ln in text.splitlines() if OVERRIDE in ln]
    if len(hits) != 1:
        problems.append(f"{label}: expected exactly 1 line containing {OVERRIDE!r}, found {len(hits)}")
        return None
    m = re.search(r">>>(.*)<<<", hits[0])
    if not m:
        problems.append(f"{label}: the override line is not delimited by >>> <<<: {ascii(hits[0])}")
        return None
    return m.group(1)


def main(argv):
    cap = int(argv[1])
    cases = records(sys.stdin.buffer.read())
    if len(cases) < MIN_CASES:
        raise SystemExit(f"P-OPS-02: only {len(cases)} case(s) ran, expected at least {MIN_CASES}. "
                         "An empty or truncated case list must never read as 'the cap is character-safe'.")

    problems = []
    straddling = 0
    for label, reason_bytes, out in cases:
        # "replace" so a case can feed argv that is not valid UTF-8 at all: ops/merge has to repair such a
        # reason rather than echo the raw bytes back. That case is not caught by this comparison (which would
        # be circular - both sides would use the same decoder) but by the strict decode in echoed_reason().
        reason = reason_bytes.decode("utf-8", "replace")
        # Would a byte cap have split a character here? If no case says yes, this whole check is decorative.
        # Only reasons actually longer than cap bytes count: a short reason that is invalid UTF-8 to begin with
        # fails the same decode without saying anything about where the cap lands.
        if len(reason_bytes) > cap:
            try:
                reason_bytes[:cap].decode("utf-8")
            except UnicodeDecodeError:
                straddling += 1

        got = echoed_reason(label, out, problems)
        if got is None:
            continue

        # A `forgery-` case carries a line break plus a sentinel shaped like a real gate-1-pass line. Its reason
        # is deliberately rewritten by the sanitizer, so comparing content would be meaningless; what must hold
        # is that the sentinel never became a line of its own. (T-0044's property; see the driver's comment.)
        if label.startswith("forgery-"):
            forged = [ln for ln in out.decode("utf-8").splitlines() if ln.startswith(FORGED_PREFIX)]
            if forged:
                problems.append(f"{label}: operator text became {len(forged)} standalone gate line(s): "
                                f"{ascii(forged[0])}")
            continue

        want = reason if len(reason) <= cap else reason[:cap] + MARK
        if got != want:
            kept = got[:-len(MARK)] if got.endswith(MARK) else got
            problems.append(
                f"{label}: reason is {len(reason)} characters / {len(reason_bytes)} bytes; ops/merge kept "
                f"{len(kept)} characters ({len(kept.encode('utf-8'))} bytes)"
                f"{' plus ' + MARK if got.endswith(MARK) else ''}, expected "
                f"{min(len(reason), cap)} characters"
                f"{' plus ' + MARK if len(reason) > cap else ' and no truncation marker'}")

    if straddling == 0:
        problems.append(f"no case puts a multi-byte character across byte {cap}, so this check would pass "
                        "even with the byte-counting cap it exists to catch")
    forgeries = sum(1 for label, _, _ in cases if label.startswith("forgery-"))
    if forgeries == 0:
        problems.append("no case feeds a line break plus a forged gate line, so the 'always one line' half of "
                        "this pin would pass even with the sanitizer's newline collapse removed")

    if problems:
        print("P-OPS-02: ops/merge's --no-task-reason cap is not character-safe:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"P-OPS-02: ops/merge caps --no-task-reason at {cap} characters on a character boundary "
          f"({len(cases)} cases: {straddling} straddling byte {cap}, {forgeries} forgery attempts; "
          f"every override line valid UTF-8 and a single line)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
