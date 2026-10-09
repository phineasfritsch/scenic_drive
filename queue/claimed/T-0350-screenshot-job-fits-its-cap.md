---
id: T-0350
title: ios-screenshot never dies at its 30-minute cap on a slow runner - the shots split across parallel jobs (or the per-shot settle trimmed by measurement), each job well under its own cap, one artifact set the owner downloads
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T18:40:31Z
lease_expires_at: 2026-10-10T02:40:31Z
worktree: .worktrees/T-0350
branch: task/T-0350
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, ops/lib/, queue/]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: [T-0346]
verify: [ops/check-pins]
acceptance:
  - "MEASURED FIRST and quoted in the Log (2026-10-09T18:48:36Z): 12 runs 37918396647..37972624773, per step and per shot by kind, the fixed (non-capture) cost per job, and main's artifact file list (run 37970447087, head 2e780fbf, an ancestor of main with no ios-screenshot.yml or apps/ios diff since: one artifact ios-screenshots, 38 PNGs)"
  - "The capture runs as a matrix of the ONE job simulator-screenshot over look: [light, dark, ax5], each leg shooting only its own pass (light and dark 16 shots each, ax5 the 6 plan cards), runs-on macos-15 and timeout-minutes 30 unchanged per leg; a job merge-screenshots (needs simulator-screenshot) merges the legs into ONE artifact named ios-screenshots and deletes the per-leg ones"
  - "In one green ios-screenshot run on task/T-0350 every job's duration (started_at..completed_at from the jobs API) is quoted; the WORST simulator-screenshot leg is under 1080 s (60% of its 30-minute cap) and merge-screenshots under 60% of its own cap"
  - "That run lists exactly one artifact, ios-screenshots, and its file list equals main's 38 names exactly (sorted diff empty) - the owner's download unchanged in shape"
  - "python ops/lib/check-ios-compile-guardrails.py is seen RED against the pre-change workflow with the new pinned structure (a first difference named), then green on the final file; --prove-red OK with every new T-0350 row red by name and the shipped file green; check-screen-rehearsals.py, bash ops/lib/check-map-attribution (P-ATTR-01), ops/lib/check-pins-yaml and ops/queue-check green on the merged head"
---
## Brief

