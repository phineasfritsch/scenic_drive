---
id: T-0120
title: a check for the defect this repo keeps shipping: an assertion whose expected value comes from the thing it checks
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T16:09:08Z
lease_expires_at: 2026-09-08T18:09:08Z
worktree: .worktrees/T-0120
branch: task/T-0120
exclusive: []
touches: [ops/lib/check-self-referential-tests.py, ops/lib/check-self-referential-cases.py, ops/check-tests, pins/PINS.yaml, Tests/ScenicKitTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/check-tests -> SELF-REF OK, exit 0"
  - "ops/check-tests --cases -> SELF-REF CASES OK (12 cases), exit 0"
  - "RED: adding one self-referential assertion to a real test file makes ops/check-tests exit 1 and ops/check-pins name P-TEST-02"
---
## Brief

**In one session this defect was found eight times by six different reviewers, and four of those were inside
tests written specifically to close a previous instance of it.**

    #expect(r2 <= LearnedCorridorSpeeds.maxRatio)              maxRatio 1.0 -> 3.0 stayed green, and a
                                                               learned corridor then returned an ETA BELOW
                                                               the free-flow it was handed, badge off
    #expect(out.duration <= out.ceiling)                       both sides from the code under test; a
                                                               mutated ceiling was invisible
    for n in 1..<LearnedCorridorSpeeds.confidenceThreshold     an empty range at 1; the test for a product
                                                               invariant passed over zero iterations
    #expect(pinned.count == AppleMapsDirections.maxWaypoints)  9 -> 99 was green
    #expect(cN.y == cE.x)                                      the two offsets cancelled the function under
                                                               test, so it held for any definition
    #expect(abs(pieces.p90 - whole.p90) < 1e-9)                asserted consistency, never correctness

The pattern is not carelessness. It is that the shape is invisible from the inside: when you have just
written `maxRatio = 1.0`, writing `#expect(r <= maxRatio)` reads like a check of the clamp. Every one of
these was written by an agent that had just been told about the defect, in several cases in the same file
and the same sitting.

So the response is not another instruction. It is a check.

## Log

    bash ops/check-tests                 SELF-REF OK (4 test files, 5 types under Sources/)   exit 0
    bash ops/check-tests --cases         SELF-REF CASES OK (12 cases)                          exit 0
    bash ops/check-pins                  PINS ok=11 (was 10), P-TEST-02 green                  exit 1*

    * the one failure is P-OPS-02, pre-existing and identical on clean main - a bash `mktemp -d` path that
      Windows python cannot read. Not introduced here and not folded into this task.

### What it detects, and what it does not

Three shapes, chosen because they are recognisable from the token stream without dataflow:

  A. a comparison against `Type.member` where `Type` is declared under `Sources/` and the other side is not
     a literal - true for any value the constant takes;
  B. `x.a <op> x.b` - one receiver supplying both the expected value and the actual one;
  C. a range bound taken from such a member - lower the constant and the loop body stops running.

**Not detected, and said out loud:** two DIFFERENT objects both produced by the code under test
(`pieces.p90` against `whole.p90`) needs dataflow. The sixth instance above is invisible to this check. A
check that claimed to cover it would be this repository's signature defect one level up.

### RED, on the real files rather than on copies

`ops/check-tests --cases` runs twelve cases through a scaffold: six shapes copied verbatim from assertions
that actually shipped (all must fire) and six that look similar and are legitimate (none may fire) -
pinning a constant against a LITERAL, a metamorphic symmetry property, a value against a literal, the
two-receiver shape this check does not cover, an allowlisted line, and a constant mentioned only in a
comment. Plus the floor: an empty tree refuses rather than passing.

`.artifacts/against-history.py` is the stronger demonstration. It reconstructs the ACTUAL pre-fix and
post-fix commits from git and runs the check over them:

    T-0118  before origin/task/T-0118~1 : exit 1, naming LearnedCorridorSpeeds.minRatio AND maxRatio
            after  origin/task/T-0118   : exit 0
    T-0116  before origin/task/T-0116~1 : exit 1, three `out.duration vs out.ceiling`
            after  origin/task/T-0116   : exit 0

It found BOTH clamp constants on T-0118, where the human reviewer had rated `minRatio` non-blocking.

### The check found three instances I could not, in its first real run

After a reviewer named this defect in `LambdaSearchTests.swift`, I fixed `ceilingAlwaysHolds` by hand and
wrote a commit message describing the problem at length. **Three identical assertions survived in the same
file**, at lines 161, 180 and 204. The check found them immediately. They are fixed on `task/T-0116`
(commit b1be8cc).

That is the argument for this task in one line, and it is a measurement rather than a claim.

### Three defects in the check itself, each found by running it rather than reading it

  * It flagged `#expect(Geo.distanceMeters(a, b) == Geo.distanceMeters(b, a))` in the existing suite. That
    is a metamorphic symmetry property and it is a good test. Comparing the code against ITSELF is fine;
    comparing it against a CONSTANT OF ITS OWN is the defect. The member pattern now excludes function calls.
  * `COMPARISON` had a capture group, so the same-object rule reported `out.duration vs out.<=` - the match
    was right and the message was nonsense, which is how a check gets ignored.
  * The operand pattern included parentheses, so `#expect(X.y == 1.0)` captured `1.0)` as the right-hand
    side, failed the literal test, and flagged the CORRECT pinning shape.

### And one in the wrapper, which is the repository's own recurring Windows hazard

`ops/check-tests` first exited 2 with

    can't open file 'C:\c\Users\phineasf\...\check-self-referential-tests.py'

`pwd` in git-bash yields `/c/Users/...`, and the Windows python interpreter reads that as a relative path.
It is now translated with `cygpath` when that exists. The wrapper locates itself from `BASH_SOURCE` rather
than `git rev-parse --show-toplevel`, which CLAUDE.md and T-0060 ban under `ops/` because WSL cannot follow
this checkout's `gitdir:` file - T-0093 records fifteen call sites that still do it, and this is not the
sixteenth.

### The escape hatch, and why it demands a sentence

A line ending `// self-ref-ok: <reason>` is skipped. The reason is required, because an allowlist whose
entries need no argument is a switch for turning the check off.

### Floors

`MIN_TEST_FILES = 3` and `MIN_TYPES = 3`. A check that iterates over an empty tree exits 0 and proves
nothing - which is the defect this file is about, one level up. Demonstrated red: an empty tree refuses.

When `against-history.py`'s scaffold hit the type floor, the scaffold was padded rather than the floor
lowered. Lowering it would have been the check bending to accommodate its own test.

### Scope: this covers Swift tests only, and the defect is not confined to them

Recorded while this task was being written, from a review of PR #52: `ops/lib/check-review-remedy` - a bash
check added specifically because a destructive remedy survived two reviews - contains two assertions that
cannot fail.

  * Its case-1 assertion is `grep -q "blocked" "$out"`, and `$out` always contains the fixture's own
    `queue/blocked/...` path in the `dup` listing earlier in the same output. Satisfied by the fixture's own
    path string, never by the guard naming main's state. A reviewer demonstrated a false `ok` against a
    mutant that reintroduces the impossible remedy.
  * Its floor counts `cases`, incremented by unconditional straight-line code with no `set -e`, no
    `continue` and no early `exit` between the increments - so reaching the floor means `$cases` is exactly
    4, always. It counts case blocks ENTERED, not assertions EXECUTED: the wrong population, the same shape
    as the `find`-based assertions this repository already replaced in P-SRC-02 and P-OPS-01.

That is the ninth instance in one session, inside a check written to catch this class.

**`ops/check-tests` would not have found either**, because it reads Swift. The bash checks under `ops/lib/`
are the other half and are not covered. Saying so is the point: a check whose stated scope quietly exceeds
its real one is the defect it exists to prevent. A follow-up should do for the bash checks what this does
for the Swift suites - the shapes there are different (a grep whose pattern the fixture always satisfies, a
counter incremented unconditionally) and need their own recogniser, not a wider regex.

