---
id: T-0384
title: The shell's "Plan a drive" pill has no Dynamic Type cap - at AX5 it draws at full accessibility size above the capped home
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T00:28:31Z
lease_expires_at: 2026-10-18T00:28:31Z
worktree: .worktrees/T-0384
branch: task/T-0384
exclusive: []
touches: [apps/ios/ScenicDrive/ScenicDriveApp.swift, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, queue/]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0378, T-0376]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0378 (PR #274) fixed the AX5 medium crash by capping the home's chrome and sheet at DynamicTypeSize.xxxLarge
(the disclaimer keeps the user's own size). Its author recorded the gap left behind: the shell's "Plan a drive"
pill (ScenicDriveApp.swift, the safeAreaInset T-0376 added) is outside that cap and still draws at AX5 size.

MEASURE: the AX5 shots on main (home-ax5-collapsed, home-ax5-medium) - how tall the pill is and what it pushes.
RULE whether the pill shares the home's cap (one binding - the same cap value, not a second literal) or gets
its own accessibility layout; the pill must stay a >= 44 pt target and readable. Re-approve the shell's frozen
lines and pinned digest in the same commit. Acceptance: ios-screenshot success; home-ax5-collapsed and
home-ax5-medium looked at and quoted (pill, chips, credit, conditions line, button visible, no overlap); light/dark
home unchanged.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0378 stillOpen (the shell pill has no Dynamic Type cap).
- 2026-10-17T00:28:31Z claimed by agent/claude-opus-5; lease until 2026-10-18T00:28:31Z
- 2026-10-17T00:32:24Z MEASURE (agent/claude-opus-5). Shots of ios-screenshot run 38969965368 (task/T-0378 head
  c78b78cd, the last home-touching shot run before main bf46585d; T-0379/T-0383 did not touch the home or shell),
  downloaded to .artifacts/t0384-main/ios-screenshots, 1206x2622 px = 402x874 pt at 3x, LOOKED AT:
  - home-light-collapsed: the pill is ~44 pt tall (px 210-341) and ~122 pt wide ("Plan a drive" on one line); the
    chip band starts ~8 pt under it (px 354).
  - home-ax5-collapsed: the pill is ~63 pt tall (px 210-400) and ~301 pt wide - three quarters of the screen, text at
    full AX5 headline size; it pushes the chip band down ~20 pt (px 413 vs 354), where the chips themselves already
    draw at the home's xxxLarge cap ("West-/wood/loop", "SF/Peninsu-/la" wrap). Credit, sheet title, three cards,
    conditions line and Open in Apple Maps are visible; nothing overlaps; the map keeps ~ px 520-1075.
  - home-ax5-medium: the same pill (~63 pt x ~301 pt) and the same 20 pt push; the map window above the credit is
    ~ px 520-780 (~87 pt), the sheet with its road list below. Nothing overlaps.
  So the pill is the one piece of the home's top chrome above the cap: it is the tallest and widest thing on the
  map and it eats the map window at both detents.
- 2026-10-17T00:32:24Z RULINGS (agent/claude-opus-5).
  - R1 The pill shares the home's cap; no own accessibility layout. It is chrome over the home exactly like the chip
    band that T-0378 capped at xxxLarge, and one cap for the whole top chrome keeps the pill and the chips in the
    same type scale. At xxxLarge the headline is about the chips' size, the one-line label still fits, and the
    frame keeps minHeight 44 (PlanDriveButton unchanged), so it stays a >= 44 pt target and readable.
  - R2 One binding. The cap value lives once, as `public enum HomeTypeSize { public static let cap }` in the new
    FeatureScenicHome/HomeTypeSize.swift (ScenicHomeScreen.swift is at 299 of 300 lines, so no room there; one
    type per file). ScenicHomeScreen's `.dynamicTypeSize(...DynamicTypeSize.xxxLarge)` becomes
    `.dynamicTypeSize(...HomeTypeSize.cap)` and the shell applies `.dynamicTypeSize(...HomeTypeSize.cap)` to the
    PlanDriveButton. After the change `DynamicTypeSize.xxxLarge` appears in apps/ios only in HomeTypeSize.swift
    (HomeSheet's `typeSize > .large` threshold is a different value and stays).
  - R3 The cap goes on the pill only, BEFORE its `.sheet(isPresented: $isPlanning)`, never on the shell's whole
    `home`: capping the home from outside would cap ScenicHomeScreen's `userTypeSize` read and so the safety
    disclaimer (T-0378 R2 keeps it at the user's own size), and would cap Settings, the corpus download sheet and
    the plan sheet - none of which this task may change. The plan sheet is attached outside the cap modifier.
  - R4 Plan vs reality: the Brief names the pill as "the safeAreaInset T-0376 added"; that is what the code shows
    (ScenicDriveApp.swift line 69-74). No other disagreement.
  - R5 Re-approval in the same commit as the code: PINNED_SHELL_DIGEST and the shell's PINNED_APP_SWIFT row,
    ScenicHomeScreen.swift's PINNED_FEATURE and PINNED_APP_SWIFT rows, new HomeTypeSize.swift rows in both lists;
    the frozen shell block gains the cap line and the frozen home block's cap line is re-typed.
- 2026-10-17T00:40:17Z CODE + RED/GREEN (agent/claude-opus-5). New FeatureScenicHome/HomeTypeSize.swift (7 lines,
  `public static let cap = DynamicTypeSize.xxxLarge`); ScenicHomeScreen's cap line now `.dynamicTypeSize(...HomeTypeSize.cap)`;
  the shell's pill `PlanDriveButton(action: { isPlanning = true })` gains `.dynamicTypeSize(...HomeTypeSize.cap)` on
  the next line, before its `.sheet(isPresented: $isPlanning ...)`.
  - RED 1 (code only): `bash ops/lib/check-safety-disclaimer` rc=1 "P-SAFE-03: a frozen render block changed:
    ScenicHomeScreen's body ... line 40 of 41 ... approved `.dynamicTypeSize(...DynamicTypeSize.xxxLarge)`, found
    `.dynamicTypeSize(...HomeTypeSize.cap)`" and "the app shell ScenicDriveApp line 38 of 55 ... approved
    `.sheet(isPresented: $isPlanning, ...) {`, found `.dynamicTypeSize(...HomeTypeSize.cap)`".
  - RED 2 (frozen lines re-typed, digests not): rc=1 "P-SAFE-03: the pinned render surface changed:
    FeatureScenicHome's file set is not the approved one: added HomeTypeSize.swift."
  - GREEN (digests typed: HomeTypeSize.swift 3e0bd071..., ScenicHomeScreen.swift 2ff8efdc..., PINNED_SHELL_DIGEST
    and the shell row 4040765f...): rc=0 "37 feature file(s), shell, footer pinned (-pinned); ... all 114 app .swift".
  - A7: `grep -rn "DynamicTypeSize.xxxLarge" apps/ios` prints one line, HomeTypeSize.swift:6. `wc -l`:
    ScenicHomeScreen.swift 299, ScenicDriveApp.swift 89, HomeTypeSize.swift 7.
  - Gates on this head before merge: check-mutate-population, check-store-links, check-ios-compile-guardrails,
    check-map-attribution, check-pins-yaml, check-exec-bits all rc=0.

## Acceptance
- A1 RED first: the Swift edits without the re-approval commit make `bash ops/lib/check-safety-disclaimer` exit
  non-zero naming the changed files; then green with the rows typed.
- A2 `gh workflow run ios-compile.yml --ref task/T-0384` on the final head: success.
- A3 `gh workflow run ios-screenshot.yml --ref task/T-0384` on the final head: success, all legs.
- A4 home-ax5-collapsed.png of that run LOOKED AT and quoted: the pill drawn smaller than main's ~63 x ~301 pt and
  >= 44 pt tall, one-line readable; chips, credit, conditions line and Open in Apple Maps visible, nothing overlaps.
- A5 home-ax5-medium.png of that run LOOKED AT and quoted: the same.
- A6 home-light-collapsed and home-dark-medium of that run beside run 38969965368's: the same layout (the cap is a
  no-op at the default size).
- A7 `grep -rn "DynamicTypeSize.xxxLarge" apps/ios` prints exactly one line, in HomeTypeSize.swift.
- A8 the bare gates of the task exit 0 on the merged head; `wc -l` of ScenicHomeScreen.swift, ScenicDriveApp.swift
  and HomeTypeSize.swift <= 300.
