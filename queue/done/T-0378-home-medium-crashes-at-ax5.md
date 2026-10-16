---
id: T-0378
title: The home at the medium detent crashes at AX5 (accessibility XXXL) - find the cause, fix it, and add home-ax5-medium back to the ax5 screenshot pass
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T21:15:30Z
lease_expires_at: 2026-10-17T21:15:30Z
worktree: .worktrees/T-0378
branch: task/T-0378
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, queue/]
pins_affected: [P-ATTR-01, P-A11Y-01, P-SAFE-03]
reviewer: agent/rv1-t-0378
depends_on: [T-0376]
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by T-0376's author. `xcrun simctl launch ... -homeDetent medium -menuRow default -screen home` with
`-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL` (the ios-screenshot ax5 pass) dies
within 15 s: "ios-screenshot: ScenicDrive (pid ...) is not running 15s after the ax5 medium launch - it crashed".
Measured three times, the same way each time: run 38882932440 attempt 1 and attempt 2 on task/T-0376 c477e258
(the pill stacked above the chips), and a control run 38887739175 on fd6d5452, which is task/T-0376 with main's
shell layout restored (the pill as a top-leading overlay). So the crash is not T-0376's. At AX5 the collapsed home
launches and is captured (home-ax5-collapsed.png written in all three runs); light and dark medium do not crash.
T-0376 left `medium` out of the ax5 LIST so that the pass can stay green. This task adds it back.

MEASURE FIRST: get the crash report (for example a step that copies `~/Library/Logs/DiagnosticReports/ScenicDrive*`
from the runner, or `log show` for the simulator, uploaded on failure) and quote its top frames in the Log before
ruling. Candidates nobody has checked yet: the medium sheet is taller than the screen at AX5 (the road list, facts
and caption all use `fixedSize` vertically) inside ScenicHomeScreen's VStack. That pushes the chip band and the
credit band past the window edges, and the measured `chipBandBottom`/`creditBandTop` reach MapView and
MapRouteCoordinator's fit and ornament margins. RULE the fix, which may be a scrolling medium sheet. Keep the credit
visible at every detent (P-ATTR-01) and the conditions line visible at both detents (P-SAFE-03).
Acceptance: `medium` back in the ax5 LIST (workflow + ios_screenshot_pinned.py, with a prove-red row), ios-screenshot
success, and home-ax5-medium looked at and quoted: credit, conditions line and button visible, no overlap.

