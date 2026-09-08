---
id: T-0088
title: the 69 mutation survivors are five gaps, and one of them is the fixture's own record shape
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T05:48:57Z
lease_expires_at: 2026-09-08T11:48:57Z
worktree: wt/T-0088
branch: task/T-0088
exclusive: []
touches: [services/etl/tests/, services/etl/etl/, ops/lib/etl_mutation.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0081]] added `ops/etl-mutation` and measured **117 killed, 69 survived of 186**. A survivor count is a
map, not a verdict, and that task's log says so. This is the reading of the map: **the 69 are not 69
independent gaps. They are five, and one of them is a real hole in the oracle's own output.**

Every claim below was executed against `task/T-0081`.

**1. `etl/oracle.py:main()` is not called by any test — ~12 survivors, one cause.**

    grep -rn 'oracle.main\|from etl.oracle import' services/etl/tests/   ->  nothing

Every constant in `main()` mutates green: exit `2 -> 3`, exit `0 -> 1`, `cap=args.limit or 400 -> 401`, and
the `20260907 -> 20260908` at line 135. Those are not twelve findings, they are one untested function, and its
exit codes are the contract `ops/etl-curvature-fixture` depends on.

**2. The emitted fixture record's SHAPE is never asserted — 4 survivors, and this is the serious one.**
`oracle_select.py:162` builds each kept record:

    kept.append({"way_id": …, "name": …, "surface": …, "oracle_curvature": …, "coords": …})

Dropping **any** key — including `oracle_curvature`, the value the entire oracle exists to carry, and `coords`,
the geometry the comparison is made against — leaves the suite green. The keys appear in the repository only
inside the committed `tests/fixtures/curvature_oracle.json`; no assertion ever reads them. So the fixture could
be regenerated without its curvature values and nothing would object, which is the same shape as the
provenance defect T-0069 was filed for, one level further in.

**3. Parser guards for malformed input are untested — 4 `continue` survivors.**
`oracle.py:82`, `:86`, `:119`, `:125` are `if not m: continue` and `if not rows: continue` on a Placemark with
no DESCRIPTION or no way rows. Turning any into `pass` is green: no test feeds a malformed block.

**4. `eligible()`'s multi-operand exclusion is untested — 4 survivors at `oracle_select.py:153`.**
Dropping any of the three operands, or flipping `or` to `and`, is green. This is E4's neighbourhood, and E4
is the evasion that beat T-0074 first.

**5. `NODE_TAGS` and the `highway` value set are unasserted** — the X11/X12 class T-0081's rules reproduced
verbatim. Already described there; listed for completeness.

- Five tests, roughly. Not sixty-nine.
- **Assert the record shape first** (gap 2). It is the cheapest and it guards the thing the oracle is for.
- After each test lands, re-run `ops/etl-mutation` and **lower `MAX_SURVIVORS`** to the new number. That is
  the ratchet working; the constant is guarded by `.githooks/commit-msg`, so raising it needs a stated reason.
- Do NOT chase survivors one at a time. Gap 1 is twelve of them and one test.
- Some survivors are genuinely equivalent mutations and will never die. When the number stops falling, say
  which remain and why, rather than leaving a floor nobody can explain.

## Log
- 2026-09-08 filed by agent/claude-opus-5. The 69 came from `ops/etl-mutation` on `task/T-0081`; the grouping
  was done by reading the modules and confirming each cause, not by counting lines.
- 2026-09-08T05:48:57Z claimed by agent/claude-opus-5; lease until 2026-09-08T11:48:57Z
