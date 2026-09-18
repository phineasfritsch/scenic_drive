---
id: T-0153
title: P-SAFE-03, the disclaimer pin, transcribed into PINS.yaml with a real assertion, and a persistent "Conditions change. Verify locally." line on the home screen before a second TestFlight tester
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T23:04:05Z
lease_expires_at: 2026-09-19T07:04:05Z
worktree: .worktrees/T-0153
branch: task/T-0153
exclusive: []
touches: [pins/PINS.yaml, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, ops/lib/]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "pins/PINS.yaml carries P-SAFE-03 with an assertion that runs on Linux today and was seen RED by name before the disclaimer existed (a structural check over Sources/FeatureScenicHome: the handoff call site is gated by a SafetyDisclaimer acknowledgement type and a persistent line is on the screen), then green; the run ids quoted"
  - "the disclaimer gates the FIRST handoff only (acknowledged once, stored on device) and a persistent line 'Conditions change. Verify locally.' stays visible on the home screen at every size; DesignTokens only, Dynamic Type, identifiers home.disclaimer / home.disclaimer.accept / home.conditions, 44 pt targets; ios-compile dispatch on the branch green with the run id quoted"
  - "the 16:13 panel drivers' round-3 strings, verbatim: title 'Skyline loop · starts and ends in San Francisco'; caption 'Preview build: one fixed Bay Area drive. The map doesn't show roads yet - tap below and it opens in Apple Maps.'"
  - "bash ops/lib/check-line-cap, bash ops/queue-check, bash ops/check-pins --source-only bare at the final commit"
---
## Brief

Carried from the 2026-09-18 02:45 panel (queue task 4, unfiled until now) and re-grounded at 10:13: on
task/T-0141 `git grep -iE 'disclaimer|budget|minute|ceiling' -- apps/ios` exits 1 - nothing under the app
mentions a disclaimer, and `pins/PINS.yaml` has no P-SAFE-03 (`grep -c P-SAFE-03 pins/PINS.yaml -> 0`).

The plan's pin: *P-SAFE-03 - the disclaimer gate blocks the first plan; the route screen has a visible
`SafetyDisclaimerDisplaying`* (call-graph + XCUITest, runs_on linux+mac). CLAUDE.md's product invariants
repeat it: "The safety disclaimer gates the first plan and stays visible on the route screen." The risk
table's mitigation for "sedan onto dirt/gated/closed road" names a blocking disclaimer AND a persistent
"Conditions change. Verify locally." line.

**Do:**
1. Transcribe P-SAFE-03 into `pins/PINS.yaml` with an assertion that can run on Linux today and fail for
   the reason it names: a source-level check that the type `SafetyDisclaimerDisplaying` exists under
   `apps/ios/Packages/ScenicApp/Sources/` and that every screen type under `Feature*/` that presents a route
   or a handoff conforms to it (anchor on the protocol name and the conformance list - identifiers, never a
   comment). `runs_on: [linux]` for the source half; the XCUITest half stays `pending:` on the first green
   Xcode Cloud run and is printed BY NAME by check-pins (see T-0149 on what `pending:` must mean).
2. A `DesignSystem` view carrying the persistent line `Conditions change. Verify locally.` in `fgMuted`,
   never hidden by a sheet detent, and its placement on `ScenicHomeScreen` beside the attribution footer.
   The full first-plan gate (the blocking disclaimer with acknowledgement) belongs to M4's Onboarding; this
   task ships only the persistent line and the pin skeleton, so that a second TestFlight tester never sees
   a handoff without it.
3. Demonstrated red: remove the conformance from the screen -> the pin's assertion names the screen.

