---
id: T-0305
title: The app downloads and activates the places corpus - a URLSession CorpusFetcher, a first-run download sheet (resumable, Wi-Fi-only by default, progress), and openForLaunch on every cold launch, with the bundled fallback until a download lands
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [package-swift]
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/PlaceStore/, Tests/PlaceStoreTests/, apps/ios/Packages/ScenicApp/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PROD-05, P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0300, T-0294, T-0303]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where the manifest URL comes from (the same UserDefaults/config seam T-0294 R7 uses for the plan base URL; absent -> no download, the bundled fallback corpus stays - T-0270), which target owns URLSession (ScenicAPIClient beside URLSessionPlanTransport, Linux-buildable via FoundationNetworking), how the shell wires it without a feature target importing ScenicAPIClient (CLAUDE.md), and the Wi-Fi-only default + Settings toggle"
  - "URLSessionCorpusFetcher conforms to T-0300's CorpusFetcher; tested on Linux with a URLProtocol stub: a 200 body is streamed to the staging path exactly; a non-200, a short body and a dropped connection each throw a typed error and leave no staging file; resume uses a Range request when a partial staging file exists (table over 0 bytes / partial / complete-but-unverified)"
  - "The shell calls CorpusUpdater.openForLaunch(isColdLaunch: true) before the first PlaceStore open, and the home's searches read the activated corpus when one exists, else the bundled fallback - a ScenicKit/PlaceStore-level test over {no download, pending, activated, rejected} chooses the right file by full equality"
  - "The download sheet shows progress, never blocks Surprise Me on the fallback corpus, keeps AttributionFooter visible on every map surface (P-ATTR-01: any new sheet is full-height or gets a typed whole-line approval in check-map-attribution-sheet, never a widened pattern), and ios-compile + ios-screenshot pass on the head"
  - "Every new or changed Sources/ and non-Swift apps/ios file re-approves its row in ops/lib/check-safety-disclaimer-linked-digests.txt (memory sources-digest-pin); a mutation population for the fetcher's error/resume logic with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Runtime lifecycles, First run + Corpus OTA: "download sheet: Bay Area PMTiles + corpus, resumable, progress; bundled
tiny fallback corpus so the app is never empty; Wi-Fi-only default with a Settings toggle". T-0300 shipped the decision/
verify/activate core (PlaceStore CorpusUpdater, CorpusFetcher protocol); this task is the app half for the CORPUS only.
PMTiles download is a later task. The R2 manifest is not published yet (owner deploy), so tests use stubs.

## Log
- 2026-10-07T19:09:58Z filed by agent/claude-opus-5 (orchestrator) from T-0300 O11 and the milestone gap map (M4).
