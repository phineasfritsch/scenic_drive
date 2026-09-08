---
id: T-0081
title: the oracle guard needs a structural property, not more enumerated routes
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:10:02Z
lease_expires_at: 2026-09-08T10:10:02Z
worktree: wt/T-0081
branch: task/T-0081
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, services/etl/pyproject.toml, ops/etl-mutation]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0074]] was given seven named routes and closed all seven, verified. The round-two adversary then executed
**ten more that pass**, and every one is the adjacent form of a route that was closed:

    X1   the size dodge, one power of two up            (E5 was `< (1 << 20)`; this is `< (2 << 20)`)
    X3   the partial read, at a bigger block            (E6 read 1 MB; this reads 2 MB)
    X2   the refusal keyed on the directory the real oracle lives in, instead of on size
    X4   the pinned constant kept, the call site ignoring it
    X5   `random.Random(seed).shuffle` -> `random.shuffle`; the fixture stops being reproducible
    X6   `cap: int = 400` -> `cap: int = 4`; round 5's "subset of itself" reached through the cap
    X7   the arity floor on condition 2's precondition
    X11  narrow the TABLE not the code - delete one entry from NODE_TAGS
    X12  keep the one value the new test uses, drop the other five

Plus the one round-one route that was explicitly out of scope and remains open: rewriting
`inputs/manifest.yaml`'s `sha256:` and the fixture's `source_sha256` to the same fabricated value, `186 passed`.

**The finding is not any single one of these. It is that the list does not terminate.** Three rounds of
T-0025, then T-0069, then T-0074, have each closed the routes they were shown and been beaten by the next
variant of the same idea. Writing an eleventh test for X1 buys nothing: X1 is E5 with a different constant.

**What a structural property would look like**, instead of a longer list:

- **Mutation testing over `etl/oracle_select.py` and `etl/oracle.py`.** Every route above is a source
  mutation, and every one leaves the suite green - that is the definition of a gap in mutation coverage. A
  mutation run answers the whole class at once and keeps answering it for mutations nobody has thought of.
  `mutmut` or `cosmic-ray` on those two modules, with a coverage floor, run in CI rather than per commit.
- **Property tests rather than fixtures for the funnel.** Every exclusion condition has a shape: given an
  input that violates condition N, `build()` must exclude it. Generate those inputs instead of hand-writing
  one KMZ per condition; the hand-written ones are what X11 and X12 walked around by narrowing the table.
- **The provenance chain needs to leave the repo.** Two co-editable literals compared with each other cannot
  be fixed inside a pytest suite, because the real oracle is gitignored and a test cannot hash a file that is
  not in the tree. The containment is `ops/etl-fetch-inputs` failing at fetch time, which is outside
  `ops/test`. That half belongs in `ops/sane` or the fetch path - file it separately, do not attempt it here.

Do not simply add ten more tests. If that is the chosen route anyway, say in the log why mutation testing was
rejected, because the next adversary will find X13.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of T-0074. All ten
  mutations were executed and reverted; the verifier's tree ended clean.
- 2026-09-08T04:10:02Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:10:02Z
