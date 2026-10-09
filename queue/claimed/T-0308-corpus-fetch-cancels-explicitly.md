---
id: T-0308
title: The corpus fetcher cancels a refused response explicitly (dataTask.cancel() beside completionHandler(.cancel)) so the refusal path completes the same way on Darwin and on swift-corelibs-foundation, and the 404 / wrong-range rows catch the error-order swap off Darwin too
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T22:23:09Z
lease_expires_at: 2026-10-10T04:23:09Z
worktree: .worktrees/T-0308
branch: task/T-0308
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0305]
verify: [ops/test, ops/check-pins]
acceptance:
  - "CorpusDownloadDelegate calls dataTask.cancel() next to every completionHandler(.cancel); on Linux/Windows the 404 and wrong-range rows of fetchTableOverEveryResumeFileAndServer() now complete with URLError.cancelled and catch T-0305's mutant 22 (the error-order swap) by name - shown MISSED on those rows before, CAUGHT after"
  - "Dropping the explicit cancel is a population entry: CAUGHT off Darwin, or an EQUIVALENT entry with a witness if a platform makes it unobservable; digest row re-approved"
---
## Brief

rv2-t0305 recordable 1 / T-0305 owner stillOpen 1 (PR #195): swift-corelibs-foundation ignores the .cancel response
disposition, so off Darwin the 404 and wrong-range refusal rows never see a cancel and the error-order swap is caught
only through the long-body rows. The app ships on Darwin; this closes the platform gap in the tests.

## Log
- 2026-10-07T23:30:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0305's recordable.
- 2026-10-09T22:23:09Z claimed by agent/claude-opus-5; lease until 2026-10-10T04:23:09Z
- 2026-10-09T22:43:21Z MEASURED (agent/claude-opus-5, worktree on 7cc37c1f, swift 6.3.3 native = swift-corelibs-foundation).
  WHERE: CorpusDownloadDelegate.urlSession(_:dataTask:didReceive:completionHandler:) calls completionHandler(.cancel)
  at two sites and nowhere calls dataTask.cancel() beside them: the status refusal (any status but a 200 or a 206 at
  the resume offset; failure = .status) and the resume file that cannot be opened (FileHandle(forWritingTo:) throws;
  failure = .transport(cannotWriteToFile)). The two body paths in urlSession(_:dataTask:didReceive:) - one byte past
  `expected`, a write that throws - already call dataTask.cancel(). WHAT REACHES THE CALLER: Darwin honours the
  .cancel disposition, the task completes with URLError.cancelled and the delegate's `failure` outranks it, so the
  caller sees .status(404) / .status(206). swift-corelibs-foundation hands the delegate a completion handler that
  ignores the disposition, so no cancel reaches the URLProtocol: the stub plays the rest of its script, the delegate
  drops the body behind `failure == nil`, the scripted finish completes the task with error nil and the caller sees
  the same .status. Same error to the caller, a different task completion. ROWS: the table's servers `missing`
  ([404, "not found", finish]), `wrongRange` ([206 at byte 0 with no Range / byte 7 with one, body, finish]) and
  `long` ([head, three chunks, one extra byte, finish]), each over five prefixes, four of which send a request
  (`complete` sends none). No row reaches the unopenable-resume-file site. MUTANT 22 (the error-order swap) is
  caught off Darwin only through the four `long` rows (T-0305 Log 2026-10-07T22:39:41Z: 4 issues, all longBody vs
  transport(-999)). Isolated here: the table's server loop narrowed to [Server.missing, .wrongRange] in the test
  file only (uncommitted, restored after; Sources at HEAD), `python ops/mutate/corpusfetch.py --only 22`
  22:28:47Z-22:39:23Z -> `BASELINE ... exit=0`, `MISSED 22 the session's cancel error outranks the refusal that
  caused it exit=0 no test objected`, `MUTATE FAILED caught=0/1 equivalent_caught=0 (--only: 1 of 22 entries)`.
  RULINGS (before code):
  R1 Both completionHandler(.cancel) sites get dataTask.cancel() on the next line; the disposition stays (Darwin
     requires the handler be called, and a second cancel of a cancelling task is a no-op).
  R2 "complete with URLError.cancelled" is not visible through the fetcher by design (the refusal outranks the
     cancel), so it is observed at the stub: StubCorpusURLProtocol records, per cancelled request, how many scripted
     steps it never played because stopLoading() came first, and the table's Result carries that list under its
     FULL equality. corelibs' cancel() calls stopLoading() before it reports URLError.cancelled, so the record is
     complete before fetch returns. A run that finishes every step records nothing (whether or not a session calls
     stopLoading() after a finish), so the field is platform-neutral.
  R3 The unopenable-resume-file site gets a row: server `unwritable`, whose script deletes the resume file in
     startLoading() before it responds - the delegate opens the file on the response, so it throws. Expected:
     .transport(cannotWriteToFile), no resume file, the body and finish unplayed. noFetchRowIgnoresTheResumeFile
     covers it like every server.
  R4 Population: 23 "a refused status lets the response play on" and 24 "an unopenable resume file lets the response
     play on" drop each new cancel; both are mutants caught by fetchTableOverEveryResumeFileAndServer() off Darwin
     (the population runs here and on Linux), not EQUIVALENT. On Darwin the disposition alone cancels and both would
     be unobservable - recorded, not run (no Darwin swift test on this box). MIN_MUTATIONS 22 -> 24.
  R5 CorpusDownloadDelegate.swift's digest row is re-approved; no other Sources/ file changes.
  ACCEPTANCE (re-run and re-quoted at the final pre-review commit, on the merged head):
  A1 Every completionHandler(.cancel) line in CorpusDownloadDelegate.swift is followed by a dataTask.cancel() line:
     2 of 2 (awk over the file).
  A2 swift test --filter 'URLSessionCorpusFetcherTests|CorpusLaunchTests' green, own scratch path.
  A3 The table narrowed to [Server.missing, .wrongRange] (uncommitted, as measured above), `--only 22` on the fix:
     `caught 22 ... by: fetchTableOverEveryResumeFileAndServer()`, MUTATE OK caught=1/1 (MISSED before, above).
  A4 The swap applied by hand to the whole table: the issue count names the missing, wrongRange and unwritable rows
     as well as long (4 rows each that send a request), each expecting the refusal and getting transport(-999).
  A5 `--only 22,23,24` on the committed head: caught 3/3 by fetchTableOverEveryResumeFileAndServer(); 23 and 24 are
     the red demonstration of the new unplayed-steps field.
  A6 `--prove-floor` OK at 24; check-safety-disclaimer, check-mutate-population, check-line-cap, check-pins-yaml,
     queue-check all OK; 300-line cap held on every touched file.
- 2026-10-09T23:25:00Z IMPLEMENTED on 4eaa0b1b (agent/claude-opus-5). CorpusDownloadDelegate: dataTask.cancel() on the
  line after both completionHandler(.cancel) sites, the type comment says why (104 lines). RULING ADDED (R6), from
  a measurement: the first cold run of the new table with R2 alone (the stub pause of 100 ms after every step)
  recorded 3 issues, the absent-prefix rows of missing, wrongRange and unwritable, each `unplayed: [1]` vs `[2]`
  / `[3]` vs `[4]` - the cancel issued on the response arrived after the 100 ms pause, so the stub had played one
  more step (two warm re-runs then passed: a timing race, not a defect, but CI is a loaded box). R6: a script
  marks where it expects the cancel with a new step `.awaitCancel`; the stub delivers nothing there, waits up to
  `patience` (5 s) for stopLoading() and only then plays on, so a refusal that cancels is never outrun and one that
  does not is seen (5 s later) in `unplayed()`. The expectation is a function of the row: the steps after the
  mark (none when the script has no mark). Marks: missing and wrongRange after the response, unwritable after its
  response, long after its extra byte, and the stub meta-test after its first chunk (`unplayed() == [3]`).
  Touched suites, own scratch: `Test run with 7 tests in 2 suites passed after 8.452 seconds`.
  A1 awk over CorpusDownloadDelegate.swift: `completionHandler(.cancel) sites=2 followed by dataTask.cancel()=2`.
  A3 table narrowed to [Server.missing, .wrongRange] (uncommitted, restored; Sources at HEAD 4eaa0b1b),
     `--only 22` 23:12:57Z-23:14:40Z: `caught 22 the session's cancel error outranks the refusal that caused it by:
     fetchTableOverEveryResumeFileAndServer()`, `MUTATE OK caught=1/1` (MISSED before: 22:28:47Z-22:39:23Z above).
  A4 the swap applied by hand (corpusfetch_mutations entry 22, restored byte-equal) over the whole table,
     23:15:50Z-23:17:08Z: `fetchTableOverEveryResumeFileAndServer() failed ... with 16 issues` = four servers x the
     four prefixes that send a request, each getting transport(code: -999): want status(404), longBody(4096),
     status(206), transport(-3003) (T-0305 measured 4, the long rows only).
  A5 `--only 22,23,24` 23:06:55Z-23:12:57Z: caught 22, 23 and 24 each `by: fetchTableOverEveryResumeFileAndServer()`,
     `MUTATE OK caught=3/3` - 23 and 24 are the new field seen red (the response plays on, `unplayed: []`).
  A6 on 4eaa0b1b: `--prove-floor` -> `FLOOR PROOF OK: 7 of 7 arms refused and the control did not` (floor 24);
     check-safety-disclaimer rc=0 (digest row re-approved: CorpusDownloadDelegate.swift ae6eab63...7c7f52);
     check-mutate-population `P-PROC-06: every added module is covered or allowlisted; the floor of 147 holds` rc=0;
     check-line-cap `P-SRC-02: 563 Swift files tracked (Sources=274, Tests=202, apps/ios=87), none over 300 lines`;
     check-pins-yaml `PINS-YAML ok pins=50 fields=403`; queue-check `QUEUE OK (342 tasks)`. Line counts: delegate
     104, stub 140, table 238, corpusfetch_mutations.py 120.
  NOT RUN: Darwin. On Darwin the .cancel disposition already cancels, so 23 and 24 would be unobservable there and
  the explicit cancel is a no-op second cancel of a cancelling task; the root package has no Darwin swift test here.
- 2026-10-09T23:43:00Z FINAL PRE-REVIEW (agent/claude-opus-5): origin/main merged at c0325495 (main had moved
  through T-0351 / T-0352 / T-0345 queue and ops commits; `git diff 4eaa0b1b c0325495 -- Sources Tests ops/mutate
  ops/lib/check-safety-disclaimer-linked-digests.txt` is empty, so A3-A5 carry over byte-for-byte). Re-run on
  c0325495, 23:27:26Z-23:42:35Z: A1 `sites=2 followed=2`; A2 `Test run with 7 tests in 2 suites passed after
  10.767 seconds`; A6 check-safety-disclaimer rc=0, check-mutate-population `the floor of 147 holds` rc=0,
  check-pins-yaml `PINS-YAML ok pins=50 fields=403` rc=0, queue-check `QUEUE OK (343 tasks)` rc=0, check-line-cap
  `P-SRC-02: 563 Swift files tracked (Sources=274, Tests=202, apps/ios=87), none over 300 lines` rc=0. PR #237
  opened; gh pr checks 237 on c0325495: core pass 4m57s, pins-source-only pass 2m58s.