T-0346 owner stillOpen 3 (PR #230): the screenshot job's 30-minute cap is fragile - the baseline 32 shots at ~31 s
each take ~27 min, T-0325's run took 26 min, and T-0346's 38-shot run 37954789863 was cancelled at the cap before
upload (R2 then cut the plan-sheet settle to 6 s; the 38-shot run now takes 17m55s-18m48s). Every new screen or text
size pushes it back toward the cap. MEASURE FIRST: per-shot wall time by kind (map vs plan fixture vs drive), runner
variance across the last ~10 runs, what the guard ops/lib/ios_screenshot_pinned.py pins (CAPTURE_RUN, the cap). Then
RULE (a matrix of jobs by pass - light/dark/AX5 - with one merged artifact, or measured settle times per kind) and
write the acceptance: every job's measured worst case under 60% of its cap, the pinned guard rows raised by name and
seen red then green, the owner's download unchanged in shape.

## Log
- 2026-10-09T18:39:48Z filed by agent/claude-opus-5 (orchestrator) from T-0346 stillOpen 3.
- 2026-10-09T18:40:31Z claimed by agent/claude-opus-5; lease until 2026-10-10T02:40:31Z
- 2026-10-09T18:41:26Z renumbered T-0348 -> T-0349 by agent/claude-opus-5 (orchestrator): task/T-0343 holds a T-0348.
- 2026-10-09T18:42:35Z renumbered T-0349 -> T-0350 by agent/claude-opus-5 (orchestrator): task/T-0343 also holds a T-0349 (T-0350 checked free on main and every open task branch).
- 2026-10-09T18:48:36Z MEASURED (agent/claude-opus-5) by DerivedData/t0350/measure.py (scratch): the jobs API and each job log of the last 12 runs, a shot timed from its `simctl launch` pid line to the next one. PER STEP (s): toolchain 28-192, choose+boot 78-128, build 231-472, capture 553-651 in the five 38-shot runs since R2 (37959095574 570, 37962723763 603, 37965740394 553, 37970447087 615, 37972624773 651), 729-970 in the older 32-shot runs at 15 s everywhere, 1171+ in the cancelled 37954789863. JOB total 1067-1547 s; the fixed non-capture cost per job (total - capture) 377-657 s (37929398054 377 ... 37962723763 657, 37959095574 655, 37918396647 646). PER SHOT by kind, 12 runs: home-map n=72 mean 20.8 median 18.6 max 61; settings n=24 mean 21.0 max 44; paywall 19.3/max 30; surprise 20.5/max 29; drive 19.5/max 28; onboarding 18.4/max 22; disclaimer 18.6/max 26; legal n=17 mean 23.9 max 57; plan (6 s settle, the five post-R2 runs) mean 8.1-8.7 per run, max 11; plan-ax5 n=25 mean 10.8 median 8.7 max 21. So a shot is its settle + ~3.5 s (launch, ps, screenshot, terminate) on a normal runner and up to ~4x that on a slow one; RUNNER VARIANCE is the risk, not the shot count - the same 38 shots took 553-651 s, and a slow runner (37925466654: toolchain 192 s, capture 970 s for 32 shots) adds minutes to every step at once. GUARD: ops/lib/ios_screenshot_pinned.py pins the whole workflow by equality (expected()), the capture run text CAPTURE_RUN, `timeout-minutes: 30`, and check-ios-compile-guardrails.py's named_problems REFUSES `strategy` on any job and allows only actions/checkout@v4 and actions/upload-artifact@v4. Main's artifact: run 37970447087, one artifact ios-screenshots (12073003 bytes), 38 PNGs, flat: {disclaimer,drive,legal,onboarding,paywall,settings,surprise}-{light,dark}, home-{light,dark}-{collapsed,medium,fastest}, plan-{preview,nothingPretty,offered,loop,trip,saved}-{light,dark,ax5}.
- 2026-10-09T18:48:36Z RULINGS (agent/claude-opus-5), before code. R1 SPLIT, not trim: the 15 s settle covers a cold launch, the remote demo style and its first tiles, and no log line tells when the tiles landed, so a shorter map settle cannot be MEASURED from here - trimming it is a guess on owner-visible evidence; the plan settle was already cut to 6 s by T-0346 R2. R2 a MATRIX of the existing job over look: [light, dark, ax5] (the Brief's preferred shape): light/dark ~16 shots ~245 s, ax5 6 shots ~55 s on a normal runner, so the worst leg is fixed cost (<= 657 s seen) + ~245 s, about 15 min, half the cap; a slow runner at 1.6x on both is ~17.5 min, still under 18. Splitting further buys little: every leg pays the 6-11 minute fixed cost (toolchain, boot, build) again. R3 the leg reads its pass from the matrix by keeping the loop and its body byte-identical - `for LOOK in ${{ matrix.look }}; do` - so the shot table, names and per-shot arguments do not move (a literal matrix value, no untrusted input). R4 ONE artifact: each leg uploads ios-screenshots-<look> (retention 1 day) and a second job merge-screenshots runs actions/upload-artifact/merge@v4 (the same repository and major as the allowed upload action) into ios-screenshots, 7 days, delete-merged: true, so the run lists one artifact of 38 flat PNGs exactly as on main. The merge job runs on macos-15 with the one pinned env: widening the runner allowlist to ubuntu for a 30-second job would loosen a guard for pennies. R5 the guard: ALLOWED_USES gains actions/upload-artifact/merge@v4, and named_problems' `strategy` refusal is relaxed to exactly the pinned strategy (ios_screenshot_pinned.STRATEGY); any other strategy, on either workflow, stays refused by name, and ios-compile with the pinned one still fails the equality net. check-ios-compile-guardrails.py is at 304 lines already, so its edit is line-neutral; the new rows live in ios_screenshot_pinned.py. R6 fail-fast: false - one crashed pass must not cancel the other two passes' evidence; the run is still red and merge-screenshots does not run.