Depends on T-0141 (PR #88). Do not open a second PR on `ScenicHomeScreen.swift` while its round 2 is under
review; T-0152 (copy) touches the same file - sequence them, do not stack them.

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 02:45 and 10:13 panels (grounded). Not started.
- 2026-09-18T23:04:01Z PROMOTED to ready/ by agent/claude-fable-5-1 (16:13 panel, grounded): the M1.5 tree is merged and
  compiles under Xcode 26.3, `grep -rli disclaimer apps/ios` is empty, and P-SAFE-03 is a CLAUDE.md product
  invariant with no assertion anywhere. Folded in, because they edit the same file: the two focus drivers'
  round-3 strings (the title omitted the START - SkylineRoute.swift says SF -> SF; the caption apologised for
  the map instead of framing the build). Duration stays off the screen (nobody has measured it); the
  straight-line distance the drivers asked for is T-0170's.
- 2026-09-18T23:04:05Z claimed by agent/claude-opus-5; lease until 2026-09-19T07:04:05Z
- 2026-09-18T23:16:34Z RULINGS by agent/claude-opus-5, before any code. Eight disagreements between the plan,
  this Brief, the code and the tree. Pointers, then the ruling.

  **R1 - scope: the Brief body says "pin skeleton + line only", the acceptance says "gates the FIRST
  handoff".** Brief `## Brief` item 2: *"The full first-plan gate (the blocking disclaimer with
  acknowledgement) belongs to M4's Onboarding; this task ships only the persistent line and the pin
  skeleton"*. Acceptance line 2: *"the disclaimer gates the FIRST handoff only (acknowledged once, stored on
  device) ... identifiers home.disclaimer / home.disclaimer.accept / home.conditions"*. The body was written
  at 17:55; the acceptance block was rewritten at the 23:04 promotion, three lines below it in the same file.
  CLAUDE.md Verification and this task's own header make the acceptance lines the contract. RULED: build the
  gate. The acknowledgement is stored on device only - `@AppStorage`, key `safety.disclaimer.acknowledged.v1`
  - no account, no server, nothing leaves the phone. The key is versioned so that a later change to what the
  user acknowledged can re-ask rather than inherit a stale yes.

  **R2 - `SafetyDisclaimerDisplaying` (a protocol) vs `SafetyDisclaimer` (a type).** The plan's pin row
  (Pins table, P-SAFE-03) says *"route screen has visible `SafetyDisclaimerDisplaying`"* and Brief item 1
  asks that *"every screen type under `Feature*/` that presents a route or a handoff conforms to it"*. The
  tree has ONE feature target and ONE screen (`ls Sources/` -> DesignSystem, MapAdapter, FeatureScenicHome;
  `ls Sources/FeatureScenicHome/` -> ScenicHomeScreen.swift, SkylineHandoff.swift). A protocol with one
  conformer, no second implementation and no generic call site is machinery, and a conformance list with one
  entry is a check that cannot discriminate. Acceptance line 1 names *"a SafetyDisclaimer acknowledgement
  type"*. RULED: a concrete `SafetyDisclaimer` in its own file now; the protocol is M4's, when a route screen
  exists to be the second conformer. The pin's statement says what is actually checked, so nothing in
  PINS.yaml claims a protocol that is not there.

  **R3 - "the route screen" does not exist.** CLAUDE.md's product invariant and the plan both put the
  persistent line on the route screen. There is no route screen (plan M4, `Route preview`). RULED: the line
  lands on the only screen there is, and the pin's statement says *home screen*. A pin that named the route
  screen would be green against a file that has no route in it.

  **R4 - assertion style.** The task brief for this session asks for the P-GIT-02 interpreter style
  (`"${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/x.py`). That form exists to choose a
  python interpreter; this check is bash, and the gate command named in the same brief is
  `bash ops/lib/check-safety-disclaimer`. RULED: `assertion: "bash ops/lib/check-safety-disclaimer"`, which
  is the form P-SRC-02 (`check-line-cap`) and P-OPS-05 (`check-sane-exit-order`) already use for bash checks.
  Executable bit set with `git update-index --chmod=+x` (P-OPS-01).

  **R5 - how the gate is detected structurally, and what the check CANNOT see.** Brief: *"anchor on the
  protocol name and the conformance list - identifiers, never a comment"*. With R2 there is no conformance
  list, so the anchor is the call graph, flattened into three lexical facts the check can actually decide:
  (a) `SkylineHandoff.open(` is called from exactly one file besides its own declaration, and that file is
  `GatedHandoffButton.swift`; (b) in that file the call is dominated by `guard isSafetyDisclaimerAcknowledged
  else` - the guard line precedes the call and the brace depth never returns below the guard's depth between
  them, so the call is still inside the block the guard protects; (c) `GatedHandoffButton(` is constructed in
  exactly one file, `ScenicHomeScreen.swift`, and the acknowledgement identifier is passed at that call.
  Stated plainly, the check CANNOT see: that the sheet ever renders, that the accept button ever writes the
  storage, that `@AppStorage` reads back what it wrote, that the line is on screen rather than behind the
  map, contrast, Dynamic Type, or the 44 pt target. Those are XCUITest and a device. It also strips `//` to
  end of line before counting braces, so a brace inside a string that follows `//` on the same line would be
  miscounted, and it does not parse `/* */`. Everything it does see is an identifier or a file name; nothing
  is anchored on a comment (CLAUDE.md).

  **R6 - `pending:` for the XCUITest half.** Brief item 1: *"the XCUITest half stays `pending:` on the first
  green Xcode Cloud run and is printed BY NAME by check-pins"*. `ops/lib/pins.py` gives a pin ONE assertion
  and `pending: T-XXXX` means *the assertion cannot exist yet*, so the pin is reported and does not run.
  P-SAFE-03's source assertion exists and runs today; marking it `pending:` would stop it running. There is
  no second-assertion slot to put the XCUITest in. RULED: one pin, `anchor: source`, a real assertion, and
  the XCUITest debt written into `why_no_test_catches_it` in the words the brief asks for - XCUITest is the
  real proof and does not exist yet. No `pending:` field.

  **R7 - where the persistent line goes.** The session brief says *"a DesignTokens.fgMuted footnote above the
  button, never over the AttributionFooter or the map's lower-right"*. `AttributionFooter.swift` documents
  why `fgMuted` over a basemap needs its own ground (*"readable on both appearances because it carries its
  own ground rather than trusting the tiles"*), and the bottom stack on this screen floats over
  `MapView`. RULED: the line is a sibling in that same bottom `VStack`, directly above the button and above
  the footer, and it carries the same `surface` chip + `border` hairline the footer carries, for the reason
  the footer states. It is never over the footer (the footer is the last element in the stack) and never in
  the lower-right corner (full width, above the button). `fgMuted` on `surface` is the pair `DesignTokens`
  was written for.

  **R8 - the drivers' round-3 caption ends with Apple Maps, and `Copy.route` stays.** Acceptance line 3 is
  verbatim and replaces `Copy.title` and `Copy.mapCaption` only. `Copy.route` (the road list) is untouched:
  T-0170 owns the copy action and the straight-line distance, and the 23:04 log entry says so. No duration
  anywhere, still (the type note in `ScenicHomeScreen.swift` says why). Identifiers `home.title`,
  `home.route`, `home.caption`, `home.error`, `home.openInAppleMaps` all keep their names.

- 2026-09-18T23:27:20Z RED FIRST, then green, by agent/claude-opus-5. `ops/lib/check-safety-disclaimer` was
  written BEFORE any Swift and run against the tree that had no disclaimer in it. Verbatim.

  Baseline, before anything was written (`bash ops/check-pins --source-only`, 2026-09-18T23:16 run):

      PINS ok=11 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only

  RED 1 - origin/main's own `Sources/FeatureScenicHome`, extracted with `git show origin/main:<path>` into
  `.redtmp/main-FeatureScenicHome` (two files, `ScenicHomeScreen.swift` and `SkylineHandoff.swift`):

      $ bash ops/lib/check-safety-disclaimer --sources .redtmp/main-FeatureScenicHome
      P-SAFE-03: missing file: .redtmp/main-FeatureScenicHome/SafetyDisclaimer.swift
        (i)/(iii) name these files; one type per file, filename == type name (CLAUDE.md).
        Population under .redtmp/main-FeatureScenicHome: 2 .swift file(s).
      exit=1

  RED 2 - the same check with no `--sources`, against the tracked tree, still before the Swift existed:

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: missing file: apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/SafetyDisclaimer.swift
        (i)/(iii) name these files; one type per file, filename == type name (CLAUDE.md).
        Population under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome: 2 .swift file(s).
      exit=1

  GREEN, after `SafetyDisclaimer.swift`, `GatedHandoffButton.swift` and the edits to `ScenicHomeScreen.swift`:

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1") on device;
        SkylineHandoff.open( called once (GatedHandoffButton.swift line 51), dominated by the
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
        passed through. Not checked here: rendering, taps, contrast, Dynamic Type, 44 pt - XCUITest owns those.
      exit=0

  SIX MUTATIONS, each refused BY NAME (`--prove-red` copies the feature sources, seds one structural fact and
  re-runs the check against the copy; a mutation that exits 0, or exits 1 without naming the expected reason,
  fails the table). The first run of this table also found a defect in the check itself - `work` was `local`,
  so the EXIT trap read an unbound variable under `set -u` and the temp tree was never removed
  (`ops/lib/check-safety-disclaimer: line 1: work: unbound variable`, printed after the table). Fixed, and the
  table re-run:

      $ bash ops/lib/check-safety-disclaimer --prove-red
      MUTATION                                             EXIT     REASON NAMED
      the SafetyDisclaimer type renamed                    1        yes
      the home.disclaimer identifier removed               1        yes
      the acknowledgement guard removed                    1        yes
      the persistent conditions line removed               1        yes
      the acknowledgement no longer passed to the button   1        yes
      the on-device store key changed                      1        yes
      prove-red: 6/6 mutations refused by name
      exit=0

  The drivers' strings, byte-exact (`grep | od -c`, so the middle dot and the hyphens are bytes, not glyphs):
  `title` carries `302 267` between "loop" and "starts" (U+00B7 MIDDLE DOT in UTF-8), and the caption carries
  an ASCII apostrophe (`'`) in "doesn't" and an ASCII hyphen (`-`) in "yet - tap". `grep -c -F 'Conditions
  change. Verify locally.' ScenicHomeScreen.swift` -> 1. The only occurrences of "duration" in the file are
  the two doc comments that say there is none.

  Sizes, measured (`awk 'END{print NR}'`): GatedHandoffButton.swift 86, SafetyDisclaimer.swift 110,
  ScenicHomeScreen.swift 217, SkylineHandoff.swift 78, ops/lib/check-safety-disclaimer 307. The cap is a
  Swift and Python rule (CLAUDE.md, and `ops/lib/check-line-cap` scans `*.swift` only); the 307-line bash
  check is over 300 and is stated here rather than left for a reviewer to find - `ops/lib/check-sweep.py` and
  `check-touches-merge.py` are larger still and no gate in this repository caps a script.
