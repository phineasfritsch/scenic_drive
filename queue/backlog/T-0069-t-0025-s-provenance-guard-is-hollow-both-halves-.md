---
id: T-0069
title: T-0025's provenance guard is hollow: both halves of the round-5 fix can be deleted with tests green
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: [T-0025]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0025's round-5 blocker was that a green run could replace the committed oracle with a subset of itself
while the fixture still claimed the pinned digest. The fix had two halves: `build()` computes
`source_sha256` from the file it read, and refuses a KMZ whose digest does not match the manifest's pin.
`test_oracle_report.py::TestTheFixtureRecordsRealProvenance::test_the_fixture_was_built_from_the_pinned_oracle`
was written as the guard that makes it stick, and the task was signed off into `queue/done/` on it.

**Both halves can be deleted with the whole suite green.** Executed on task/T-0025:

    restore the hardcoded literal - defect #4 verbatim:
      "source_sha256": "3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046",
      -> 171 passed on Windows/CPython 3.10, 171 passed in the pinned scenic-etl image. Nothing red.

    delete the refusal: `if want and digest != want:` -> `if False:`
      -> also survives the whole suite with nothing red.

**Why.** Both sides of the assertion are committed, hand-editable text in the same commit: the fixture's
`source_sha256` field and `inputs/manifest.yaml`'s pin. And **no test in the suite ever calls
`oracle_select.build()` or `eligible()`** - `git grep -n 'build(\|eligible('` over `services/etl/tests/` on
that branch returns exactly one hit, inside this file's own module docstring. So the property the fix
actually introduced - that the field is COMPUTED rather than typed - is untested, and the committed fixture
already carries the manifest's literal.

The docstring's sentence *"Rebuild from any other file and `build()` records that file's digest, and this
fails"* is a claim about `build()` that the assertion cannot reach.

- Call `build()` in a test. Point it at a temporary KMZ whose digest is known and different, and assert the
  written `source_sha256` is that digest and not the manifest's. That is the property, and nothing currently
  exercises it.
- Assert the refusal separately: `build()` against an unpinned KMZ must raise, with the message naming both
  digests.
- The sweep also notes `build()`'s refusal keys on the BASENAME via `oracle.pinned_digest(kmz.name)`, so a
  differently-named file with the same basename resolves to the same pin. Check whether that is reachable.
- Demonstrate red by restoring the literal, exactly as above, and show the new test failing where the whole
  suite currently passes.

**This is the same defect one level further out, for the sixth time in this task's history** - each round's
fix containing the shape it was written to remove. Worth stating in the log rather than only fixing, because
the pattern is the finding.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the self-referential-check sweep, which was built precisely to
  hunt this class after it appeared in five consecutive rounds of T-0025. It found it in the round-5 fix.
