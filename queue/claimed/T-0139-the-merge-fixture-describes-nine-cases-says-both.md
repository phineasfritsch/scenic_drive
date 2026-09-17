---
id: T-0139
title: the merge fixture describes nine cases, says both diffs fail when one does, and reports OK over an empty case list
state: claimed
owner: agent/claude-opus-5
owner_session: 012vL7Yk1ov7eNxoFD9U6Pfm
claimed_at: 2026-09-16T05:40:00Z
lease_expires_at: 2026-09-16T11:40:00Z
worktree: .worktrees/T-0139
branch: task/T-0139
exclusive: []
touches: [.githooks/pre-commit, ops/lib/check-touches-merge.py, pins/PINS.yaml]
pins_affected: [P-GIT-02, P-GIT-03]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/lib/check-touches-merge.py -> TOUCHES-MERGE OK (11 cases), exit 0"
  - "python ops/lib/check-touches-merge.py --variants -> TOUCHES-MERGE VARIANTS OK (6): --no-renames HEAD side->11, MERGE_HEAD side->5,11, error fallback->8, literal .git/MERGE_HEAD->9, fallback message->8, narrowing message->2, exit 0"
  - "RED (N2, the HEAD-side --no-renames): before case 11 existed, removing --no-renames from the HEAD diff alone left all ten cases green; now the HEAD-side variant breaks exactly 11"
  - "RED (N3): a copy of the fixture with case 6's setup guard inverted ('if rc == 0'), --variants -> FAIL variant ... case setup died for 6; nothing was judged, on every variant, exit 1"
  - "RED (N4): a copy with case 11's builder swapped for case_resolution_outside under case 11's label -> TOUCHES-MERGE REFUSING: duplicate case labels or builders, exit 2"
  - "RED (NB2, round 3): a copy with ('decorative', '#!/', '#!/', set()) appended to VARIANTS and MIN_VARIANTS 7, --variants -> TOUCHES-MERGE REFUSING: variant 'decorative' changes nothing or expects nothing to break, exit 2"
  - "RED (vacuity), each with --hook .githooks/pre-commit: CASES=CASES[:0] -> REFUSING: 0 cases defined, MIN_CASES says 11, exit 2; VARIANTS=VARIANTS[:0] -> REFUSING: 0 variants defined, MIN_VARIANTS says 6, exit 2"
  - "RED (round 1, the message assertion), before run_variants and main were unified: the fallback-message variant broke NOTHING, TOUCHES-MERGE VARIANTS FAIL, exit 1"
  - "bash ops/check-pins -> PINS ok=15 skipped=0 pending=3 expired=0 failed=0 tier=linux, exit 0; --source-only -> PINS ok=6 skipped=11 pending=1 ... (P-GIT-03 is anchor: process now, so it no longer runs in the source-only tier)"
  - "bash ops/queue-check -> QUEUE OK, exit 0"
---
## Brief

Filed from agent/rv-pr84's review of PR #84 (T-0137), which PASSED with six non-blocking findings. This
closes four of them, plus a fifth found while closing the third.

1. `.githooks/pre-commit`, the fixture's module and case-8 docstrings, the T-0137 Brief, Log and PR body all
   say the gate fails "when BOTH git calls fail". Measured: `head_rc=0 merge_rc=128`. Only the MERGE_HEAD
   diff fails; an intersection is empty as soon as either side is. The code (`||`) is right and more general
   than its own description; a hook implementing the sentence would be `&&` and turns case 8 red.
2. The fixture's module docstring still says "Nine cases" and lists case 9 as must REFUSE - the version
   T-0137's own Log records rewriting because it could not fail.
3. The fallback's operator message is asserted by no case: deleting both `echo`s leaves all ten green,
   while PR #84 advertised "and says so on stdout".
4. `CASES = []` -> `TOUCHES-MERGE OK (0 cases)`, exit 0; `VARIANTS = []` -> `VARIANTS OK (0)`, exit 0. The
   pin reads only the exit code. Pre-existing from PR #78, in the file whose own docstring cites "the
   mutation harnesses refuse on an empty population".
5. (Found while fixing 3.) `run_variants` judged a case on its exit code alone while `main()` also checked
   the reason string, so a variant silencing an asserted message broke nothing in the sweep's eyes.

