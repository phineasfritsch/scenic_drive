---
id: T-0041
title: check-exec-bits REQUIRED will omit three more load-bearing ops/lib files once T-0021 and T-0023 merge
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-exec-bits]
pins_affected: []
reviewer: null
depends_on: [T-0021, T-0023]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-exec-bits` (P-OPS-01) carries a `REQUIRED` list of load-bearing files whose absence must fail
the pin. T-0036 added the `ops/lib/*.py` helpers to it, but three more load-bearing files exist only on
branches that had not merged when that work was done, so they are outside `REQUIRED` and will land silently:

- `ops/lib/classify-checks.py` (on `task/T-0021`) - the fail-closed check classifier `ops/merge` depends on.
  Deleting it makes `ops/merge` refuse everything, which is safe, but renaming it is not caught.
- `ops/lib/gh-stub-for-merge-tests` (on `task/T-0021`, also added on `task/T-0022`) - the deterministic `gh`
  double the merge-gate demonstrations run against. Without it those demonstrations cannot be reproduced.
- `ops/lib/check-failure-naming` (on `task/T-0023`) - P-OPS-02's whole assertion.

Confirmed by agent/reviewer-19 with `git ls-tree` on both branches while reviewing T-0036, and filed as a
MAJOR non-blocking finding there.

- Add all three to `REQUIRED` once T-0021 and T-0023 are merged (hence `depends_on`).
- Decide the mode for `classify-checks.py`: T-0036 established that `ops/lib/*.py` invoked only through an
  interpreter belongs in the 100644 data bucket. Check its call sites and follow that rule, or argue against it.
- `ops/lib/check-failure-naming` is a bash script invoked as `bash ops/lib/check-failure-naming`; confirm what
  mode the rule actually requires rather than assuming.
- Demonstrate red: `git rm --cached` each of the three in turn and show the pin passing before the change and
  failing after, naming the file.

Related: `ops/lib/ro_grammar.py:5-6`'s docstring documents `ro_grammar.py --self-test` with no interpreter
prefix - a bare invocation that no longer works now the file is 100644 (reviewer-19, MINOR). Fix the docstring
in the same pass.

### 2026-09-07 - a second, worse symptom of the same merge, found by rehearsing it

The original finding was that three load-bearing files will be missing from `REQUIRED` once T-0021 and
T-0023 land. Merging the whole backlog locally, in `queue/MERGE-ORDER.md`'s order, turned up something
sharper on the same file:

    P-OPS-01: wrong git file mode:
      ops/lib/classify-checks.py (data, should be 100644, is 100755)

`ops/lib/classify-checks.py` is committed 100755 on `task/T-0021`. T-0036 reclassified `ops/lib/*.py` into
the 100644 data bucket - correctly, they are only ever invoked as `"$PY" ops/lib/x.py` - and flipped the four
that existed on `main` at the time. `classify-checks.py` was not one of them, because it does not exist on
`main`; it only exists on T-0021.

So: **neither branch is wrong on its own, both pass their own gates, and the merged result fails P-OPS-01.**
`main` would have gone red on the first merge after both landed, with a failure that points at a file neither
task touched together.

That makes this a MERGE-TIME fix, not a follow-up: flipping the mode has to happen in the same window as
adding the three names to `REQUIRED`, and `queue/MERGE-ORDER.md` now names it as a step. Do both here:

    git update-index --chmod=-x ops/lib/classify-checks.py

and check the same trap for the other two files this task adds - `ops/lib/gh-stub-for-merge-tests` and
`ops/lib/check-failure-naming` are bash scripts, so 100755 is correct for them, but verify rather than assume:
the rehearsal only caught the `.py` because P-OPS-01 happens to encode the rule.

Demonstrate red by reproducing the rehearsal rather than by reasoning: merge `origin/task/T-0021` and
`origin/task/T-0036` into a scratch branch off `main` and run `bash ops/lib/check-exec-bits`.

## Log
