---
id: T-0127
title: CLAUDE.md tells agents to commit ops/*.py executable; P-OPS-01 rejects exactly that
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [CLAUDE.md, ops/lib/check-exec-bits, pins/PINS.yaml]
pins_affected: [P-OPS-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md, under **File discipline**, says:

> New scripts under `ops/` or `.githooks/` must be committed executable: `git update-index --chmod=+x <path>`.
> `core.filemode` is false on the Windows checkout, so git will not notice on its own and CI (`bash ops/x`) stays
> green while direct invocation breaks. Pin P-OPS-01 enforces it; data files there stay 100644.

`ops/lib/check-exec-bits`, which *is* P-OPS-01's assertion, disagrees. Its awk rule classifies every `*.py`
under `ops/` as a **data file that must be 100644**, and documents why at length:

> except `ops/lib/*.py`, which is also 100644: every call site ... invokes it as `"$PY" ops/lib/x.py` ... i.e.
> as an argument to an interpreter, never as `./ops/lib/x.py`. The exec bit does nothing there, so asserting
> 100755 would assert a mode the repo does not actually depend on.

The reasoning in the check is right. The sentence in CLAUDE.md is the one that is wrong, and CLAUDE.md is the
document every agent is told to obey on every task.

### The demonstration, already run

T-0126 added `ops/mutate/hazards.py`, read CLAUDE.md, and did what it says:

```
$ git update-index --chmod=+x ops/mutate/hazards.py
$ bash ops/lib/check-exec-bits
P-OPS-01: wrong git file mode:
  ops/mutate/hazards.py (data, should be 100644, is 100755)
EXIT=1
$ git update-index --chmod=-x ops/mutate/hazards.py
$ bash ops/lib/check-exec-bits
P-OPS-01: 34 files, 23 required present, all modes correct
```

This is not hypothetical and not a one-off: **PR #59 (task/T-0080) is red in CI right now** for the mirror
image of the same confusion - `ops/lib/pins_mutation.py` and `ops/lib/pins_mutation_cases.py` are 100644 (the
mode main's checker wants) while that branch still carries an older `check-exec-bits` demanding 100755. Two
agents, opposite directions, same root cause: the rule exists in two places and they do not say the same thing.

Note also that the check's own comment says `ops/lib/*.py` while the awk it describes matches `*.py` **anywhere**
under `ops/` - which is how `ops/mutate/hazards.py` got caught. The comment and the code disagree about scope
even inside the one file.

### Do

1. Make CLAUDE.md state the actual rule, including the `.py`-is-invoked-by-an-interpreter reasoning, so an agent
   that follows CLAUDE.md produces a green tree. The sentence should say what `check-exec-bits` enforces, not a
   simplification of it.
2. Fix the scope disagreement inside `ops/lib/check-exec-bits`: either narrow the awk to `ops/lib/*.py` to match
   its comment, or widen the comment to match the awk. Decide which is intended - `ops/mutate/*.py` are run as
   `python ops/mutate/x.py`, so by the check's own stated reasoning they belong in the 100644 class and the
   COMMENT is the thing that is too narrow.
3. **Do not anchor anything on the comment** - CLAUDE.md forbids it. Whatever the rule becomes, it has to be
   asserted from the awk's behaviour, with a test that adds a `.py` under a *new* subdirectory of `ops/` and
   pins which mode P-OPS-01 demands for it.
4. Demonstrate red then green in the log, in both directions: a `.py` wrongly 100755, and a non-`.py` script
   wrongly 100644.

### Why it is worth a task rather than a one-line edit

The premise in CLAUDE.md is that `ops/`, `pins/` and `queue/` exist to contradict the agent. When the
instruction file and the enforcing check contradict *each other*, an agent that obeys the written rule gets a
red CI run and then - this is the dangerous part - learns to treat P-OPS-01 as noise to be chmod-ed away. That
is exactly how a real mode regression would get waved through.

## Log
- 2026-09-08T19:30:00Z filed by agent/claude-opus-5 while closing T-0126, which hit it. Filed with the red run
  above already performed, so the next owner starts from a demonstrated failure rather than a claim.
