#!/usr/bin/env python3
"""P-OPS-02's assertion, part 2 of 2. Driven by ops/lib/check-merge-reason-cap; see that file for the why.

Reads NUL-separated (label, expectation, exit code, reason, ops/merge stdout) records on stdin as raw bytes.
Three things are asserted of EVERY case, whatever it claims to test:

  * ops/merge's stdout is valid UTF-8                     (the T-0049 defect itself)
  * it splits into exactly as many lines under str.splitlines() as ops/merge itself wrote newlines - i.e. the
    operator's text did not start a line via U+0085, U+2028, U+2029 or a stray CR   (T-0049 / reviewer-39)
  * no line of it is a forged gate line: `task<spaces>T-FAKE...`, where <spaces> counts U+00A0 and friends,
    because NBSP rebuilds the 5-space column of a real gate-1-pass line and no `tr` in the pipeline sees it

and then, per the case's expectation:

  derive     the echoed reason must be exactly `reason` if len(reason) <= cap, else `reason[:cap] + MARK`,
             with len() and the slice in CHARACTERS. Derived from the input, so a case cannot drift away from
             what it claims to test. Also: the echoed reason must contain no C0 control, DEL, U+0085, U+2028
             or U+2029 - that is what guards the ESC/ANSI strip and the line-separator fold.
  is:<text>  the echoed reason must be exactly <text>. For inputs the sanitizer is MEANT to rewrite, where
             there is nothing to derive: stating the post-sanitizing text pins HOW it was rewritten (a space
             and not a deletion, one space and not five, the ESC byte gone but its payload text kept).
  refuse     ops/merge must exit 1, print MERGE REFUSED, and record no override line at all - the rule that a
             reason of nothing but whitespace and control bytes is no reason.

Anti-vacuity, because every one of these was found by mutating something and watching nothing happen:
  * at least MIN_CASES cases must have run
  * a case where a BYTE cap would produce invalid UTF-8 - else the check passes on ASCII while the defect it
    exists to catch is still present
  * a case whose reason contains LF or CR                 (else T-0044's newline collapse has no guard)
  * a case whose reason contains U+0085/U+2028/U+2029     (else this pin's "exactly one line" claim is again
    broader than what it tests - the T-0049 review FAIL)
  * a case carrying U+000B, U+000C and U+001C-U+001E      (the other five breaks splitlines() honours; step 2
    deletes them as control bytes, but a claim about lines has to cover every code point that makes one)
  * a case whose reason contains ESC                      (else T-0044's ANSI strip has no guard)
  * a case carrying the T-FAKE gate-line sentinel         (else nothing notices a promoted gate line)
  * a case that must be refused                           (else "empty reason means refuse" has no guard)
  * a case with a precomposed character                   (else a silent NFD rewrite of the record passes)
  * a case where folding a break to a space makes a run of spaces or a leading/trailing one (else the repeat
    of the collapse-and-trim after the fold is unreachable and could be deleted unnoticed)
"""
import re
import sys
import unicodedata

# Diagnostics quote the reason, which is deliberately full of emoji and han. On Windows this script's stdout is
# cp1252 and printing those raises UnicodeEncodeError, which turned a clear failure message into a traceback
# (found by mutating away ops/merge's >>> <<< delimiters). Every message below stays ASCII by construction;
# this is the belt for the braces, and it keeps the encoding ops/lib/pins.py decodes with unchanged.
sys.stdout.reconfigure(errors="backslashreplace")

MARK = "...[truncated]"
OVERRIDE = "review gate overridden on record:"
REFUSAL = "MERGE REFUSED: branch "
# The head of a gate-1-pass line. The column is any run of space-ish characters, not five ASCII spaces: U+00A0
# and the other Unicode spaces pass through the sanitizer untouched and render identically.
FORGED = re.compile("^task[ \t\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+T-FAKE")
# None of these may reach the override line: C0 controls, DEL, and the three line breaks `tr` cannot see.
BANNED = re.compile("[\x00-\x1f\x7f\u0085\u2028\u2029]")
BREAKS_ASCII = ("\n", "\r")
BREAKS_UNICODE = ("\u0085", "\u2028", "\u2029")
# The rest of what str.splitlines() honours. These are C0 controls, so ops/merge deletes them at step 2 rather
# than folding them - but they are line breaks to the same reader, so the case list has to feed them too.
BREAKS_DELETED = ("\v", "\f", "\x1c", "\x1d", "\x1e")
# A break next to a space, at either end of the reason, or doubled: folding it to a space makes whitespace that
# the collapse-and-trim has to run over a second time. Asked of the INPUT only - nothing here re-implements the
# pipeline, it just refuses to certify a case list that cannot reach that step.
RECOLLAPSE = re.compile("(?:^|[ \t])[\u0085\u2028\u2029]|[\u0085\u2028\u2029](?:[ \t]|$)"
                        "|[\u0085\u2028\u2029]{2}")
