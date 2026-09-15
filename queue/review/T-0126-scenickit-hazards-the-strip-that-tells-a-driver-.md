---
id: T-0126
title: ScenicKit Hazards: the strip that tells a driver what the route will do to them
state: review
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T18:07:49Z
lease_expires_at: 2026-09-08T20:07:49Z
worktree: .worktrees/T-0126
branch: task/T-0126
exclusive: []
touches: [Sources/ScenicKit/Hazards/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: agent/reviewer-pr80
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python ops/mutate/hazards.py -> `caught by a named test: 21 of 21   (trapped 0, compile-only 0, MISSED 0, skipped 0)`, all 3 EQUIVALENT mutants reported MISSED, exit 0"
  - "the red run: delete any one entry from MUTATIONS -> `REFUSING: 20 mutations and 3 equivalent mutants, expected at least 21 and 3.` exit 2. Delete `func noCellHasNoCeiling()` from HazardStripTests.swift -> `caught by a named test: 20 of 21` with `MISSED: no-cell silently stops firing above 600 minutes`, exit 1"
---
## Brief

The hazard strip is the one place the product tells a driver something they cannot see on the map, and it is
the safety half of the plan's risk table: *"Sedan onto dirt/gated/closed road - Med likelihood, injury and
liability blast radius."*

CLAUDE.md makes it a product invariant: **every `Route` has `hazards: [HazardFlag]`**, and P-SAFE-02 requires
the flags at three layers - ScenicKit, a golden fixture, and an XCUITest on `warning.*`. This is the first
of the three.

From the plan, the flags a V1 route can carry:

  * `surfaceUnknown(km:)` - the route spends distance on ways with no `surface` tag. Shown only past a
    threshold, because "unknown" is not "unpaved" and flagging every rural lane trains the driver to ignore
    the strip.
  * `gate` / `ford` - positive evidence of a physical obstruction on the way.
  * `closure(source:until:)` - from the 511/Caltrans feed, with its provenance, because a closure the app
    cannot attribute is one the driver cannot verify.
  * `noCell(minutes:)` - from the FCC BDC join. Minutes, not kilometres: the question a driver is actually
    asking is how long they are out of contact.
  * `twilightArrival(at:)` - arriving after civil twilight, which matters most on exactly the roads this
    product sends people down.

### What makes this more than an enum

**Ordering is the product.** A strip is read top-down and the first line is the one that gets read at all.
So the flags sort by consequence - a closure or a ford before a stretch of unknown surface - and that
ordering has to be pinned, not incidental to how the derivation happened to append them.

**Thresholds are safety decisions.** `surfaceUnknown` only appears past 2 km (the plan's number), and
`noCell` only past a duration worth naming. Both must be pinned against literals, not against the constants
they check - this repository has shipped that defect eleven times in one session and four of those were in
tests written to close a previous instance.

**A flag must never be silently dropped.** The derivation takes what the router reported and turns it into
flags; anything it cannot classify has to surface, not vanish. A hazard strip that quietly omits a ford is
worse than no strip, because the driver has learned to trust it.

Do:

1. `Sources/ScenicKit/Hazards/HazardFlag.swift` - a closed enum, one case per hazard above, `Equatable`
   and `Sendable`, with the payloads the UI needs to write a sentence.
2. `Sources/ScenicKit/Hazards/HazardStrip.swift` - derivation from a route's per-edge facts, ordering by
   consequence, and the thresholds.
3. Tests pinning: the order, each threshold at and either side of its boundary, that an unclassifiable input
   surfaces rather than disappears, and that a route with nothing wrong produces an empty strip rather than
   a reassuring flag.
4. `ops/mutate/hazards.py` in the shape of the existing five: built before a compile failure is believed, a
   catch requires a NAMED test, `trapped` reported separately, an `EQUIVALENT` list asserted the other way
   round, and `--prove-vacuity`.

**No `Package.swift` change**: `Sources/ScenicKit/Hazards/` is inside the existing target path.

**Not in scope**: the 511 feed, the FCC join, and the solar arithmetic. This is the type and the derivation;
each source is its own task, and inventing their formats here would be the fabrication this repository
exists to catch.

## Log
- 2026-09-08T18:07:49Z claimed by agent/claude-opus-5; lease until 2026-09-08T20:07:49Z
- 2026-09-08T19:05:00Z GREEN: `swift test --scratch-path .build-T0126` -> 29 tests in 4 suites passed (0.037 s). `bash ops/check-pins --source-only` -> `PINS ok=5 skipped=9 pending=0 expired=0 failed=0`. Line counts: HazardFlag 71, HazardStrip 106, HazardStripTests 152, ops/mutate/hazards.py 234 - all under the 300 cap.
- 2026-09-08T19:05:00Z `bash ops/test` FAILS, and NOT because of this task: `FAIL: services/api exists but vitest produced no report`. `services/api/node_modules` is absent in this worktree AND on main, so the Worker tier cannot run for anyone right now. That is already filed as T-0040 (claimed). The Linux Swift tier is green (29/4 above) and this task adds 13 tests to it. I did not raise floor_linux - a floor ratchet is the reviewer's, and it cannot be verified while ops/test cannot produce a total.
- 2026-09-08T19:05:00Z MUTATION HARNESS `ops/mutate/hazards.py`, 15 mutations, all caught BY A NAMED TEST: `caught by a named test: 15   trapped: 0   compile-only: 0   MISSED: 0   of 15`. Six move a NUMBER or a comparison direction (2.0 -> 0.1, 2.0 -> 50.0, `>` -> `>=` on surface, 5 -> 60, `>=` -> `>` on no-cell, `>` -> `>=` on twilight) because a reviewer found an earlier harness whose every mutation was structural, which is exactly where a suite is blind. Three permute `severityRank` (closure 0 -> 9, surfaceUnknown 6 -> 0, unrecognised 3 -> 8). The rest attack the two product claims: nothing is dropped (delete the `.unrecognised` loop; drop the dedup; report a ford as a gate; accept a sourceless closure) and a clean route stays empty (seed `out` with a reassuring flag).
- 2026-09-08T19:05:00Z EQUIVALENT MUTANT asserted the other way round: swapping the order of the independent `.ford`/`.gate` appends cannot change the output, since the stable sort restores ford(1) before gate(2). The harness reports it MISSED, which is the PASS - a catch there would mean a test had an opinion about how the code is written rather than what it does, and the way an agent satisfies such a demand is by anchoring on source text.
- 2026-09-08T19:05:00Z VACUITY PROOF: `ops/mutate/hazards.py --prove-vacuity` replaces HazardStripTests.swift with an empty suite and requires every mutation to go MISSED. Result `caught by a named test: 0 ... MISSED: 15 of 15`, `VACUITY PROOF OK`. Without this the harness could be measuring the Swift compiler.
- 2026-09-08T19:05:00Z RED (the harness itself, not just the code): deleted the ONE named test that pins the no-cell boundary, `func noCellThreshold()`, and re-ran. `HARNESS EXIT = 1`, with `MISSED: no-cell comparison strict, so exactly 5 minutes stops firing`. Honest detail worth the reviewer's attention: the sibling mutation `5 -> 60 minutes` stayed CAUGHT, because `orderedByConsequence` passes `noCellMinutes: 30` and would stop producing that flag at 60. So deleting one test cost exactly one mutation, the boundary one - which is the correct and non-flattering result, and evidence the harness measures assertions rather than files. Tests restored byte-identical (verified by comparing bytes, not by re-reading the diff).
- 2026-09-08T19:05:00Z THE DEFECT THIS REPOSITORY KEEPS SHIPPING was avoided deliberately and the reviewer should attack exactly this. The order is asserted in `orderedByConsequence` as a WRITTEN-OUT SEQUENCE of seven `flags[i] == ...` comparisons, never as `flags.map(\.severityRank).sorted()` or any expression that reads `severityRank` - deriving the expectation from the property under test would hold for any ordering the code happened to have. Both thresholds are written as literals (`== 2.0`, `== 5`) and then probed on BOTH sides of the boundary (1.9 / 2.0 / 2.1 and 4 / 5 / 6), so the constant and the comparison are each pinned independently. The three `severityRank` mutations and the two comparison-direction mutations all being caught is the mechanical evidence that this held. **[CORRECTED 2026-09-15 - that last sentence is an overclaim and the PR #80 reviewer was right (F8). Those catches are evidence about the ORDER the strip comes out in. They are NOT evidence that `severityRank` is what produces it, and cannot be: see the 2026-09-15 entry below.]**
- 2026-09-08T19:05:00Z ONE CONSTANT IS NOT FROM THE PLAN AND IS LABELLED SO. `surfaceUnknownMinimumKm = 2.0` is the plan's number, quoted at the declaration ("shown only if the route spends >2 km on such edges"). `noCellMinimumMinutes = 5` IS NOT: the plan specifies the FCC BDC join and the flag and leaves the threshold open. Its doc comment says so in as many words and says the 5 is chosen, so it is not mistaken later for a value handed down. Reviewer: this is the number to argue with.
- 2026-09-08T19:05:00Z `HazardFlag` is a CLOSED enum with no `String` escape hatch, and `.unrecognised(String)` is how a tag this version has no case for reaches the screen instead of vanishing. A strip that quietly omits a ford is worse than no strip, because the driver has learned to trust it. `.unrecognised` sorts at rank 3, above the three advisories, because nobody has judged it.
- 2026-09-08T19:05:00Z SCOPE HELD. No 511 feed, no FCC join, no solar arithmetic - `RouteFacts` is a plain value the caller fills, and inventing those formats here would be the fabrication this repository exists to catch. `Sources/ScenicKit/Hazards/` is inside the existing SwiftPM target path, so NO `Package.swift` edit and no `exclusive:` lock was needed. This is layer 1 of 3 for P-SAFE-02; the golden fixture and the `warning.*` XCUITest are separate tasks and the pin stays pending until they exist.
- 2026-09-08T19:05:00Z moved to review/. Reviewer must not be agent/claude-opus-5 (`ops/queue-check`).

### 2026-09-15 — fixer round against the PR #80 review (`.artifacts/rv1/pr80.md`)

- FIVE SURVIVORS CLOSED, and a sixth of the same shape the review did not name. Every one reproduced first against the shipped suite (`.artifacts/fix_probe.py`, pristine bytes from `git show HEAD:`, never the working tree): `SURVIVED RV1/RV5/RV6/RV7/RV14 ... NO TEST OBJECTED`, plus RV14b, the SOURCE half of `RouteFacts ==`, which survives exactly as the `until` half does. After the five new tests, the same script on the same six: `CAUGHT ... by:` the named test written for it, each caught by exactly one test and no other. NO SOURCE CHANGE: the code was right in all six cases, nothing pinned it. `HazardStrip.swift` and `HazardFlag.swift` are byte-identical to the reviewer's md5s (b67469b6 / ece140a4).
- THE BLIND SPOT BEHIND FOUR OF THE FIVE, named so the next harness does not repeat it: every fixture in the suite probed a threshold at its FLOOR and nothing anywhere probed the TOP of a range. A hazard can therefore be removed for being too big - 600 minutes out of contact, 100 km of unsurveyed surface - and nothing moves. The fifth is the same failure in another dress: seven flags is the number of flag KINDS, so `.prefix(7)` looked complete in every fixture that existed. New tests: `nothingIsTruncated` (nine flags in, nine out, the count transcribed from the inputs by hand and the closures and tags fed in the OPPOSITE order to the one expected out), `noCellHasNoCeiling`, `surfaceHasNoCeiling`, `whitespaceSourcedClosureReachesTheStrip`, `routeFactsEqualityCoversEveryField` (all ten fields, since a tuple array cannot be synthesised and each line of the operator can be deleted alone).
- NOT ONE EXPECTED VALUE IS READ BACK FROM THE CODE. No new assertion mentions `severityRank`, `noCellMinimumMinutes` or `surfaceUnknownMinimumKm`; every expectation is a literal transcribed by hand. Each new test was then shown to FAIL: `.artifacts/fix_probe.py` reports each of the six going SURVIVED -> CAUGHT, and the acceptance block's red run deletes `func noCellHasNoCeiling()` and re-runs the harness for `caught by a named test: 20 of 21` with `MISSED: no-cell silently stops firing above 600 minutes`, exit 1. Deleting one test costs exactly one mutation, which is the non-flattering and correct result.
- THREE SURVIVORS REFUSED, matching the reviewer's own standard. RV2 (delete the sort), RV4 (flatten every `severityRank` to 0) and RV3 (rank-only unstable sort) are NOT banked as fixes. `flags(for:)` appends in groups of non-decreasing rank, and within a group every element shares a rank, so ordering by `(rank, offset)` is ordering by `offset`, which is the order `out` is already in: the sort is the IDENTITY for every possible input. PROVED, not asserted - `.artifacts/equiv_check.py` dumps `flags(for:)` over 15000 input combinations under pristine, under RV2 and under RV4 and the three dumps are byte-identical (md5 70f0d00463bec147c23ea3e2edae8db2). RV2 and RV4 now live in the harness's EQUIVALENT arm, where a CATCH fails the run, because the only test that could close them is one that reads `severityRank` - the signature defect. RV3 is in NEITHER arm: `sorted(by:)` is not contractually stable in Swift, so a rank-only sort is behaviour-preserving by implementation accident rather than by argument, and neither arm can honestly hold it. Said plainly: the product-visible ORDER is pinned; the MECHANISM that produces it is not, and cannot be without a self-referential test.
- THE LOG'S OWN OVERCLAIM IS CORRECTED, not defended - see the bracketed correction on the 19:05 entry above. What the three caught `severityRank` mutations show is that a WRONG ORDER is caught. They show nothing about the order being derived from the rank table, because for every input the append sequence already equals rank order.
- HARNESS, each guard demonstrated RED then GREEN (`.artifacts/atk_fix.py`, which loads both the HEAD copy and the working copy by path and overrides globals IN MEMORY - the tracked file's md5 is unchanged across the whole attack run):
  * MIN_MUTATIONS 13 -> 21 and MIN_EQUIVALENT 1 -> 3, EQUAL to the shipped population. BEFORE: two of fifteen mutations deleted, no refusal, the run proceeds to `caught by a named test: 0 of 13`. AFTER: one of twenty-one deleted -> `REFUSING: 20 mutations and 3 equivalent mutants, expected at least 21 and 3.` EXIT 2; one of three equivalents deleted -> the same refusal. A floor that does not refuse a deletion is a comment, not a floor.
  * the baseline build is RETRIED, as the mutation build already was (F4 / T-0132). BEFORE, one injected transient failure then a healthy box: `baseline does not build; nothing below would mean anything`, EXIT 2. AFTER: `build()` called twice, the run gets past the baseline. False FAIL only, but it is a false FAIL nobody would have trusted twice.
  * `vacuity_gap()` is new. `--prove-vacuity` empties only HazardStripTests.swift, and the review established by hand with one grep that no other test file references the subject. A fact a harness depends on belongs in the harness: planting a second test file that mentions `HazardStrip` now gives `REFUSING: --prove-vacuity empties only HazardStripTests.swift, but these test files also reference the subject and could catch a mutation: Tests/ScenicKitTests/ZZHazardProbe.swift`, EXIT 2. On the HEAD copy the same planted file produces no refusal at all.
  * `FAIL_LINE` narrowed to `Test "..." recorded an issue` (F7). The old second branch, `Test run with .*failed`, is the RUN-LEVEL summary - "a non-zero exit, summarised", which the docstring promises the harness does not accept. Shown directly: against a run-level summary line OLD matches and NEW does not; against a named failure both match. The full run is `21 of 21` under the narrowed regex, so nothing was lost.
  * `SCRATCH` moved from `.build-mutate-hazards` to `.build/mutate-hazards` (F5). `.gitignore` has `.build/`, which never matched the old name, so the harness left `?? .build-mutate-hazards/` behind and `ops/sane` counted the worktree it had just certified as dirty. `.gitignore` is outside this task's `touches:`, so the fix is in the harness rather than the ignore file. Both stale directories deleted; `git status --porcelain` is empty.
  * the mutation named "sort by rank alone, losing the stable order within a severity" is renamed "sort by rank DESCENDING, so the strip is read worst-last". Its replacement also inverted the comparator, so its catch was evidence about direction and never about stability - the reviewer was right that the name claimed more than the mutation shows.
- ACCEPTANCE BLOCK POPULATED (F12) and both lines re-run verbatim from the committed state, not from prose: `.artifacts/redrun.py` produced the exact strings in the frontmatter, exit 2 and exit 1 respectively, and proved each restore by md5 against `git show HEAD:<path>` plus `git diff --quiet`, not by trusting a `finally`.
- LINE COUNTS, replacing the stale ones in the 19:05 entry (F13 - that entry said 234 when the file was already 256): HazardFlag 71, HazardStrip 106, HazardStripTests 244, ops/mutate/hazards.py 354. The three Swift files are under the 300-line cap. The harness is not, and P-SRC-02 does not apply to it: its assertion (`ops/lib/check-line-cap`) globs `Sources/**/*.swift` and `Tests/**/*.swift` only, and `ops/lib/queue.py` is 1007 lines. Flagging this explicitly because the PR #80 review measured this file against the cap and the next one will too.
- NOT CLOSED, and the PR should still be read as blocked on the first of these:
  * **F1/F2 - a closure with an empty source is dropped entirely, and `emptyStringsIgnored` pins the dropping.** Reproduced, and I am not fixing it in this round: it is a product decision about what an unattributable rank-0 hazard should do (surface as `.closure` with blank provenance, surface as `.unrecognised`, or stay dropped), it changes shipped behaviour plus a shipped test plus the harness mutation "accept a closure with no source", and it was not in this round's scope. It wants its own task and a decision, not a fixer's guess. Note that the new `whitespaceSourcedClosureReachesTheStrip` does NOT cement it: if F1 is resolved by removing the guard, that test still passes, and only the closure line of `emptyStringsIgnored` has to move.
  * F9 (`orderedByConsequence` is titled "whatever order the router reported them" but permutes nothing) - the new `nothingIsTruncated` does feed both orderable inputs in reversed order, so the CLAIM is now covered by a test; the misleading title on the older test is untouched.
  * F10 (`surfaceUnknownMinimumKm` is an exclusive bound wearing an inclusive name), F11 (5 minutes is too low), F14 (`reviewer:` filled in by the owner). All three are judgement calls for a human or the reviewer, not defects a fixer should quietly settle. F11 in particular is the number the task asked the reviewer to argue with, and the reviewer argued; changing it is a product decision.
- ENVIRONMENTAL, checked and not attributed: `bash ops/test` is green on the Linux tier - `√ Test run with 34 tests in 4 suites passed` (29 before this round; the five new tests are the difference) - then `FAIL: services/api exists but vitest produced no report`, because `services/api/node_modules` is absent here and on main. That is T-0040. `bash ops/check-pins` -> `PINS ok=12 skipped=0 pending=2 expired=0 failed=0 tier=linux`, exit 0. `bash ops/queue-check` -> `QUEUE OK (119 tasks)`. `bash ops/sane` -> `SANE FAIL exit=10`, naming ten worktrees; nine belong to other agents working concurrently on this box and T-0126's own entry was this round's uncommitted work, which is now committed and pushed.
- NOT TRANSITIONED. This task stays in `queue/review/` with `state: review` for a different agent to review, per CLAUDE.md.
