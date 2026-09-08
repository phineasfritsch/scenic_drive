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
touches: [ops/lib/check-self-referential-tests.py, ops/lib/check-self-referential-cases.py, ops/lib/check-self-referential-history.py, ops/check-tests, pins/PINS.yaml, Tests/ScenicKitTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/check-tests -> SELF-REF OK, exit 0"
  - "ops/check-tests --cases -> SELF-REF CASES OK (19 cases), exit 0"
  - "ops/check-tests --history -> SELF-REF HISTORY OK (2 commit pairs), exit 0"
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

---

## Fix pass: reviewer-pr77 found that the check has the defect it exists to catch, in three places

Ten findings. The three that matter most are not false negatives - they are the check being green on
nothing, which is the class it was written to close.

### 1. The history demonstration decayed into a green (BLOCKING)

`.artifacts/against-history.py` anchored on `origin/task/T-0116~1` - **a moving branch tip**. The branch
advanced, `~1` became the fix commit, and the transcript in the Log stopped reproducing. It was true when
written and false a few hours later. The substance survived at the fixed sha `10c2c5a`, which the reviewer
checked.

Worse: `main()` did `continue` on an unreadable ref **without setting `ok = False`**, so pointed at a
branch that did not exist it printed `AGAINST HISTORY OK` and exited 0 having demonstrated nothing. Had the
branch been deleted rather than advanced, the decay would have been silent.

And `.artifacts/` is gitignored, so the PR's headline "stronger demonstration" shipped nowhere and nobody
could re-run it - the same defect the fourth finding of the FIRST review already made about the mutation
harness, repeated one file over.

Now `ops/lib/check-self-referential-history.py`: tracked, every commit pinned by full SHA, a SKIP is a
FAILURE, and each before-run must NAME the expected finding rather than merely exit 1. Wired in as
`ops/check-tests --history`.

    before 245d5418ebf1: exit 1, naming LearnedCorridorSpeeds.minRatio AND maxRatio
    after  d8d15e2     : exit 0
    before 10c2c5a     : exit 1, three `out.duration vs out.ceiling`
    after  b1be8cc     : exit 0

### 2. A traceback read as a successful catch (BLOCKING)

`--cases` used `fired = code == 1`, and a traceback is exit 1. The reviewer replaced the matcher body with
`raise` and **all six RED cases reported `ok RED`**. The suite failed only because the negative half caught
it. A catch now requires `SELF-REF FAIL` in the output AND the expected finding text.

### 3. The floor counted the wrong population (BLOCKING)

`MIN_TEST_FILES` counts files PRESENT. Three files containing no assertions cleared it - and two of this
check's own three scaffold files were a single comment line. **That is the identical defect this task's own
Brief indicts in `ops/lib/check-review-remedy`**: "counts case blocks ENTERED, not assertions EXECUTED".

`MIN_ASSERTIONS = 10` now floors the assertions actually examined, and the OK line reports it:
`SELF-REF OK (31 assertions in 4 test files, 5 types under Sources/)`. The scaffold gained real assertions
rather than the floor being lowered to fit it.

### 4. The escape hatch promised more than it enforced

The docstring said the reason "must be more than a word" and nothing inspected it: a single character
silenced a real finding, and a bare `// self-ref-ok:` with no reason survived a mutation of that very line.
`ALLOW` now requires two words. And `ALLOW.search(raw)` ran BEFORE `strip_comment`, so the marker inside a
Swift **string literal** silenced the line; suppression is now decided on the trailing comment, anchored at
its start, and only for lines that are actually assertions. The count is printed, because an unqualified
"OK" over a tree with silenced findings is the same shape as a green over an empty one.

### 5. The case crediting the function-call exclusion was vacuous

`Geo` was not among the scaffold's declared types, so rule A never reached the lookahead: green with it,
green without it. The first of the three "defects found by running it" had a test that could not fail.
`Geo` is now declared.

### 6. Four false positives, three on shapes the remedy text recommends

`== .5`, `== .infinity` and `== ["a","b"]` were all flagged, because `LITERAL` accepted only
decimal/hex/quoted-string/bool/nil, and because the right-hand operand was matched with a character class
that cannot span `["a", "b"]`. A check that flags its own advice is a check that gets switched off. The RHS
is now taken as the rest of the line and `LITERAL` covers leading-dot floats, enum cases and collection
literals.

Rule C had no `\b` after MEMBER, so the engine backtracked one character to satisfy the lookahead and
reported `LambdaSearch.stepCoun` - a symbol that does not exist. That is the third "defect found by running
it" still live in the rule the original fix did not reach.

### 7. Nine false negatives, now written down

The Brief admitted one. The reviewer found eight more, including **the most natural way to write the
defect** - a function call on the left, `#expect(Geo.distanceMeters(a,b) <= Geo.earthRadiusMeters)`. All
nine are listed in the check's own docstring, and P-TEST-02's statement is narrowed from "No assertion" to
"No assertion **of the three recognised shapes**", with the scope caveat carried in the pin itself.

A check whose stated scope quietly exceeds its real one is the defect it exists to prevent.

### What did NOT change, and why the check is still worth having

It found three real instances in `LambdaSearchTests.swift` that a person had already been told about, in
that exact file, in the same sitting, and still could not see. That is the argument, and it is unaffected by
any of the above.

    bash ops/check-tests            SELF-REF OK (31 assertions in 4 test files)   exit 0
    bash ops/check-tests --cases    SELF-REF CASES OK (19 cases)                  exit 0
    bash ops/check-tests --history  SELF-REF HISTORY OK (2 commit pairs)          exit 0