FIELDS = 5
# A floor, in the spirit of pins/floor_linux.txt: the driver ships 15 cases, and this refuses to certify a run
# that has quietly lost a quarter of them. Raise it with the suite; lowering it is a reviewer's decision.
MIN_CASES = 12


def records(blob):
    """Split the NUL-separated stream into (label, expectation, rc, reason_bytes, stdout_bytes) records."""
    parts = blob.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    if not parts or len(parts) % FIELDS != 0:
        raise SystemExit(f"P-OPS-02: driver produced {len(parts)} NUL-separated fields, "
                         f"expected a multiple of {FIELDS}")
    return [(parts[i].decode("ascii"), parts[i + 1].decode("utf-8"), parts[i + 2].decode("ascii"),
             parts[i + 3], parts[i + 4]) for i in range(0, len(parts), FIELDS)]


def echoed_reason(label, text, problems):
    """The reason ops/merge actually printed, as text. None (with a problem recorded) if it cannot be read."""
    hits = [ln for ln in text.splitlines() if OVERRIDE in ln]
    if len(hits) != 1:
        problems.append(f"{label}: expected exactly 1 line containing {OVERRIDE!r}, found {len(hits)}")
        return None
    m = re.search(r">>>(.*)<<<", hits[0])
    if not m:
        problems.append(f"{label}: the override line is not delimited by >>> <<<: {ascii(hits[0])}")
        return None
    return m.group(1)


def check_shape(label, text, problems):
    """The two properties that hold for every case: one line per newline, and no forged gate line."""
    wrote = text.count("\n") + (0 if text.endswith("\n") else 1)
    lines = text.splitlines()
    if len(lines) != wrote:
        problems.append(f"{label}: ops/merge wrote {wrote} line(s) but its output splits into {len(lines)} "
                        f"under Unicode line-break rules - operator text started a line "
                        f"(U+0085, U+2028, U+2029 or a stray CR)")
    forged = [ln for ln in lines if FORGED.match(ln)]
    if forged:
        problems.append(f"{label}: operator text became {len(forged)} standalone gate line(s): "
                        f"{ascii(forged[0])}")


def check_cap(label, cap, reason, reason_bytes, got, problems):
    """The T-0049 property: the kept prefix is the CHARACTER slice of the reason."""
    want = reason if len(reason) <= cap else reason[:cap] + MARK
    if got == want:
        return
    kept = got[:-len(MARK)] if got.endswith(MARK) else got
    problems.append(
        f"{label}: reason is {len(reason)} characters / {len(reason_bytes)} bytes; ops/merge kept "
        f"{len(kept)} characters ({len(kept.encode('utf-8'))} bytes)"
        f"{' plus ' + MARK if got.endswith(MARK) else ''}, expected "
        f"{min(len(reason), cap)} characters"
        f"{' plus ' + MARK if len(reason) > cap else ' and no truncation marker'}")


