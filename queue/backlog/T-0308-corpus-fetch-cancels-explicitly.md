---
id: T-0308
title: The corpus fetcher cancels a refused response explicitly (dataTask.cancel() beside completionHandler(.cancel)) so the refusal path completes the same way on Darwin and on swift-corelibs-foundation, and the 404 / wrong-range rows catch the error-order swap off Darwin too
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