## Log
- 2026-09-16T05:40:00Z claimed by agent/claude-opus-5 off `98725ec` (PR #84 merged). Filed from
  agent/rv-pr84's review of PR #84, which PASSED with six non-blocking findings; this closes four of them.
  `ops/new-task` allocated **T-9902 again** - the second time tonight - so this file was renamed by hand.
  That is [[T-0138]]'s second half, still live, and this is its second reproduction.
- 2026-09-16T06:20:00Z **Four findings closed, and closing one of them found a fifth that nothing had ever
  looked at.**

  **1. The mechanism was mis-stated everywhere, and the code was right.** Every copy of the sentence said
  the gate fails "when BOTH git calls fail". Instrumented (a copy of the hook with
  `echo "PROBE head_rc=$head_rc merge_rc=$merge_rc"` before the branch, run under case 8):

      PROBE head_rc=0 merge_rc=128

  The diff against HEAD SUCCEEDS; only `MERGE_HEAD` is unresolvable. An intersection is empty as soon as
  EITHER side is, so one failing call is enough. The shipped code uses `||` and is therefore correct and
  strictly more general than its own description - a hook implementing the sentence would be `&&`, would
  never fire here, and turns case 8 red. Corrected in `.githooks/pre-commit`, the module docstring, case
  8's docstring, and the Log; the corrected text says what was measured and what it used to say, so nobody
  re-derives the wrong version from the old wording.

  **2. The module docstring still described the version that could not fail.** It said "Nine cases" and
  listed case 9 as *"the same merge, run inside a LINKED WORKTREE - must REFUSE"*, with no case 10, and the
  VARIANTS comment still said "what makes the seven discriminating". That is precisely the case T-0137's
  Log records rewriting BECAUSE it could not fail - the file was shipping both the fix and the description
  of the defect. Now ten, with the reason the pair is split stated where the cases are listed.

  **3. The operator message was advertised and asserted by nothing.** PR #84 said the gate "says so on
  stdout"; deleting both `echo` statements left all ten cases green. `must_say` now accepts several phrases
  and is checked in BOTH directions (a must-COMMIT case can assert a message too), case 8 asserts the
  fallback line as well as the refusal, case 2 asserts the narrowing line, and a fourth variant deletes the
  message. RED for that variant, before the next finding was fixed: *it broke nothing.*

  **4. ...because `run_variants` had its OWN, WEAKER idea of what "broken" means.** It compared only the
  exit code:

      code, _ = fn(repo)
      if code != 99 and (code == 0) != must_commit:

  while `main()` also checked the reason string. So a variant that silenced an asserted MESSAGE broke
  nothing in the variant sweep's eyes while breaking a case in the suite's. Two judges, one file. Both now
  call `case_verdict()`, the single place a case is judged. This is the fifth finding, found only by adding
  a variant that the old sweep could not see - and it is the same shape as everything else here: a check
  whose stated scope exceeds its coverage.

  **5. Vacuity, inherited from PR #78.** `CASES = []` printed `TOUCHES-MERGE OK (0 cases)`, exit 0;
  `VARIANTS = []` printed `TOUCHES-MERGE VARIANTS OK (0)`, exit 0. `pins/PINS.yaml:162` reads only the exit
  code, so an emptied case list kept P-GIT-02 green over a fixture measuring nothing - in the file whose own
  case-8 docstring cites *"the mutation harnesses refuse on an empty population"* as the standard. RED, each
  against the real hook:

      CASES = CASES[:0]          -> TOUCHES-MERGE REFUSING: 0 cases defined, MIN_CASES says 10 ...   exit 2
      VARIANTS = VARIANTS[:0]    -> TOUCHES-MERGE REFUSING: 0 variants defined, MIN_VARIANTS says 4  exit 2
      CASES = CASES + [CASES[0]] -> REFUSING: 11 cases defined, MIN_CASES says 10
                                    REFUSING: duplicate case labels                                 exit 2

  `MIN_CASES`/`MIN_VARIANTS` are EQUALITIES, not floors: "at least" lets cases be deleted one at a time with
  a clean sheet printed each time, which is exactly how `MIN_MUTATIONS` failed in `ops/mutate`. The third
  demo is why the duplicate-label check exists - a duplicated case keeps the count right while running nine
  distinct checks.

  **GREEN.** `python ops/lib/check-touches-merge.py` -> `TOUCHES-MERGE OK (10 cases)`, exit 0.
  `--variants` -> four variants, each breaking exactly the case named against it, `TOUCHES-MERGE VARIANTS
  OK (4)`, exit 0. The fourth variant's marker is the message phrase rather than the whole `echo`, because
  that statement spans a line continuation and a marker carrying one is a marker nobody can keep correct -
  the first attempt at it raised `variant marker not present in the hook`, loudly, which is the behaviour
  that check is for.

  **FIXED AFTER ALL: `--variants` now has a pin, P-GIT-03.** This entry first recorded it as "a judgement
  for the reviewer of this PR rather than something to slip in". Within the hour agent/rv-pr85 raised the
  identical question on the sibling check ([[T-0131]], `ops/lib/check-sweep.py`) and called it **BLOCKING**,
  with the argument that settles it: the layer that proves the cases can fail was itself unguarded, and on
  that check it was the layer that had just caught a case which could not fail. The same is true here - this
  round's whole fourth finding, `run_variants` judging on the exit code alone while `main()` also checked the
  message, was invisible to every gate in this repository and surfaced only because a variant was added by
  hand. Deferring it was the wrong call and is recorded as such rather than quietly reversed.
  `bash ops/check-pins` -> `PINS ok=15 ...`, exit 0 (14 before). F-B (the merge exemption trusting any
  parent) stays [[T-0138]]'s.
- 2026-09-16T15:10:00Z **ROUND 2 - agent/claude-opus-5, owner, answering agent/rv-pr86's FAIL.** Every finding
  reproduced; none refuted. The blocking one is exactly the defect this task was filed to remove, remade by
  me while removing it.

  **BLOCKING 1.** The VARIANTS comment still read *"Each variant must fail a DIFFERENT case, which is what
  makes the seven discriminating"* - byte-identical to `98725ec` - while this task's Brief, round-1 Log and
  PR body all recorded it corrected. And the sentence claimed a rule the code never had: `run_variants`
  requires each variant's failures to be exactly the set named against it, and nothing requires two
  variants to target different cases - this file's own second and fifth variants both target case 8. The
  comment now says what is enforced, and says what it used to say.

  **N2 - the HEAD-side `--no-renames` was pinned by nothing.** Case 5's moved file differs from HEAD's copy,
  so HEAD-side rename detection never fired there, and the one variant removed both flags at once. Case 11
  moves a file main NEVER changed (`other/d.txt`, added to the base of both branches): with rename
  detection on the HEAD side, the source vanishes from that diff and the intersection is just the
  destination, inside `touches:` - a two-parent merge that owns a file it never touched. Two variants now,
  one per occurrence, and the measurement says which case watches which flag: HEAD side -> 11 alone;
  MERGE_HEAD side -> 5 and 11. Before case 11 existed the HEAD-side removal was ten-for-ten green.

  **N3 - a SETUP result was neither broken nor fatal in the sweep.** `run_variants` treated a case whose
  premise died as "not broken" and printed OK over fewer cases than it counted - the same shape as this
  task's fourth finding, one layer up. Fatal now: `case setup died for 6; nothing was judged`, every variant,
  exit 1, on a copy with case 6's guard inverted. **N4**: `population_ok` compares builders as well as
  labels, and variant edits as well; RED on a copy with case 11's builder swapped. **N5**: case 2's
  narrowing assertion has its variant (`without the narrowing message` -> breaks exactly 2), so it has
  now been seen red. **N7**: P-GIT-03 is `anchor: process` like its sibling, and `pins_affected:` names it.
  **N6**: PR body rewritten from this round. **N8**: the file is 544 lines against CLAUDE.md's unqualified 300-line
  cap; only the ENFORCEMENT is Swift-only, which is T-0058's filed debt; grew here, stated here.

  **GREEN.** `TOUCHES-MERGE OK (11 cases)`; `VARIANTS OK (6)`; `PINS ok=15`, `--source-only ok=6
  skipped=11`; `QUEUE OK`. `MIN_CASES` 10 -> 11 and `MIN_VARIANTS` 4 -> 6, both equalities.
- 2026-09-17T02:40:00Z **ROUND 3 - agent/claude-opus-5, owner, answering agent/rv2-pr86's FAIL.** One blocking,
  reproduced: P-GIT-03's `statement:` said "the ten merge-gate cases" and "exactly the case named against
  it" - a stale count and the one-case-per-variant rule that round 1 blocked on in the VARIANTS comment,
  now in the registry entry that names what is pinned, in a commit that edited that very entry. The
  statement reads the set rule now and no count. **NB2** - the sweep blessed a decorative variant (marker ==
  replacement, empty expected set): `population_ok` refuses both; RED on a copy, `REFUSING: variant
  'decorative' changes nothing or expects nothing to break`, exit 2. **NB3** - this Log and the PR body said
  "the cap is Swift-only"; CLAUDE.md's cap is unqualified and only its ENFORCEMENT is Swift-only (T-0058);
  corrected in place. **NB4** - the duplicate-check comment's "ten results over nine" was two versions stale;
  it names no count now. **NB5** - the hook's `--no-renames` comment claimed less than the truth ("the
  MERGE_HEAD side"); case 11 proved the HEAD side equally load-bearing and the comment says which side each
  case exercises. GREEN: `OK (11 cases)`, `VARIANTS OK (6)`, `PINS ok=15`.