def main(argv):
    cap = int(argv[1])
    cases = records(sys.stdin.buffer.read())
    if len(cases) < MIN_CASES:
        raise SystemExit(f"P-OPS-02: only {len(cases)} case(s) ran, expected at least {MIN_CASES}. "
                         "An empty or truncated case list must never read as 'the cap is character-safe'.")

    problems = []
    straddling = 0
    seen = dict.fromkeys(("lf-cr", "unicode-break", "deleted-break", "esc", "sentinel", "refuse",
                          "precomposed", "recollapse"), 0)

    for label, want_spec, rc, reason_bytes, out in cases:
        # "replace" so a case can feed argv that is not valid UTF-8 at all: ops/merge has to repair such a
        # reason rather than echo the raw bytes back. That case is not caught by this comparison (which would
        # be circular - both sides would use the same decoder) but by the strict decode below.
        reason = reason_bytes.decode("utf-8", "replace")
        # Would a byte cap have split a character here? If no case says yes, this whole check is decorative.
        # Only reasons actually longer than cap bytes count: a short reason that is invalid UTF-8 to begin with
        # fails the same decode without saying anything about where the cap lands.
        if len(reason_bytes) > cap:
            try:
                reason_bytes[:cap].decode("utf-8")
            except UnicodeDecodeError:
                straddling += 1
        seen["lf-cr"] += any(c in reason for c in BREAKS_ASCII)
        seen["unicode-break"] += any(c in reason for c in BREAKS_UNICODE)
        seen["deleted-break"] += all(c in reason for c in BREAKS_DELETED)
        seen["esc"] += "\x1b" in reason
        seen["sentinel"] += "T-FAKE" in reason
        seen["refuse"] += want_spec == "refuse"
        seen["precomposed"] += unicodedata.normalize("NFD", reason) != reason
        seen["recollapse"] += bool(RECOLLAPSE.search(reason))

        try:
            text = out.decode("utf-8")
        except UnicodeDecodeError as e:
            near = out[max(0, e.start - 4):e.start + 4].hex(" ")
            problems.append(f"{label}: ops/merge emitted invalid UTF-8 ({e.reason} at byte {e.start}); "
                            f"bytes around the split: {near}")
            continue

        check_shape(label, text, problems)

        if want_spec == "refuse":
            if rc != "1":
                problems.append(f"{label}: ops/merge exited {rc}; a reason that sanitizes to nothing is no "
                                "reason at all and gate 1 must refuse (exit 1)")
            if REFUSAL not in text:
                problems.append(f"{label}: ops/merge did not refuse; {REFUSAL!r} is absent from its output")
            if ">>>" in text:
                problems.append(f"{label}: ops/merge recorded an override for a reason that sanitized away: "
                                f"{ascii(text)}")
            continue

        if rc != "0":
            problems.append(f"{label}: ops/merge exited {rc}, expected 0 under the gh stub; "
                            f"its output was {ascii(text)}")
            continue

        got = echoed_reason(label, text, problems)
        if got is None:
            continue
        bad = BANNED.search(got)
        if bad:
            problems.append(f"{label}: the override line carries U+{ord(bad.group()):04X}, which sanitizing "
                            "must have removed (a C0 control, DEL, or a line break tr cannot see)")

        if want_spec == "derive":
            check_cap(label, cap, reason, reason_bytes, got, problems)
        elif want_spec.startswith("is:"):
            if got != want_spec[3:]:
                problems.append(f"{label}: the sanitizer rewrote the reason to {ascii(got)}, "
                                f"expected {ascii(want_spec[3:])}")
        else:
            problems.append(f"{label}: unknown expectation {want_spec!r} (want derive, refuse or is:<text>)")

    if straddling == 0:
        problems.append(f"no case puts a multi-byte character across byte {cap}, so this check would pass "
                        "even with the byte-counting cap it exists to catch")
    for key, why in (
        ("lf-cr", "no case feeds a reason containing LF or CR, so T-0044's newline collapse has no guard"),
        ("unicode-break", "no case feeds a reason containing U+0085, U+2028 or U+2029 - the three line breaks "
                          "`tr` cannot see - so this pin's 'exactly one line' claim would again be broader "
                          "than what it tests"),
        ("deleted-break", "no single case feeds all of U+000B, U+000C and U+001C-U+001E, the five breaks "
                          "str.splitlines() honours that step 2 deletes rather than folds, so the 'exactly one "
                          "line' claim covers code points this check never sends"),
        ("esc", "no case feeds an ESC byte, so T-0044's ANSI-escape strip has no guard"),
        ("sentinel", "no case carries the T-FAKE sentinel, so nothing here notices operator text being "
                     "promoted to a line shaped like one of ops/merge's own gate lines"),
        ("refuse", "no case feeds a reason that sanitizes to nothing, so 'an empty reason refuses the merge' "
                   "is untested and the override line could be recorded blank"),
        ("precomposed", "no case feeds a precomposed character, so a filter that silently NFD-normalizes the "
                        "operator's text on its way to the permanent record would pass"),
        ("recollapse", "no case puts a line break next to a space, at an end of the reason, or doubled, so "
                       "folding it to a space never produces whitespace to re-collapse and the repeat of the "
                       "collapse-and-trim after the fold could be deleted unnoticed"),
    ):
        if seen[key] == 0:
            problems.append(why)

    if problems:
        print("P-OPS-02: ops/merge's --no-task-reason override line is not what this pin claims:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"P-OPS-02: ops/merge caps --no-task-reason at {cap} characters on a character boundary and its "
          f"override line is always valid UTF-8 and exactly one line ({len(cases)} cases: {straddling} "
          f"straddle byte {cap}, {seen['sentinel']} forge a gate line, {seen['unicode-break']} use a line "
          f"break tr cannot see, {seen['esc']} carry ESC, {seen['refuse']} must be refused)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
