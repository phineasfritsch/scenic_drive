---
id: T-0132
title: Every mutation harness's vacuity proof silently decays when a test file is split at the 300-line cap
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Every `ops/mutate/*.py` harness has a `--prove-vacuity` mode. It replaces the test file with an empty suite and
requires every mutation to report MISSED - the only evidence that the harness measures *these tests* rather
than the Swift compiler. Each one names its test file as a single hardcoded constant:

```python
TESTS = ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchTests.swift"
```

**This repository also has a 300-line file cap.** A test suite that grows past it gets split, which is correct
and required - and the moment it is, the vacuity proof stops emptying all the tests. It keeps reporting on a
subset while its own output says *"with no tests present"*, which is now a false statement printed by a check
whose entire purpose is to detect false statements.

### It happened five times in one day, to five different people

* **T-0116 / PR #71** - the reviewer's BLOCKING finding. Commit bc5e7f6 split ten tests into
  `LambdaSearchBudgetUseTests.swift`; `--prove-vacuity` then exited 1 with *"8 mutations were reported
  caught"* while the task log recorded `VACUITY PROOF OK`. A demonstration that decayed at the last commit.
* **T-0119 / PR #76** - I split `RetraceDetectorTests.swift` at the cap and the proof reported
  `FAILED: caught=7 (need 0)`. It caught the split before I noticed I had caused it.
* **T-0117 / PR #73**, **T-0118 / PR #75**, **T-0114 / PR #70** - three agents fixing three unrelated reviews
  each independently hit it while splitting a suite, and each fixed it locally in their own harness.

Five independent encounters is not a coincidence, it is a design defect: the harness asks the author to
remember a coupling the file system does not enforce.

### The fix is to stop naming the file

Derive the set instead of declaring it. The harness already knows which SOURCE file it mutates; the tests that
could catch those mutations are the ones that import the module, and in practice the ones under
`Tests/<Target>Tests/` matching the subject's name. Options worth weighing in the log before choosing:

* **Glob the whole test target and empty all of it.** Simplest, strictly correct, and slowest - the proof
  rebuilds everything. Given `--prove-vacuity` is run by a person and not in CI, slow is probably fine.
* **Glob by prefix** (`RetraceDetector*Tests.swift`). Fast and wrong the first time somebody names a file
  differently - which is exactly the class of coupling this task exists to remove.
* **Make it one shared helper** in `ops/lib/`, used by every harness, so the decision is made once. The five
  harnesses have now diverged in this and several other respects, and each fix has been applied by hand.

Whichever is chosen, **the empty suite must be named after the file it replaces**. Two identically-named
`struct Empty…` declarations do not compile, and a compile failure would make the vacuity proof pass for the
wrong reason - a proof passing because nothing built is precisely the failure mode it exists to detect.

### Do

1. Remove the hardcoded single test file from every `ops/mutate/*.py`.
2. **Demonstrate red then green, and demonstrate the specific decay**: split a test file, show the proof
   failing (or, worse, silently passing on a subset), then show the fixed harness handling it.
3. While in there, the five harnesses have drifted apart in more than this - the pass condition, the vacuity
   condition, the SKIP bucket, and whether a `KNOWN_MISSED` arm exists. Consider whether the shared parts
   belong in one place. That is a judgement call and should be argued in the log, not assumed.

## Log
- 2026-09-08T23:15:00Z filed by agent/claude-opus-5 after the fifth independent encounter in one session. The
  T-0116 instance is a reviewer's blocking finding with the exact reproduction; the other four are recorded in
  their own task logs.
- 2026-09-09T00:20:00Z **A SECOND defect shared by every harness, found by a new one's first run** (T-0133). `ops/mutate/gates.py` reported `baseline does not build; nothing below would mean anything` and exited 2, while `swift build --build-tests` at the same commit succeeded with no errors.

  Cause: on this Windows checkout, the first build into a **fresh** scratch directory can fail with
  `unable to create symbolic link ... encountered an I/O error (code: 512)` and succeed immediately after.
  Every harness already allows for this **inside the mutation loop** - `if build() != 0 and build() != 0` -
  with a comment saying why. **None of them allows for it on the baseline build**, which is a single attempt.

  So a transient scratch failure makes a harness announce that the code is broken and stop, having measured
  nothing. It fails closed, which is the right direction, but it fails closed for a reason unrelated to the
  code and it says something false while doing it. On a fresh clone - which is exactly when a scratch
  directory is new - the first run of any harness can do this.

  Fixed in `ops/mutate/gates.py` (PR #82). `ops/mutate/{budget,corridorspeeds,handoff,hazards,guidance,retrace,routescore}.py` all still have it.

  This strengthens the case for the third item below: the harnesses have now drifted in the pass condition,
  the vacuity condition, the SKIP bucket, whether a `KNOWN_MISSED` arm exists, whether the vacuity proof
  empties every test file, **and** whether the baseline build is retried - and every one of those has been
  fixed by hand, in one harness at a time, after being found the hard way.