## Log
- 2026-10-16T10:58:18Z filed by agent/claude-opus-5 (T-0376 owner). Ids checked on main and on all 271 remote task/*
  branches: the highest was T-0377.
- 2026-10-16T11:26:00Z scope widened by agent/claude-opus-5 (T-0376 owner). home-ax5-collapsed.png (run 38890737661, af793caf)
  shows the whole home overflowing at AX5: the chip band runs up under the status bar with labels wrapping a few
  letters per line, the credit takes six lines, and the collapsed sheet's title is drawn over its menu chips. T-0376
  R8 holds the shell's "Plan a drive" pill on screen with a fixed home frame. The home's own overflow is this task's.
- 2026-10-16T21:15:30Z claimed by agent/claude-opus-5; lease until 2026-10-17T21:15:30Z
- 2026-10-16T21:23:10Z MEASURED (agent/claude-opus-5, owner). The failure-only step the Brief asks for already exists:
  `why it failed` (`if: failure()`) in .github/workflows/ios-screenshot.yml runs `find ~/Library/Logs/DiagnosticReports
  -name 'ScenicDrive*'` and `simctl spawn booted log show --last 5m --predicate 'process == "ScenicDrive"'`. Its output
  on the control run 38887739175, job 116929500894 (ax5 leg, fd6d5452), read with `gh run view --job --log`:
  - launch: `10:42:36.355 com.phineasfritsch.scenicdrive: 25185` (the ax5 medium launch);
  - `find` printed NOTHING: no ScenicDrive crash report on the runner;
  - the process's LAST log line, 1.18 s after the launch, on its main thread 116be:
    `10:42:37.532 E ScenicDrive[25185:116be] (Metal) -[MTLTextureDescriptorInternal validateWithDevice:], line 1416:
    error 'Texture Descriptor Validation MTLTextureDescriptor has height (10006) greater than the maximum allowed size
    of 8192.'` - nothing after it; `ios-screenshot: ScenicDrive (pid 25185) is not running 15s after the ax5 medium
    launch - it crashed` at 10:42:51.
  The device: home-ax5-collapsed.png of run 38954903799 (task/T-0379 b28de469, main's home) is 1206x2622 px, 3x, so
  402x874 pt; a texture 10006 px tall is 3335 pt, 3.8 windows. That PNG, LOOKED AT: the chip band's three drive chips
  wrap two or three letters per line ("Sa/ddl/e/Pea/k") and run ~1000 px; the credit takes six lines (~750 px); the
  sheet shows its grabber and the first line of the title and is cut by the window's bottom edge - the conditions line
  and the button are OFF SCREEN at AX5 collapsed on main today. home-light-medium.png of the same run: at the default
  size the medium sheet already reaches the window's bottom (the details end ~120 px above it).
- 2026-10-16T21:23:10Z RULINGS (before code).
  - R1 (Brief vs reality: "quote its top frames"). There are no frames: no crash report was written (the `find` above
    printed nothing). The measured cause is the Metal validation abort quoted above, on the main thread. Ruled cause:
    at AX5 medium the home's overlay VStack (chips, credit, HomeSheet with every text `fixedSize` vertically) lays out
    far taller than the window; the ZStack takes that height and MapView - MapLibre's Metal view, the only in-process
    Metal drawer on the home - is handed a drawable over 8192 px. Collapsed at AX5 is shorter (no details) and stays
    under the limit, which is why only medium dies. No workflow change is needed to MEASURE; the step stays as it is.
  - R2 (the fix). The home cannot fit at AX5 by scrolling the details alone: the chips and the credit by themselves
    take ~1750 of the 2622 px (measured above), and the conditions line and the button live inside `sheetSummary`,
    whose lines are frozen by ops/lib/check-safety-disclaimer-sheet (s2) - not in this task's touches - so they
    cannot be pinned outside a scroll view. Ruled: (a) the home screen's ZStack caps Dynamic Type at
    `DynamicTypeSize.xxxLarge`, the largest non-accessibility size, with one `.dynamicTypeSize(...)` at the end of
    ScenicHomeScreen's body; the disclaimer sheet it presents is handed back the user's OWN size (read from the
    environment above the cap), so the safety text is never capped; (b) HomeSheet, at any size above `.large`, puts
    the medium details in a ScrollView 15% of the window tall (`containerRelativeFrame`); at `.large` and below it is
    the unchanged `details()`, so the light and dark shots (default size) are unchanged. The credit stays the
    sheet's sibling directly above it at every detent (P-ATTR-01 limb (h) lines untouched) and the conditions line
    stays in the summary at both detents (P-SAFE-03 (s2) untouched). The frozen whitelists in
    ops/lib/check-safety-disclaimer-frozen are re-approved in the same commit as the code.
  - R3 (pins_affected names P-A11Y-01). No such pin: `grep -rn A11Y-01 pins` prints nothing. Nothing to keep; the AX5
    screenshot is the only accessibility evidence.
  - R4 (the LIST). `medium` goes back into the ax5 LIST after `collapsed`, in the workflow and in
    ops/lib/ios_screenshot_pinned.py's AX5_LIST, with a prove-red row "T-0378: the AX5 medium shot dropped". RED
    first: the workflow edited alone must fail check-ios-compile-guardrails.py by name before the pinned copy follows.
- 2026-10-16T21:31:48Z RED then GREEN (R4), by name.
  - RED: ios-screenshot.yml's ax5 LIST edited alone to `collapsed medium preview ...`; `python
    ops/lib/check-ios-compile-guardrails.py` exit=1: `IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-screenshot.
    steps[4].run: differs from the pinned value (compared by equality)` / `IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s)
    gone in ios-screenshot.yml`.
  - GREEN: ios_screenshot_pinned.py's run text and AX5_LIST follow; the same command exit=0 (`IOS-COMPILE-GUARDRAILS
    OK: ios-screenshot.yml equals the pinned workflow ...`). `--prove-red` exit=0: `[red rc=1] ios-screenshot.yml:
    T-0378: the AX5 medium shot dropped (the crash at the largest text size unseen again): ... differs from the pinned
    value` and `PROVE-RED OK: 98 mutations red, 6 legitimate spellings green over 2 workflows, 0 unexpected result(s)`.
  - The Swift edit, before its whitelists: `bash ops/lib/check-safety-disclaimer` exit=1, `P-SAFE-03: a frozen render
    block changed: HomeSheet's struct line 6 of 62 ... found @Environment(\.dynamicTypeSize) private var typeSize` and
    `ScenicHomeScreen's body ... line 38 of 39 ... found .dynamicTypeSize(userTypeSize)`; then, the frozen lists
    edited, `the pinned render surface changed: HomeSheet.swift ... sha256 9be4c20e...` and `ScenicHomeScreen.swift
    ... 8b8b0823...`; both digests re-approved (`sed 's/\r$//' FILE | sha256sum` agrees): exit=0.
  - c78b78cd pushed; ios-compile run 38969961170 and ios-screenshot run 38969965368 dispatched.
- 2026-10-16T21:52:41Z ACCEPTANCE re-run on c78b78cd (`git fetch origin` in the main checkout: origin/main 14e1aab2
  is already an ancestor, nothing to merge).
  - A1 ios-screenshot 38969965368: `completed success`, dark=success light=success ax5=success merge-screenshots=success.
    The ax5 leg launched `-homeDetent medium` at AX5 and the process was alive after the settle and after the capture.
  - A2 home-ax5-medium.png LOOKED AT: the chip band (labels wrap by syllable at most, "West-/wood/loop") under the
    shell's pill; the map with the route; the credit `© MapLibre · Natural Earth · © OpenStreetMap contributors` in two
    lines directly above the sheet; the sheet's title in two lines, the three menu chips, `Conditions change. Verify
    locally.`, the orange `Open in Apple Maps` button, then the road list in the scrolling band, cut by the band's
    edge at its fourth line (scrolls). Nothing drawn over anything; nothing under the status bar.
  - A3 home-ax5-collapsed.png LOOKED AT: the same chips, the route fitted between the chip band and the credit, the
    credit in two lines, the title, the menu chips, the conditions line and the button above the home indicator.
    Main's run 38954903799 showed only the title's first line (conditions line and button off screen).
  - A4 home-light-medium and home-dark-medium LOOKED AT beside 38954903799's light medium: the same layout line for
    line (the unscrolled details, the caption ending "yet."); paywall-light LOOKED AT (Scenic Drive Pro, Subscription
    Unavailable, Terms of Use / Privacy Policy). PNG sizes old/new: light-collapsed 512971/514067, light-medium
    701427/702013, dark-collapsed 393868/394930, dark-medium 470243/471019, paywall-light 131999/131666,
    paywall-dark 130484/129728 (the clock differs).
  - A5 `python ops/lib/check-ios-compile-guardrails.py` exit=0; `--prove-red` exit=0, the T-0378 row red (quoted above).
  - A6 ios-compile 38969961170: `completed success`.
  - A7 bare gates exit=0: check-safety-disclaimer, check-map-attribution, check-line-cap (`694 Swift files ... none over
    300 lines`), check-exec-bits, check-pins-yaml, ios_screenshot_pinned, check-store-links, check-telemetry-emit-sites,
    check-mutate-population, check-mutate-only, queue-check (`QUEUE OK (373 tasks)`). `wc -l`: HomeSheet.swift 97,
    ScenicHomeScreen.swift 299, ios_screenshot_pinned.py 296.
  - GAP, recorded not fixed: the shell's "Plan a drive" pill (ScenicDriveApp, outside this task's touches) is not
    capped and is still drawn at AX5 size above the chip band.
- 2026-10-16T22:49:04Z REVIEW PASS by agent/rv1-t-0378 (not the owner) on origin/task/T-0378 9c9dbd74 (PR #274).
  - A1 ios-screenshot 38969965368 (headSha c78b78cd; 9c9dbd74 differs from it only under queue/): conclusion success,
    simulator-screenshot (dark)=success (light)=success (ax5)=success, merge-screenshots=success.
  - A2 home-ax5-medium.png downloaded and LOOKED AT: chips, the credit `(c) MapLibre . Natural Earth . (c)
    OpenStreetMap contributors` in two lines directly above the sheet, title in two lines, the three menu chips,
    `Conditions change. Verify locally.`, the orange `Open in Apple Maps` button, the road list in the scroll band cut
    at its edge. Nothing drawn over anything.
  - A3 home-ax5-collapsed.png LOOKED AT: route, credit, title, menu chips, conditions line and button all on screen.
  - A4 home-light-medium.png LOOKED AT: unscrolled details down to the caption ending "yet." (default size unchanged).
  - A5 `python ops/lib/check-ios-compile-guardrails.py` rc=0; `--prove-red` rc=0: `[red rc=1] ios-screenshot.yml:
    T-0378: the AX5 medium shot dropped ...` / `PROVE-RED OK: 98 mutations red, 6 legitimate spellings green over 2
    workflows, 0 unexpected result(s)`.
  - A6 ios-compile 38969961170 success; `gh pr checks 274`: core pass, pins-source-only pass.
  - A7 bare gates rc=0: check-safety-disclaimer, check-ios-compile-guardrails, check-map-attribution, check-line-cap
    (`694 Swift files ... none over 300 lines`), check-pins-yaml, check-exec-bits, check-store-links,
    check-telemetry-emit-sites, check-mutate-population, check-mutate-only, queue-check (`QUEUE OK (373 tasks)`).
    `wc -l`: ScenicHomeScreen.swift 299, HomeSheet.swift 97.
  - Own mutants, each with BOTH digest rows re-approved, `bash ops/lib/check-safety-disclaimer`:
    RM1 `.dynamicTypeSize(userTypeSize)` deleted (the disclaimer capped): rc=1 `P-SAFE-03: a frozen render block
    changed: ScenicHomeScreen's body ... line 38 of 41 ... approved .dynamicTypeSize(userTypeSize), found }`. RED.
    RM2 `if typeSize > .large {` -> `> .xxxLarge` (the band never engages under the cap): rc=1 `P-SAFE-03: a frozen
    render block changed: HomeSheet's struct line 17 of 70 ... approved if typeSize > .large {, found if typeSize >
    .xxxLarge {`. RED.
  - `git merge-base --is-ancestor origin/main origin/task/T-0378` rc=0 (after `git fetch origin`).
  - Recorded, not blocking: the disclaimer at AX5 is not in the ax5 shot list, so "the safety text is never capped"
    rests on code reading (RM1 shows the line is frozen); the shell's "Plan a drive" pill is uncapped at AX5 (owner's
    recorded gap, no task filed); the cap at xxxLarge is a product call an accessibility layout could replace.

## Acceptance
- A1 `gh workflow run ios-screenshot.yml --ref task/T-0378` on the final head: conclusion success, all three legs.
- A2 home-ax5-medium.png of that run LOOKED AT and quoted: the credit, the conditions line and the Open in Apple Maps
  button all visible, nothing drawn over anything.
- A3 home-ax5-collapsed.png of that run LOOKED AT: the same four things visible.
- A4 home-light-collapsed, home-light-medium, home-dark-medium, paywall-light and paywall-dark LOOKED AT beside run
  38954903799's: the same layout.
- A5 `python ops/lib/check-ios-compile-guardrails.py` exit 0; its `--prove-red` shows the T-0378 row red.
- A6 `gh workflow run ios-compile.yml --ref task/T-0378`: success.
- A7 the bare gates of the task exit 0 on the merged head; `wc -l` of HomeSheet.swift and ScenicHomeScreen.swift
  <= 300.
