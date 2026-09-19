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

- 2026-09-18T23:37:08Z ACCEPTANCE BLOCK, re-run whole at the final pre-review commit, by
  agent/claude-opus-5. Code head `d975dfb`. The only file edited after these runs is this task file's own
  Log; `bash ops/queue-check` was re-run after the record commit and is quoted again at the bottom.

  **(1) P-SAFE-03 in pins/PINS.yaml, an assertion that runs on Linux today, seen RED by name first, then
  green; the run ids quoted.** The pin is `anchor: source`, `runs_on: [linux, mac]`,
  `assertion: "bash ops/lib/check-safety-disclaimer"`. Red-by-name is the 23:27 entry above, verbatim: RED 1
  against `origin/main`'s own `Sources/FeatureScenicHome` and RED 2 against the tracked tree, both refusing
  with `missing file: .../SafetyDisclaimer.swift` at exit 1, before any Swift was written. Green:

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1") on device;
        SkylineHandoff.open( called once (GatedHandoffButton.swift line 51), dominated by the
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
        passed through. Not checked here: rendering, taps, contrast, Dynamic Type, 44 pt - XCUITest owns those.
      exit=0

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

  The pin is carried by the runner, not just by this file - `ops/check-pins --source-only` went from
  `ok=11` before the pin to `ok=12` after it, with nothing else changed:

      before: PINS ok=11 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      after:  PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only

  **(2) The gate, the persistent line, the tokens, and a green ios-compile run id.** The first tap calls
  `onBlocked()` and presents `SafetyDisclaimer` (`home.disclaimer`); accepting writes
  `@AppStorage("safety.disclaimer.acknowledged.v1")` - on the device, no account, no server - and dismisses;
  the handoff is reached only through `guard isSafetyDisclaimerAcknowledged else` in
  `GatedHandoffButton.swift` (line 46, the call at line 51, both measured by the check above). The accept
  button is `home.disclaimer.accept` and the sheet is `interactiveDismissDisabled()`, so it cannot be swiped
  past. `Copy.conditions` is on the home screen unconditionally - not inside any `if` - directly above the
  button and above `AttributionFooter`, which is last in the stack and keeps the lower-right corner. Colour
  is `DesignTokens` only (`fgMuted`, `surface`, `border`, `primary`, `onPrimary`, `fg`, `bg`, `destructive`);
  there are no point sizes anywhere in the three files, only text styles, and every new tappable frame is
  `minHeight: 44`. ios-compile, dispatched on this branch:

      $ gh workflow run ios-compile.yml --ref task/T-0153
      $ gh run view 35405951245 --json databaseId,status,conclusion,headSha,createdAt,updatedAt
      {"conclusion":"success","createdAt":"2026-09-18T23:30:19Z","databaseId":35405951245,
       "headSha":"d975dfb2e59d514c8b57d1b379867b555cad3ec3","status":"completed",
       "updatedAt":"2026-09-18T23:31:39Z"}
      $ grep -n -F '** BUILD' <run log>
      2156:simulator-build	build for the iOS Simulator	2026-09-18T23:31:32.5423000Z ** BUILD SUCCEEDED **
      $ grep -n -F ' error:' <run log>     -> no lines

  One dispatch, one run, first try. `d975dfb` is the code head: the record commit that follows touches only
  this file, which the iOS build does not read.

  **(3) The drivers' round-3 strings, verbatim.** From `ScenicHomeScreen.swift` lines 198 and 211, read back
  through `od -c` so the claim is about bytes:

      static let title = "Skyline loop · starts and ends in San Francisco"
          ...  S k y l i n e   l o o p  302 267   s t a r t s   a n d   e n d s   i n   S a n   F r a n c i s c o

      "Preview build: one fixed Bay Area drive. The map doesn't show roads yet - tap below and it opens in Apple Maps."
          ...  d o e s n ' t  ...  y e t   -   t a p  ...

  `302 267` is U+00B7 MIDDLE DOT in UTF-8; the apostrophe and the hyphen are ASCII `'` and `-`. `Copy.route`
  is untouched (T-0170 owns the copy action and the straight-line distance). No duration anywhere: the only
  matches for `-iE 'minute|hour|duration'` in the file are the two doc comments saying there is none.

  **(4) The gates, bare.**

      $ bash ops/lib/check-line-cap
      P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none over 300 lines
      exit=0

      $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

      $ bash ops/check-pins --source-only
      PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  **STILL OPEN.** Plainly, because none of it is in this PR.
  1. NOTHING HERE HAS BEEN RENDERED. There is no Apple toolchain on this box and no simulator; the ios-compile
     run proves the three files COMPILE for the iOS Simulator and nothing more. Nobody has seen the sheet, the
     conditions chip, or either of them on a dark appearance.
  2. THE ACKNOWLEDGEMENT HAS NEVER BEEN TAPPED. That `@AppStorage` writes on accept, that the sheet dismisses,
     that the second tap then leaves for Apple Maps, and that the flag survives a relaunch are all unobserved.
     `check-safety-disclaimer` says so in its own output and in the pin's `why_no_test_catches_it`.
  3. NO XCUITEST EXISTS. `apps/ios/Packages/ScenicApp/Package.swift` has no test target, on purpose; the tests
     arrive with the first green Xcode Cloud run. `home.disclaimer`, `home.disclaimer.accept` and
     `home.conditions` are reserved for it and are not asserted by any runtime test today. P-SAFE-03 is
     therefore HALF the pin the plan describes: the source half runs, the XCUITest half is not filed as a
     `pending:` field (ruling R6) and is owed by whoever lands the first XCUITest bundle.
  4. `SafetyDisclaimerDisplaying`, the plan's protocol, is not in the tree (ruling R2). It wants a second
     screen to be worth anything, and M4's route preview is the first one.
  5. The 44 pt targets, the Dynamic Type behaviour and the contrast of `fgMuted` on the `surface` chip over a
     basemap are arguments from `DesignTokens` and the plan's UI section, not measurements. Nothing on this
     box can measure them.
  6. `ops/lib/check-safety-disclaimer` is 307 lines. No gate caps a bash script; it is over the number
     CLAUDE.md names for Swift and Python and that is recorded rather than hidden.
- 2026-09-19T01:12:38Z THE SEVENTH BLIND SPOT, closed by agent/claude-opus-5 before the review was bought, on the
  hourly panel's grounded synthesis. `ops/lib/check-safety-disclaimer` could not see the BLOCKED path: every
  anchor stopped at the guard. `GatedHandoffButton.swift`'s guard calls `onBlocked()`, wired on the screen as
  `onBlocked: { isShowingDisclaimer = true }` with `.sheet(isPresented: $isShowingDisclaimer)`; replacing that
  closure with `{ }` left all six mutations green while the first tap did NOTHING and the disclaimer never
  appeared. A gate that refuses the handoff and offers no way through it is a liveness hole in a safety pin.
  Three new anchors, all identifiers or fixed strings over //-stripped code: `onBlocked()` between the guard
  and its `return` in `GatedHandoffButton.swift` (the awk that decides dominance now also decides the guard
  body is not silent), and `onBlocked: { isShowingDisclaimer = true }` + `isPresented: $isShowingDisclaimer`
  on `ScenicHomeScreen.swift`. No Swift was touched, so ios-compile run 35405951245 on `d975dfb` stands.

  RED FIRST, each refusal named, against copies of the feature sources with one mutation applied (the tracked
  tree was untouched; `.redtmp/` removed afterwards):

      $ sed -i -e 's/onBlocked: { isShowingDisclaimer = true }/onBlocked: { }/' .redtmp/blocked-dead/ScenicHomeScreen.swift
      $ bash ops/lib/check-safety-disclaimer --sources .redtmp/blocked-dead
      P-SAFE-03: the blocked tap is not wired to the sheet in .redtmp/blocked-dead/ScenicHomeScreen.swift: `onBlocked: { isShowingDisclaimer = true }` absent.
        GatedHandoffButton's guard calls onBlocked() on a refused tap; the screen must turn that into a
        presentation (`onBlocked: { isShowingDisclaimer = true }`) and bind a sheet to the same flag
        (`.sheet(isPresented: $isShowingDisclaimer)`). With either gone the first tap is silent.
      exit=1

      $ sed -i -e 's/\.sheet(isPresented: \$isShowingDisclaimer)/.sheet(isPresented: .constant(false))/' .redtmp/sheet-unbound/ScenicHomeScreen.swift
      $ bash ops/lib/check-safety-disclaimer --sources .redtmp/sheet-unbound
      P-SAFE-03: the blocked tap is not wired to the sheet in .redtmp/sheet-unbound/ScenicHomeScreen.swift: `isPresented: $isShowingDisclaimer` absent.
      exit=1

      $ sed -i -e 's/^                onBlocked()$//' .redtmp/guard-silent/GatedHandoffButton.swift
      $ bash ops/lib/check-safety-disclaimer --sources .redtmp/guard-silent
      P-SAFE-03: no `onBlocked()` between the guard at line 46 and its return at line 48 in .redtmp/guard-silent/GatedHandoffButton.swift.
        The refused tap has to hand the screen something to present, or the user taps a dead button forever.
      exit=1

  The mutation table moved to `ops/lib/check-safety-disclaimer-mutations` (new file, committed 100755 with
  `git update-index --chmod=+x`, P-OPS-01): one file, one concern, and the check comes DOWN to 299 lines from
  the 307 recorded at 23:27, rather than past 330. `--prove-red` now runs that file and row 7 is
  `the blocked tap no longer presents the disclaimer`. `pins/PINS.yaml` P-SAFE-03's `why_no_test_catches_it`
  names the new anchors and says `--prove-red refuses seven mutations by name`; the check's header lists the
  seventh blind spot as closed and states what it STILL cannot see (rendering, a tap reaching the button, that
  the sheet's accept writes the @AppStorage flag - the anchors prove the blocked path is WIRED, never that it
  RUNS).

- 2026-09-19T01:12:38Z ACCEPTANCE BLOCK, the lines this change touches, re-run at the final commit by
  agent/claude-opus-5. Code head `e5726d8`. Lines (2) and (3) are unchanged and their 23:37 runs stand -
  no Swift file was edited, so the quoted ios-compile run 35405951245 on `d975dfb` still describes this tree.

  **(1) P-SAFE-03's assertion, green, and the mutation table.**

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1") on device;
        SkylineHandoff.open( called once (GatedHandoffButton.swift line 51), dominated by the
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
        passed through; the blocked tap is wired - onBlocked() at line 47 before the return at
        line 48, `onBlocked: { isShowingDisclaimer = true }` and a sheet bound to that flag on the
        screen. Not checked here: rendering, taps, that accepting the sheet writes the flag, contrast,
        Dynamic Type, 44 pt - XCUITest owns those.
      exit=0

      $ bash ops/lib/check-safety-disclaimer --prove-red
      MUTATION                                             EXIT     REASON NAMED
      the SafetyDisclaimer type renamed                    1        yes
      the home.disclaimer identifier removed               1        yes
      the acknowledgement guard removed                    1        yes
      the persistent conditions line removed               1        yes
      the acknowledgement no longer passed to the button   1        yes
      the on-device store key changed                      1        yes
      the blocked tap no longer presents the disclaimer    1        yes
      prove-red: 7/7 mutations refused by name
      exit=0

  **(4) The gates, bare.**

      $ bash ops/lib/check-line-cap
      P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none over 300 lines
      exit=0

      $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

      $ bash ops/check-pins --source-only
      PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  Sizes, re-measured (`wc -l`, the T-0162 lesson - a correction commit re-measures what it changed):
  `ops/lib/check-safety-disclaimer` 299, `ops/lib/check-safety-disclaimer-mutations` 73. The four Swift files
  are byte-identical to `d975dfb`.

  STILL OPEN, unchanged and now with one item retired: items 1-5 of the 23:37 block stand (nothing rendered,
  the acknowledgement never tapped, no XCUITest, no `SafetyDisclaimerDisplaying`, the 44 pt / Dynamic Type /
  contrast arguments unmeasured). Item 6 (the check over 300 lines) is closed: 299 and 73 in two files. New:
  the three anchors added here prove the blocked path is WIRED and nothing more - that a tap presents the
  sheet, and that accepting it writes the flag, remain XCUITest's, and `ops/lib/check-safety-disclaimer-mutations`
  has itself never been seen to pass a mutation it should have refused, only the seven rows it carries.

- 2026-09-19T02:59:10Z REVIEW FAIL by agent/rv1-pr101 (not the owner, not the fixer). PR #101, head 4c0f7fc,
  base main. Every acceptance number re-run in a detached worktree at 4c0f7fc and every one of them
  reproduces: `bash ops/lib/check-safety-disclaimer` exit 0 with the 01:12 paragraph verbatim; `--prove-red`
  7/7 refused by name, exit 0; `bash ops/lib/check-line-cap` "P-SRC-02: 73 Swift files tracked (Sources=26,
  Tests=37, apps/ios=10), none over 300 lines" exit 0; `bash ops/queue-check` "QUEUE OK (169 tasks)" exit 0;
  `bash ops/check-pins --source-only` "PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux
  source-only" exit 0; `wc -l` 299 and 73, both 100755; ios-compile 35405951245 conclusion success on
  headSha d975dfb, log line 2156 `** BUILD SUCCEEDED **`, `grep -c -F ' error:'` 0; the title's middle dot is
  `302 267` under `od -c`. `git diff --name-only d975dfb 4c0f7fc -- 'apps/ios/**/*.swift'` is empty, so that
  run does describe this tree. Rulings R1-R4 and R6-R8 upheld; R6 verified against `ops/lib/pins.py`
  (pending is handled at lines 126-138, the assertion only runs at 141-147, so `pending:` would indeed have
  silenced it).

  THE PRODUCT QUESTION, answered against the tree: a build CAN ship with the handoff reachable un-acknowledged
  and P-SAFE-03 green. Three mutants of the reviewer's own, on copies and on one untracked file in the
  reviewer's worktree, all restored, `git status --short` empty after each:

  B1 - the @AppStorage DEFAULT is not anchored. The check greps `@AppStorage("safety.disclaimer.acknowledged.v1")`
  (lines 175-178) and nothing about the initial value on the next line.

      $ sed -i -e 's/private var isSafetyDisclaimerAcknowledged = false/private var isSafetyDisclaimerAcknowledged = true/' <copy>/ScenicHomeScreen.swift
      $ bash ops/lib/check-safety-disclaimer --sources <copy>
      P-SAFE-03: 4 Swift file(s) ... @AppStorage("safety.disclaimer.acknowledged.v1") on device; ...
      exit=0

  On a fresh install nothing is stored, @AppStorage yields the declared default, the guard passes and the
  FIRST tap opens Apple Maps having shown nobody the sheet. That is the pin's statement ("unreachable without
  a SafetyDisclaimer acknowledgement stored on the device") false with the assertion green, and it is not what
  "whether accepting writes the store" discloses - that disclosure is about a runtime round-trip, this is a
  literal three tokens from an anchor the check already reads.

  B2 - the call-site anchor scans one directory at `-maxdepth 1` (line 108) while `public enum SkylineHandoff`
  is exported from the `FeatureScenicHome` library product. Against the TRACKED tree, with
  `apps/ios/ScenicDrive/DriveNowButton.swift` added (one `try? SkylineHandoff.open()`, in the shell target
  that already imports the product):

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: ... SkylineHandoff.open( called once (GatedHandoffButton.swift line 51) ...
      exit=0

  It had just scanned 4 of the 10 tracked Swift files under apps/ios and printed a sentence that was false of
  the tree. Same hole one level down: `Package.swift` declares `path: "Sources/FeatureScenicHome"` with no
  `sources:` list, so `Sources/FeatureScenicHome/Debug/QuickDriveButton.swift` compiles and is invisible.

  B3 - `GatedHandoffButton(` is counted per FILE, not per construction (lines 233-243; `built+=("$f")` ignores
  the count) and the pass-through anchor is `-ge 1`. Adding a second button beside the real one:

      $ grep -c 'GatedHandoffButton(' <copy>/ScenicHomeScreen.swift
      2
      $ bash ops/lib/check-safety-disclaimer --sources <copy>
      P-SAFE-03: ... the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged passed through; ...
      exit=0

  where the second is `GatedHandoffButton(isSafetyDisclaimerAcknowledged: true, onBlocked: { }, onFailure: ...)`.
  Row 5 of the table catches REPLACING the pass-through; it does not catch ADDING one.

  Correctly refused, for the record: the guard inverted (`guard !ack`) reads as absent and is named by row 3;
  a second call site in a SIBLING top-level file is named; a second button in ANOTHER file is named; the
  conditions line removed is named. The key read but never written is not caught and does not need to be - it
  fails closed.

  The Swift in this PR is correct and the tree as committed is gated; B1-B3 are holes in the guard, not bugs
  in the app. But acceptance line 1's deliverable is the assertion and the pin's statement is absolute, and
  this is the same class as the seventh blind spot the owner closed himself at 01:12 - except these three fail
  OPEN. Each is a few lines plus a mutation row: anchor `= false` on the declaration; enumerate the call site
  over `git ls-files 'apps/ios/**/*.swift'` rather than one directory at maxdepth 1; require the count of
  `GatedHandoffButton(` to equal the count of `isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged`.
  Recorded and not blocking: the accept closure is unanchored but fails closed (T-0180's); `runs_on: [linux,
  mac]` buys nothing today; `/* */` is unparsed (self-disclosed); the 01:12 block re-ran lines (1) and (4) and
  argued (2)/(3) stand, which the reviewer verified independently; and the mutations file's own
  "UNREFUSED or UNNAMED" branch has never been seen to fire.

- 2026-09-19T03:35:00Z FIX by agent/claude-opus-5 (the owner; agent/rv1-pr101 found and did not fix) for the
  three blocking findings above. All three were in `ops/lib/check-safety-disclaimer`, all three failed OPEN,
  and each one is the pin's own statement - "the handoff on the home screen is unreachable without a
  SafetyDisclaimer acknowledgement stored on the device" - false with its own assertion at exit 0. No Swift
  was touched in this pass.

  REPRODUCED FIRST, on copies under `.artifacts/red/` (gitignored), the tracked tree untouched and the
  copies removed afterwards. Three greens that should have been red:

      $ cp -R apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome .artifacts/red/b1
      $ sed -i -e 's/private var isSafetyDisclaimerAcknowledged = false/private var isSafetyDisclaimerAcknowledged = true/' .artifacts/red/b1/ScenicHomeScreen.swift
      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b1
      P-SAFE-03: 4 Swift file(s) under .artifacts/red/b1; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1") on device;
      exit=0

      $ cp -R apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome .artifacts/red/b2sub && mkdir -p .artifacts/red/b2sub/Debug
      $ cp .artifacts/redsrc/QuickDriveButton.swift .artifacts/red/b2sub/Debug/QuickDriveButton.swift   # one `try? SkylineHandoff.open()`
      $ grep -c -F 'SkylineHandoff.open(' .artifacts/red/b2sub/Debug/QuickDriveButton.swift
      1
      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b2sub
        SkylineHandoff.open( called once (GatedHandoffButton.swift line 51), dominated by the
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
      exit=0

      $ cp -R apps/ios .artifacts/red/b2tree
      $ sed -i -e 's/ScenicHomeScreen()/ScenicHomeScreen().onAppear { try? SkylineHandoff.open() }/' .artifacts/red/b2tree/ScenicDrive/ScenicDriveApp.swift
      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b2tree/Packages/ScenicApp/Sources/FeatureScenicHome
        SkylineHandoff.open( called once (GatedHandoffButton.swift line 51), dominated by the
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
      exit=0

      $ cp -R apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome .artifacts/red/b3
      $ sed -i -e 's|^                    conditions$|                    conditions\n                    GatedHandoffButton(isSafetyDisclaimerAcknowledged: true, onBlocked: { }, onFailure: { _ in })|' .artifacts/red/b3/ScenicHomeScreen.swift
      $ grep -c -F 'GatedHandoffButton(' .artifacts/red/b3/ScenicHomeScreen.swift
      2
      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b3
        guard at line 46; the button is built once, in ScenicHomeScreen.swift, with isSafetyDisclaimerAcknowledged
        passed through; the blocked tap is wired - onBlocked() at line 47 before the return at
      exit=0

  WHAT CHANGED. Three anchors, all fixed strings or identifiers over //-stripped code, none on a comment:

  (B1) the @AppStorage DEFAULT. `ack_default_verdict` finds the `@AppStorage("safety.disclaimer.acknowledged.v1")`
  line and requires the FIRST line carrying any code after it to read exactly
  `private var isSafetyDisclaimerAcknowledged = false`. @AppStorage yields its declared default whenever
  nothing is stored, which is every fresh install, so `= true` was an acknowledgement nobody gave.

  (B2) the population. The call graph is now decided over EVERY `*.swift` under `apps/ios`, recursively -
  the Packages sources, `apps/ios/ScenicDrive/`, and anything else that appears there - instead of one
  directory at `-maxdepth 1`. The tracked run scans 10 files where it used to scan 4. A copy is scanned as
  its own app tree unless `--app-tree DIR` names one, which is how the table hands the check a copy of the
  whole of `apps/ios` (row 9).

  (B3) occurrences, not files. `occurrences_by_file` returns `path(count)`, and `SkylineHandoff.open(` must
  be one occurrence in one file (`GatedHandoffButton.swift`) and `GatedHandoffButton(` one occurrence in one
  file (`ScenicHomeScreen.swift`). `button_args` then reads that one construction's argument list across its
  four lines and requires `isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged` in it and no
  `: true` anywhere in it.

  The readers moved to `ops/lib/check-safety-disclaimer-lib` (new file, committed 100755 with
  `git update-index --chmod=+x`, P-OPS-01) so the check stays under the 300-line cap: one concern each -
  the lib is HOW a fact is read out of Swift source, the check is WHICH facts P-SAFE-03 asserts, the
  mutations file is the table that proves the refusals. `wc -l`: `ops/lib/check-safety-disclaimer` 293
  (from 299), `ops/lib/check-safety-disclaimer-lib` 189, `ops/lib/check-safety-disclaimer-mutations` 83
  (from 73). The header's blind-spot list now also states that Swift OUTSIDE `apps/ios` is not scanned and
  that a second `GatedHandoffButton(` inside `GatedHandoffButton.swift` itself is not counted (a #Preview
  belongs there). `pins/PINS.yaml` P-SAFE-03's `why_no_test_catches_it` names the three new anchors and says
  ten rows.

  RED, BY NAME. The table is three rows longer and each new row was seen red by the refusal it is named for
  (full runs quoted in the acceptance block below; these are the refusal texts):

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b1                                   # row 8's shape
      P-SAFE-03: the acknowledgement does not default to false in .artifacts/red/b1/ScenicHomeScreen.swift (@AppStorage line 40).
        The line after the key must read exactly `private var isSafetyDisclaimerAcknowledged = false`. @AppStorage yields its DECLARED DEFAULT when
        nothing is stored, which is every fresh install - so `= true` ships a first tap that leaves for
        Apple Maps having shown nobody the disclaimer, with this check green (PR #101, finding B1).
      exit=1

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b2tree/Packages/ScenicApp/Sources/FeatureScenicHome --app-tree .artifacts/red/b2tree   # row 9's shape
      P-SAFE-03: SkylineHandoff.open( must be called exactly once, from .artifacts/red/b2tree/Packages/ScenicApp/Sources/FeatureScenicHome/GatedHandoffButton.swift; found: .artifacts/red/b2tree/Packages/ScenicApp/Sources/FeatureScenicHome/GatedHandoffButton.swift(1) .artifacts/red/b2tree/ScenicDrive/ScenicDriveApp.swift(1)
        Counted over all 10 .swift file(s) under .artifacts/red/b2tree. A second call site is a second door, and only
        one of them is behind the disclaimer - including one a directory down or in the app shell, which
        imports this feature's product (PR #101, finding B2).
      exit=1

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b2sub                                # the same hole one directory down
      P-SAFE-03: SkylineHandoff.open( must be called exactly once, from .artifacts/red/b2sub/GatedHandoffButton.swift; found: .artifacts/red/b2sub/Debug/QuickDriveButton.swift(1) .artifacts/red/b2sub/GatedHandoffButton.swift(1)
        Counted over all 5 .swift file(s) under .artifacts/red/b2sub. A second call site is a second door, and only
      exit=1

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red/b3                                   # row 10's shape
      P-SAFE-03: GatedHandoffButton( must be constructed exactly once, in .artifacts/red/b3/ScenicHomeScreen.swift; found: .artifacts/red/b3/ScenicHomeScreen.swift(2)
        Counted by occurrence over all 4 .swift file(s) under .artifacts/red/b3. Every other way onto the map's
        one button would bypass the guard inside it.
      exit=1

  FOUND WHILE FIXING, AND FIXED: `--prove-red`'s own guard against running the table over an already-red
  tree was SILENT. `run_check ... >/dev/null || { echo ...; }` called `fail`, and `fail` exits, so the
  script ended with status 1 and the reason swallowed by the redirect - the `||` branch never ran. Seen red
  and then green on a copy with `SafetyDisclaimer.swift` deleted (the probe now runs in a subshell):

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red2/already-red --prove-red   # before
      exit=1

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/red2/already-red --prove-red   # after
      P-SAFE-03: --prove-red refuses to run against a tree that is already red.
      P-SAFE-03: missing file: .artifacts/red2/already-red/SafetyDisclaimer.swift
        (i)/(iv) name these files; one type per file, filename == type name (CLAUDE.md).
        Population under .artifacts/red2/already-red: 3 .swift file(s).
      exit=1

  It is pre-existing - the reviewed head at `4c0f7fc` has it - and it fails closed (a red tree still exits
  non-zero), so it was never a wrong verdict, only an unreadable one. It is in this commit because it is
  three tokens in the file being fixed and because a guard nobody can see fire is the thing this task is
  about. The acceptance block below was re-run after it.

  The reviewer's R5 is NOT closed and is not claimed to be: the table's own "UNREFUSED or UNNAMED" branch
  still has not been seen to fire. The three reproductions above were run against copies with the check
  invoked directly, not through the table, so nothing here exercised that branch. It stays in STILL OPEN.

- 2026-09-19T03:45:49Z ACCEPTANCE BLOCK, all four lines, re-run at the final commit by agent/claude-opus-5.
  The reviewer's R4 asked for the WHOLE block rather than an argument that two lines stand; this is that.

  **(1) P-SAFE-03's assertion, green, and the mutation table.**

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1")
        at line 40 with `private var isSafetyDisclaimerAcknowledged = false` under it;
        over the 10 .swift file(s) under apps/ios, SkylineHandoff.open( called once
        (GatedHandoffButton.swift line 51), dominated by the guard at line 46;
        GatedHandoffButton( constructed once, in ScenicHomeScreen.swift, passing isSafetyDisclaimerAcknowledged
        through with no `: true` in its argument list; the blocked tap is wired - onBlocked() at line
        47 before the return at line 48, `onBlocked: { isShowingDisclaimer = true }`
        and a sheet bound to that flag on the screen. Not checked here: rendering, taps, that accepting
        the sheet writes the flag, contrast, Dynamic Type, 44 pt - XCUITest owns those.
      exit=0

      $ bash ops/lib/check-safety-disclaimer --prove-red
      MUTATION                                             EXIT     REASON NAMED
      the SafetyDisclaimer type renamed                    1        yes
      the home.disclaimer identifier removed               1        yes
      the acknowledgement guard removed                    1        yes
      the persistent conditions line removed               1        yes
      the acknowledgement no longer passed to the button   1        yes
      the on-device store key changed                      1        yes
      the blocked tap no longer presents the disclaimer    1        yes
      the acknowledgement defaults to true                 1        yes
      a second call site in the app shell                  1        yes
      a second button beside the real one                  1        yes
      prove-red: 10/10 mutations refused by name
      exit=0

  **(2) The gate itself, and the compile.** No Swift file was edited in this pass and none was edited in the
  one before it: `git diff --name-only d975dfb -- apps/ios` is EMPTY at this commit, so ios-compile run
  35405951245 (conclusion success, headSha `d975dfb`, log line 2156 `** BUILD SUCCEEDED **`, `grep -c -F
  ' error:'` 0, quoted at 23:37 and re-verified by the reviewer at 02:59) describes this tree's Swift
  exactly. The identifiers `home.disclaimer` / `home.disclaimer.accept` / `home.conditions`, the
  on-device-only `@AppStorage` key and the 44 pt minimum height are the same four files. `gh pr checks 101`
  is quoted in the PR body.

  **(3) The 16:13 panel drivers' round-3 strings, verbatim.**

      $ grep -c -F 'Skyline loop · starts and ends in San Francisco' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      1
      $ grep -c -F "Preview build: one fixed Bay Area drive. The map doesn't show roads yet - tap below and it opens in Apple Maps." apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      1

  **(4) The gates, bare.**

      $ bash ops/lib/check-line-cap
      P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none over 300 lines
      exit=0

      $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

      $ bash ops/check-pins --source-only
      PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  Sizes, re-measured at this commit (`wc -l`, the T-0162 lesson): `ops/lib/check-safety-disclaimer` 293,
  `ops/lib/check-safety-disclaimer-lib` 189, `ops/lib/check-safety-disclaimer-mutations` 83. Modes:
  100755, 100755, 100755 (`git ls-files -s`).

  STILL OPEN. Items 1-5 of the 23:37 block stand, unchanged: nothing on this screen has been rendered, the
  acknowledgement has never been tapped, there is no XCUITest, there is no `SafetyDisclaimerDisplaying`
  protocol, and the 44 pt / Dynamic Type / contrast arguments are unmeasured. Carried from the review as
  recordable and NOT fixed here: R1, the accept closure that writes the @AppStorage flag
  (`ScenicHomeScreen.swift` lines 99-102) is still unanchored - disclosed by the pin, and it fails CLOSED
  (a user who is never recorded is trapped behind the sheet, nobody drives ungated); it is T-0180's
  XCUITest, not this PR's. R2, `runs_on: [linux, mac]` buys nothing today, since the assertion is a bash
  source check that behaves identically in both tiers - left as the plan writes it, noted so nobody reads a
  mac run as covering the XCUITest half. R3, `/* */` is still unparsed and a `/*`-commented-out guard would
  still be counted; not reachable today, and the check's header says so. R5, the table's own
  "UNREFUSED or UNNAMED" branch, has still never been seen to fire - the three new rows are red by name,
  which is the branch NOT firing. New with this pass: the table now
  copies the whole of `apps/ios` ten times and takes ~6 minutes on the Windows box (up from ~1), which is
  T-0184's problem when it puts every `--prove-red` table in CI; and the check still cannot see a second
  construction of `GatedHandoffButton(` inside `GatedHandoffButton.swift` itself, which is where a #Preview
  would legitimately put one - stated in the header rather than closed, because closing it would refuse the
  preview this feature will want.

- 2026-09-19T04:28:48Z REVIEW FAIL (round 2) by agent/rv2-pr101 (not the owner, not rv1-pr101, not the
  fixer). PR #101, head a9c109f, base main. Reviewed in a detached worktree at a9c109f, removed after.

  THE THREE ROUND-1 HOLES ARE CLOSED. Re-applied on copies of apps/ios, each refused BY NAME, exit 1:
  B1 (`= false` -> `= true`) "the acknowledgement does not default to false ... (@AppStorage line 40)";
  B2 both ways - a new `Extras/BypassButton.swift` one directory DOWN inside the feature target, and a new
  `ScenicDrive/Extra/ShellBypass.swift` in a SUBdirectory of the shell, neither of which row 9 covers -
  "SkylineHandoff.open( must be called exactly once ... Counted over all 11 .swift file(s)"; B3 (a second
  `GatedHandoffButton(isSafetyDisclaimerAcknowledged: true, ...)` in the SAME file) "GatedHandoffButton(
  must be constructed exactly once ... found: .../ScenicHomeScreen.swift(2)".

  EVERY ACCEPTANCE NUMBER REPRODUCES at a9c109f: the bare check exit 0 with the 03:45 paragraph verbatim;
  `--prove-red` 10/10 refused by name, exit 0; `wc -l` 293 / 189 / 83 and `git ls-files -s` 100755 / 100755
  / 100755; `bash ops/lib/check-line-cap` "P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37,
  apps/ios=10), none over 300 lines"; `bash ops/queue-check` "QUEUE OK (169 tasks)"; `bash ops/check-pins
  --source-only` "PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only"; all exit 0.
  `git diff --name-only d975dfb a9c109f -- 'apps/ios/**/*.swift'` empty and run 35405951245 headSha
  d975dfb conclusion success, so that ios-compile still describes this tree. `gh pr checks 101`: core pass,
  pins-source-only pass. The diff is ops/lib (three files) + pins/PINS.yaml + this file only, no Swift, and
  this file's diff is append-only (280 added, 0 removed). The three-file split is sound: the lib is SOURCED
  after an explicit missing-file refusal, never executed, and 100755 is right for bash under ops/
  (P-OPS-01). R5 correctly still open, not claimed.

  BLOCKING, B4 - every WRITE to the acknowledgement is unanchored, and the open direction is not in the
  ten rows. B1 anchored the DECLARED default; nothing anchors who may SET the flag.
  `grep -rn -F 'isSafetyDisclaimerAcknowledged = true' apps/ios/` is one line today, ScenicHomeScreen.swift
  :100, inside `SafetyDisclaimer(onAccept:`. The check never counts that string and never reads where it
  sits, so a second write on the same screen opens the gate with P-SAFE-03 green:

      $ sed -i -e 's/^        .background(DesignTokens.bg)$/        .background(DesignTokens.bg)\n        .onAppear { isSafetyDisclaimerAcknowledged = true }/' <copy>/ScenicHomeScreen.swift
      $ bash ops/lib/check-safety-disclaimer --sources <copy>/<FS> --app-tree <copy>
      P-SAFE-03: 4 Swift file(s) ... @AppStorage("safety.disclaimer.acknowledged.v1") at line 40 with
        `private var isSafetyDisclaimerAcknowledged = false` under it; ... SkylineHandoff.open( called
        once (GatedHandoffButton.swift line 51), dominated by the guard at line 46;
      exit=0

  @AppStorage sets nonmutating, so that line compiles and writes true to UserDefaults the moment the only
  screen appears; the button is then constructed with true from the real pass-through, the guard passes and
  the FIRST tap leaves for Apple Maps with the sheet never presented, on every launch. That is this pin's
  statement false with its own assertion green - the same defect B1 was, in the pin's own words "an
  acknowledgement nobody gave", reached by an assignment instead of a default. The 03:45 entry says this
  region "fails CLOSED"; it fails closed in one direction (RV2-M3: delete line 100, exit 0, nobody is ever
  recorded) and OPEN in this one, and only the closed half is disclosed anywhere. Closing it needs no new
  machinery: `occurrences_by_file "isSafetyDisclaimerAcknowledged = true"` over the app tree must be exactly
  `ScenicHomeScreen.swift(1)` and a depth walk must place that line inside the `onAccept` block - both
  readers are already in ops/lib/check-safety-disclaimer-lib, green on HEAD, red on the mutant. Wanted: an
  eleventh row, the anchor in (iii), the PINS.yaml sentence, and the STILL OPEN R1 wording corrected.

  RECORDABLE, not asked for here. (a) The recursive population has no test carve-out: a legitimate
  apps/ios/ScenicDriveUITests/HandoffUITests.swift naming `SkylineHandoff.open(` is refused by name. It
  fails CLOSED, an XCUITest proper would drive XCUIApplication instead, but T-0180's half and the unit-test
  target ScenicApp/Package.swift promises would trip it - carve `*Tests/` out there, or name the exclusion
  in the pin. (b) `ack_default_verdict` refuses the equally legal one-line spelling `@AppStorage("...")
  private var isSafetyDisclaimerAcknowledged = false`; fails closed and the refusal names the expected
  line. (c) RV2-M2, the guard block's `return` deleted, is REFUSED ("A guard body that falls through is not
  a gate") - the guard half holds. state stays `claimed`; nothing in the tree was changed by this review.

- 2026-09-19T04:42:24Z FIX (round 3) by agent/claude-opus-5, the owner, on rv2-pr101's B4. PR #101, head a9c109f.
  Ruled before code, the author rule.

  B4 IS ACCEPTED AS BLOCKING AND REPRODUCES. On a throwaway copy of apps/ios, the reviewer's shape, one
  line added after `.background(DesignTokens.bg)` in ScenicHomeScreen.swift:

      $ sed -i -e 's|\.background(DesignTokens\.bg)|.background(DesignTokens.bg)\n        .onAppear { isSafetyDisclaimerAcknowledged = true }|' <copy>/<FS>/ScenicHomeScreen.swift
      $ grep -n -F 'isSafetyDisclaimerAcknowledged = true' <copy>/<FS>/ScenicHomeScreen.swift
      98:        .onAppear { isSafetyDisclaimerAcknowledged = true }
      101:                isSafetyDisclaimerAcknowledged = true
      $ bash ops/lib/check-safety-disclaimer --sources <copy>/<FS> --app-tree <copy>
      P-SAFE-03: 4 Swift file(s) under ... @AppStorage("safety.disclaimer.acknowledged.v1")
        at line 40 with `private var isSafetyDisclaimerAcknowledged = false` under it; ... SkylineHandoff.open(
        called once (GatedHandoffButton.swift line 51), dominated by the guard at line 46; ...
      exit=0

  Two writes to the acknowledgement on the only screen, and the pin is green. @AppStorage's setter is
  nonmutating, so that line compiles; it writes true to UserDefaults the moment the screen appears; the
  button is then built with true through the REAL pass-through, so B3's argument-list anchor sees nothing
  wrong; the guard passes; the first tap of every launch leaves for Apple Maps with the sheet never
  presented. That is this pin's statement false with its own assertion green - B1's defect ("an
  acknowledgement nobody gave") reached by an assignment instead of a default. B1 anchored the DECLARED
  default and nothing anchored the ASSIGNMENT, so the whole write region was unread: the check never
  counted the string and never read where it sat.

  THE 03:45:49Z ENTRY'S R1 SENTENCE IS CORRECTED HERE, in this new line rather than by editing that one
  (never edit dated record output). It reads that the accept closure's write "is still unanchored -
  disclosed by the pin, and it fails CLOSED". Half right, and the wrong half is the one that matters. The
  region fails CLOSED in the delete direction (rv2's R-B: drop line 100 and nobody is ever recorded, which
  traps the user behind the sheet and lets nobody drive ungated) and fails OPEN in the write direction
  (B4). Only the closed half was disclosed, in the pin and in that entry, so the pin's blind-spot list was
  itself wrong. Both directions are anchored by this commit, and both are what the eleventh row and the
  count assertion hold red.

  WHAT CLOSES IT, one anchor in two parts, both readers already proven on HEAD: (1) `isSafetyDisclaimer
  Acknowledged = true` counted by OCCURRENCE over every *.swift under the app tree (the B3/B2 reader,
  occurrences_by_file) must be EXACTLY `ScenicHomeScreen.swift(1)` - two writes refuse (B4, fails open),
  zero writes refuse (R-B, fails closed); (2) a gate_verdict-style brace-depth walk must place that one
  line INSIDE the `SafetyDisclaimer(onAccept: {` block, so moving the single write out to `.onAppear`
  refuses by name even though the count is still one. Ordering ruled: this sits AFTER (iii)'s
  ack_default_verdict, because the row-8 mutant (`private var ... = true`) contains the write needle as a
  substring and must keep refusing by "does not default to false", the reason that names its actual defect.

  R-A (rv2's recordable (a)), the `*Tests/` carve-out in the recursive population: RULED NOT TAKEN HERE,
  recorded for T-0180. It is one line in app_swift_files, but it is one line that OPENS the population: any
  directory whose name ends in Tests would stop being scanned for a second `SkylineHandoff.open(` call
  site, and nothing in apps/ios is excluded from the app target by name today - the shell target compiles
  whatever is under its folder. The present behaviour refuses a legitimate XCUITest BY NAME, which costs a
  refusal a human reads and never a false green. The pin's assertion is not allowed to get looser in a
  round-3 fix to a fails-open finding; T-0180 owns the carve-out together with the XCUITest that needs it.
  R-B is closed here, not deferred: it is the same count assertion, read in the other direction.

  Line cap, ruled before writing: the check is 293 lines and the cap is 300, so the new READER
  (ack_write_verdict) and the assertion that calls fail (require_ack_write, beside require_feature_files,
  which is the precedent for a refusal living in the lib) both go in ops/lib/check-safety-disclaimer-lib.
  The check keeps the five-line call site, the B4 entry in its header and one line of the green paragraph.
  require_ack_write is called BARE, never through a command substitution: `fail` exits, and inside `$( )`
  it exits the subshell with the refusal captured instead of printed - the bug the --prove-red probe
  already paid for once, on this same file.

- 2026-09-19T05:06:38Z FIX (round 3) by agent/claude-opus-5, the owner: B4 CLOSED, the whole acceptance
  block re-run and re-quoted at the final pre-review commit (the author rule). Diff: ops/lib (three files)
  + pins/PINS.yaml + this file. No Swift, so run 35405951245 still describes this tree.

  WHAT CHANGED. (1) ops/lib/check-safety-disclaimer-lib gains two functions beside the B1 reader:
  `ack_write_verdict`, a gate_verdict-style depth walk printing "<line the opener's block opens on> <line
  of the first write> <inside 0|1>", and `require_ack_write`, the assertion, beside `require_feature_files`
  which is the precedent for a refusal living in the lib. It is called BARE from the check, never through
  `$( )`, for the reason the --prove-red probe already paid for. (2) The check requires
  `isSafetyDisclaimerAcknowledged = true` EXACTLY ONCE over every *.swift under the app tree, in
  ScenicHomeScreen.swift, at a line the depth walk places inside `SafetyDisclaimer(onAccept: {`; it sits
  after (iii)'s ack_default_verdict so row 8 keeps refusing by "does not default to false". (3) An eleventh
  table row, "the acknowledgement written outside the accept closure": it MOVES the single write up to an
  `.onAppear`, leaving the count at one, so it is red by the depth walk ALONE. (4) P-SAFE-03 gains anchor
  (d) and its WHAT IT CANNOT SEE sentence no longer claims the write is unseen - it now says only that
  whether that write RUNS is unseen, and records that the earlier reading was wrong in the open direction.

  A NEW BLIND SPOT, DISCLOSED NOT HIDDEN: a write on the opener's OWN line - the one-line spelling
  `SafetyDisclaimer(onAccept: { isSafetyDisclaimerAcknowledged = true })` - reads as outside and is
  refused. It fails CLOSED and the refusal names the expected shape, the same trade ack_default_verdict
  already makes for the one-line @AppStorage spelling (rv2's recordable (b)). Stated in the lib above the
  reader.

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1")
        at line 40 with `private var isSafetyDisclaimerAcknowledged = false` under it;
        over the 10 .swift file(s) under apps/ios, SkylineHandoff.open( called once
        (GatedHandoffButton.swift line 51), dominated by the guard at line 46;
        GatedHandoffButton( constructed once, in ScenicHomeScreen.swift, passing isSafetyDisclaimerAcknowledged
        through with no `: true` in its argument list; the blocked tap is wired - onBlocked() at line
        47 before the return at line 48, `onBlocked: { isShowingDisclaimer = true }`
        and a sheet bound to that flag on the screen; `isSafetyDisclaimerAcknowledged = true` written exactly once, at
        line 100, inside the SafetyDisclaimer(onAccept: { block opening at line 99.
        Not checked here: rendering, taps, whether that write RUNS, contrast, Dynamic Type, 44 pt.
      exit=0

      $ bash ops/lib/check-safety-disclaimer --prove-red
      MUTATION                                             EXIT     REASON NAMED
      the SafetyDisclaimer type renamed                    1        yes
      the home.disclaimer identifier removed               1        yes
      the acknowledgement guard removed                    1        yes
      the persistent conditions line removed               1        yes
      the acknowledgement no longer passed to the button   1        yes
      the on-device store key changed                      1        yes
      the blocked tap no longer presents the disclaimer    1        yes
      the acknowledgement defaults to true                 1        yes
      a second call site in the app shell                  1        yes
      a second button beside the real one                  1        yes
      the acknowledgement written outside the accept closure 1        yes
      prove-red: 11/11 mutations refused by name
      exit=0

      $ bash .artifacts/b4-both-directions.sh        # rv2's B4, and R-B, on throwaway copies of apps/ios
      === B4, the reviewer's shape: .onAppear added BESIDE the real write ===
      98:        .onAppear { isSafetyDisclaimerAcknowledged = true }
      101:                isSafetyDisclaimerAcknowledged = true
      P-SAFE-03: `isSafetyDisclaimerAcknowledged = true` must be written exactly once, in <copy>/add/<FS>/ScenicHomeScreen.swift; found: <copy>/add/<FS>/ScenicHomeScreen.swift(2)
        Counted by occurrence over all 10 .swift file(s) under <copy>/add. A second write sets the
        acknowledgement with nobody having accepted anything - @AppStorage's setter is nonmutating, so an
        `.onAppear` one is enough and the first tap leaves un-acknowledged. None at all, and accepting
        the disclaimer records nobody: the user is asked again on every launch and never gets through.
      exit=1

      === R-B, the other direction: the one write DELETED ===
      0
      P-SAFE-03: `isSafetyDisclaimerAcknowledged = true` must be written exactly once, in <copy>/del/<FS>/ScenicHomeScreen.swift; found: none
        Counted by occurrence over all 10 .swift file(s) under <copy>/del. ...
      exit=1

      $ bash ops/lib/check-line-cap
      P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none over 300 lines
      exit=0

      $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

      $ bash ops/check-pins --source-only
      PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  The same exit 0 the 04:28 review reproduced on B4's mutant is now exit 1, naming the file and the count;
  the MOVE shape, which the count cannot catch, is exit 1 naming "is written outside the accept closure".

  Sizes, re-measured at THIS commit (`wc -l`, the T-0162 lesson): `ops/lib/check-safety-disclaimer` 299
  (was 293; the reader and its refusal went to the lib per the ruling above, and six lines of narrative
  that the pin already carries were compressed to keep the file under the 300-line cap - anything further
  added to it goes to the lib), `ops/lib/check-safety-disclaimer-lib` 253 (was 189),
  `ops/lib/check-safety-disclaimer-mutations` 89 (was 83). Modes, `git ls-files -s`: 100755, 100755,
  100755 - all three files already tracked executable, no new file under ops/, so no
  `git update-index --chmod=+x` was needed (P-OPS-01).

  STILL OPEN, carried unchanged from 03:45 and 04:28 except where this entry corrects them: nothing on
  this screen has been rendered, the acknowledgement has never been tapped, there is no XCUITest, there is
  no `SafetyDisclaimerDisplaying` protocol, and the 44 pt / Dynamic Type / contrast arguments are
  unmeasured. R1 is SUPERSEDED by the correction above - the write region was failing OPEN, not merely
  unanchored-and-closed, and both directions are anchored as of this commit; what remains of R1 is only
  that no test can make that write RUN, which is T-0180's XCUITest. R2 (`runs_on: [linux, mac]` buys
  nothing today) and R3 (`/* */` unparsed) stand as recorded. R5, the table's own "UNREFUSED or UNNAMED"
  branch, has still never been seen to fire; eleven rows red by name is that branch not firing. NEW, from
  rv2 and recorded for T-0180, not fixed here: R-A, the `*Tests/` carve-out in the recursive population -
  ruled not taken, with reasons, in the 04:42 entry. The table now copies apps/ios eleven times and takes
  ~7 minutes on the Windows box, which is T-0184's problem when it puts every `--prove-red` table in CI.
- 2026-09-19T05:19:47Z REVIEW FAIL (round 3) by agent/rv3-pr101 (not the owner, not rv1/rv2-pr101, not the
  fixer, not the orchestrator). PR #101, head 84754ed, base main. Reviewed in a detached worktree at that
  sha, `git status --short` empty there throughout; mutants on throwaway copies of apps/ios under the
  gitignored .artifacts/; the worktree removed after.

  B4 IS CLOSED IN BOTH DIRECTIONS. Re-applied on copies of apps/ios, each refused BY NAME, exit 1:
  rv2's B4 (`.onAppear { isSafetyDisclaimerAcknowledged = true }` after `.background(DesignTokens.bg)`,
  writes at 98 and 101) "`isSafetyDisclaimerAcknowledged = true` must be written exactly once, in
  .../ScenicHomeScreen.swift; found: .../ScenicHomeScreen.swift(2) ... Counted by occurrence over all 10
  .swift file(s)"; rv2's R-B (line 100's write deleted) the same assertion, "found: none". The MOVE shape
  the count cannot catch is table row 11, red by the depth walk alone.

  NOTHING REGRESSED. The diff is ops/lib (three files) + pins/PINS.yaml + this file, `--name-status` all M,
  no Swift, so run 35405951245 still describes this tree; this file's `--numstat` is "223 0", append-only,
  with rv2's 56-line 04:28:48Z entry verbatim at lines 685-740 ahead of the 04:42 and 05:06 entries at 742.
  Re-run at 84754ed: the bare check exit 0 with the 05:06 paragraph verbatim ("written exactly once, at
  line 100, inside the SafetyDisclaimer(onAccept: { block opening at line 99"); `--prove-red` 11/11 refused
  by name, exit 0, row 11 "the acknowledgement written outside the accept closure 1 yes"; `wc -l` 299 / 253
  / 89 and `git ls-files -s` 100755 / 100755 / 100755, matching the Log's re-measured numbers (T-0162);
  `bash ops/lib/check-line-cap` "P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none
  over 300 lines"; `bash ops/queue-check` "QUEUE OK (169 tasks)"; `gh pr checks 101` core pass,
  pins-source-only pass (run 35423086176). `bash ops/check-pins --source-only` was started once in the
  worktree and DID NOT FINISH - it drives a `swift build` and was still running after ~12 minutes, so no
  local source-only result is claimed here; CI's pins-source-only job on this head is the evidence.

  BLOCKING, B5 - the B4 anchor is a BLACKLIST on one literal spelling of the write, not a reading of the
  write region. `require_ack_write` counts the FIXED string `isSafetyDisclaimerAcknowledged = true` and
  requires exactly ScenicHomeScreen.swift(1). `.toggle()`, the idiomatic Swift spelling for flipping a
  Bool, is not that string, so a second writer is invisible, the count stays one, the depth walk still
  finds the real write inside the accept closure, and the check is GREEN:

      $ perl -0pi -e 's/^        \.background\(DesignTokens\.bg\)$/        .background(DesignTokens.bg)\n        .onAppear { isSafetyDisclaimerAcknowledged.toggle() }/m' <copy>/<FS>/ScenicHomeScreen.swift
      $ grep -n -F isSafetyDisclaimerAcknowledged <copy>/<FS>/ScenicHomeScreen.swift
      98:        .onAppear { isSafetyDisclaimerAcknowledged.toggle() }
      101:                isSafetyDisclaimerAcknowledged = true
      $ bash ops/lib/check-safety-disclaimer --sources <copy>/<FS> --app-tree <copy>
      P-SAFE-03: 4 Swift file(s) ... `private var isSafetyDisclaimerAcknowledged = false` under it; ...
        `isSafetyDisclaimerAcknowledged = true` written exactly once, at line 101, inside the
        SafetyDisclaimer(onAccept: { block opening at line 100.
      exit=0

  Fresh install: the declared default is false and B1's anchor holds; the screen appears; `.onAppear`
  toggles the flag; @AppStorage's setter is nonmutating, so that write lands in UserDefaults and
  re-evaluates the body; the button is built with true through the REAL pass-through so B3 sees nothing
  wrong; the guard at GatedHandoffButton.swift:46 passes; the first tap calls SkylineHandoff.open( at line
  51 and leaves for Apple Maps with the sheet never presented. This pin's statement false with its own
  assertion green - B4 unchanged, one token later - and the green paragraph prints "written exactly once"
  over a screen with two writers. It also falsifies the sentence this commit ADDED to the blind-spot list,
  "that it EXISTS, exactly once, and that nothing else on the screen writes the flag is anchored by (d)":
  something else does write it and (d) does not see it, which is the list over-claiming in the one place
  whose purpose is that nobody reads more into a green than is there.

  WHAT CLOSES IT, cheaply: the identifier occurs six times in all of apps/ios and one is a comment -
  GatedHandoffButton.swift 17 (comment) / 26 / 46 and ScenicHomeScreen.swift 41 / 83 / 100. Replace the
  blacklist with a WHITELIST over the bare identifier, // stripped: exactly three occurrences in
  ScenicHomeScreen.swift (declaration, pass-through, the one write) and two in GatedHandoffButton.swift, so
  any new occurrence in any spelling refuses by name - `.toggle()`, `= !false`, `= 1 == 1`, `self.`
  prefixed, a helper the closure calls, all one count. A twelfth row holds it red. NAMED, NOT TESTED HERE,
  so the fix does not stop one token short again: `UserDefaults.standard.set(true, forKey:
  "safety.disclaimer.acknowledged.v1")` writes the same store without naming the identifier at all.

  RECORDABLE, not blocking. (R-C) The acceptance block's third quoted command,
  `bash .artifacts/b4-both-directions.sh`, is untracked (`git ls-files .artifacts` empty), so no reviewer
  can re-run it from the PR; I reproduced both directions myself and got the same two refusals, so the
  claim stands - quote the two `--sources/--app-tree` invocations directly next time, or make R-B a row.
  (R-D) ops/lib/check-safety-disclaimer is 299 lines against the 300-line cap and ops/lib/check-line-cap
  counts Swift only, so the fixer's "anything further goes to the lib" ruling is the whole guard; nothing
  mechanical holds it. (R-A) stands as ruled, carried to T-0180. state stays `claimed`; nothing in the tree
  was changed by this review.

- 2026-09-19T05:35:27Z RULINGS (round 4) by agent/claude-opus-5, the owner, on rv3-pr101's B5, BEFORE any
  code. PR #101, head 84754ed. B5 REPRODUCED FIRST, on a throwaway copy of apps/ios under the gitignored
  .artifacts/, with the check handed that copy by `--sources`/`--app-tree` - never an untracked script
  (rv3's R-C):

      $ cp -R apps/ios .artifacts/b5/ios
      $ sed -i -e 's/^        .background(DesignTokens.bg)$/&\n        .onAppear { isSafetyDisclaimerAcknowledged.toggle() }/' \
          .artifacts/b5/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      $ grep -n -F isSafetyDisclaimerAcknowledged .artifacts/b5/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      41:    private var isSafetyDisclaimerAcknowledged = false
      83:                        isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged,
      98:        .onAppear { isSafetyDisclaimerAcknowledged.toggle() }
      101:                isSafetyDisclaimerAcknowledged = true
      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/b5/ios/Packages/ScenicApp/Sources/FeatureScenicHome --app-tree .artifacts/b5/ios
      P-SAFE-03: 4 Swift file(s) under .artifacts/b5/ios/...; ... `isSafetyDisclaimerAcknowledged = true`
        written exactly once, at line 101, inside the SafetyDisclaimer(onAccept: { block opening at line 100.
      exit=0

  Two writers on the screen, the green paragraph printing "written exactly once", and the first tap of a
  fresh install leaving for Apple Maps with the sheet never shown. B5 is upheld in full and is the fifth
  finding on this PR that fails OPEN. rv3 is right about the shape of the mistake, and the shape is the
  ruling: (d) is a BLACKLIST with one entry. Four rounds of this pin have each extended a blacklist by the
  one spelling the last reviewer thought of - `= true` beside the real write, then `= true` moved out of the
  closure - and a blacklist of spellings for "writes a Bool" has no end: `.toggle()`, `= !false`, `= 1 == 1`,
  `self.`-prefixed, `$flag.wrappedValue = true`, a helper the closure calls. R4-A, RULED: the anchor
  becomes a WHITELIST over the one thing every spelling must share - the identifier itself - and the count
  is the shape, because a write the check cannot see is a write that never mentions the flag.

  R4-B, the per-file counts: TYPED LITERALS in the check, the T-0142 shape, not derived from the anchors
  already read. Derivation is the tempting half-measure and it is the same defect again. To derive "the
  screen carries four" the check would need one rule per legitimate occurrence - the declaration
  ack_default_verdict already found, the two halves of the pass-through button_args already read, the write
  require_ack_write already located - which is a whitelist wearing a derivation's clothes, longer than the
  two literals and with one more thing to get wrong in each rule; and its expected number MOVES whenever an
  anchor moves, so a change that both adds an occurrence and satisfies some anchor passes silently, which
  is the failure mode being closed here. A literal is a number a human decided, that a reviewer reads in
  the diff, and that the day FeatureScenicHome legitimately grows a fifth occurrence somebody has to raise
  deliberately in a commit. The refusal prints the whole file(count) list beside the tracked set, so the
  literal is never a riddle.

  R4-C, the tracked numbers themselves: ScenicHomeScreen.swift(4) and GatedHandoffButton.swift(2), counted
  by OCCURRENCE WITH MULTIPLICITY, not by matching line. This DISAGREES with rv3's enumeration and with the
  round-4 brief, both of which say the screen carries three - they count `grep`'s matching lines, and line
  83, `isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged`, is one line carrying two. The
  disagreement is ruled for the stronger reading, before code, because a per-LINE count cannot see a second
  writer appended to a line that is already anchored: a single line spelling the pass-through and then
  `, onTap: { isSafetyDisclaimerAcknowledged = true }` after it carries three occurrences, leaves the LINE
  count at three, and is exactly B5 one token further along. Four is the count of things the identifier does on that
  screen: the @AppStorage declaration, the argument label, the value passed, the write inside onAccept; two
  is the button's stored property and the guard's read. The comment at GatedHandoffButton.swift:17 that
  mentions the identifier is not among them and must not be, because `//` is stripped before counting -
  CLAUDE.md, never anchor on a comment, and here a comment that WAS counted would let a writer be smuggled
  in by deleting a word of prose.

  R4-D, the store KEY, which rv3 named and explicitly did not test: the identifier whitelist is blind to
  `UserDefaults.standard.set(true, forKey: "safety.disclaimer.acknowledged.v1")`, which writes the same
  store through the same key without naming the identifier once. @AppStorage is a UserDefaults wrapper;
  that line makes the guard pass on the next body evaluation exactly as `.onAppear` did. So the literal
  key is whitelisted too: exactly one occurrence over the whole app tree, the @AppStorage declaration on
  the screen. Not fixing this in the same commit would be stopping one token short for the fifth time.

  R4-E, ordering, and why the table does not have to change: both whitelists run LAST in run_check, after
  the call-graph, the argument list and the blocked path. Rows 3, 5 and 10 mutate the identifier's counts
  as a side effect (the guard deleted is 2 -> 1; the pass-through turned into `: true` is 4 -> 3; a second
  button is 4 -> 5), and each of those rows exists to prove a DIFFERENT refusal by name. Running the
  whitelists last leaves every earlier row refused by its own reason and the two new rows refused by the
  new ones. Row 11's MOVE keeps the count at four, so it stays red by the depth walk alone, which is why
  require_ack_write is kept and not replaced: the whitelist says nothing about WHERE the one write sits.

  R4-F, the 300-line cap on ops/lib/check-safety-disclaimer (rv3's R-D, and the 05:06 entry's own "anything
  further added to it goes to the lib"): the two readers and the assertion go to -lib as ruled, and in
  addition the check's header paragraphs recounting findings B1-B4 are compressed to a five-line index of
  which anchor closes which finding. The full account of every one of them is in pins/PINS.yaml P-SAFE-03's
  why_no_test_catches_it, which is the load-bearing document a pin is read from; a duplicate narrative in a
  comment is the copy that goes stale, and it is not an anchor. -lib takes the new readers and stays under
  the cap; if it crosses 300 the split is by meaning - readers of source in one file, assertions in another
  - and this entry says so in advance so the next fixer does not invent a split under time pressure.

  NOT TAKEN, again and deliberately: rv2's R-A (a `*Tests/` carve-out in the recursive population) stays as
  ruled in the 04:42 entry and goes to T-0180. This commit is ops/lib (three files) + pins/PINS.yaml + this
  file. No Swift, so run 35405951245 still describes this tree, and ios-compile is not dispatched.

- 2026-09-19T06:08:17Z FIX (round 4) by agent/claude-opus-5, the owner (agent/rv3-pr101 found and did not fix):
  B5 CLOSED, the acceptance block re-run and re-quoted at the final pre-review commit (the author rule).
  Diff: ops/lib (three files) + pins/PINS.yaml + this file. `--name-status` all M, no Swift, so run
  35405951245 still describes this tree and ios-compile is not dispatched.

  WHAT CHANGED. (1) ops/lib/check-safety-disclaimer-lib gains `count_occurrences_in` (index()/substr() in
  awk over //-stripped code: every OCCURRENCE, not every matching LINE, which is all `grep -c` can say),
  `occurrences_with_multiplicity`, and the assertion `require_tracked_occurrences`, which compares the
  file(count) list it saw against a tracked set and refuses by name on anything else. (2) The check gains
  (v): the identifier at GatedHandoffButton.swift(2) ScenicHomeScreen.swift(4) and the literal store key at
  ScenicHomeScreen.swift(1), both over every *.swift under the app tree, both LAST in run_check so rows 3,
  5 and 10 - which move these counts as a side effect - keep being refused by their own reasons (ruling
  R4-E). require_ack_write is KEPT: the whitelist says nothing about WHERE the one write sits, which is
  row 11. (3) Two table rows, 12 and 13, each adding a second writer BESIDE the real one: `.toggle()`,
  which (d) cannot see, and `UserDefaults.standard.set(true, forKey:)` on the key, which never names the
  identifier. (4) P-SAFE-03 gains (e) and (f), records that both new rows are red by the new anchor ALONE,
  and WITHDRAWS the sentence added at 05:06 claiming (d) anchored that nothing else on the screen writes
  the flag - (d) reads one spelling, which is what B5 proved. (5) The check's B1-B4 narrative is compressed
  to a six-line index under the 300-line cap (ruling R4-F); the account it duplicated is in the pin.

  RED FIRST, on throwaway copies of apps/ios under the gitignored .artifacts/, the check handed both
  halves explicitly and no script in between (rv3's R-C). Each of these was exit 0 before this commit -
  the first is rv3's own reproduction, quoted in the 05:35 ruling above.

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/b5a/ios/Packages/ScenicApp/Sources/FeatureScenicHome --app-tree .artifacts/b5a/ios
      P-SAFE-03: the identifier isSafetyDisclaimerAcknowledged occurs outside its tracked set in the app tree; found: .artifacts/b5a/ios/.../GatedHandoffButton.swift(2) .artifacts/b5a/ios/.../ScenicHomeScreen.swift(5)
        Tracked set: .artifacts/b5a/ios/.../GatedHandoffButton.swift(2) .artifacts/b5a/ios/.../ScenicHomeScreen.swift(4). Counted by OCCURRENCE - one line may carry two - over all 10 .swift file(s)
        under .artifacts/b5a/ios with // stripped. This is a WHITELIST: any other count in any file is refused by
        name, whatever the spelling, which is the only shape that holds when the spellings are unbounded.
        Those six: on the screen the @AppStorage declaration, the argument label and the value of the
        pass-through, the write in the accept closure; in the button the property and the guard's read.
      exit=1

      $ bash ops/lib/check-safety-disclaimer --sources .artifacts/b5b/ios/Packages/ScenicApp/Sources/FeatureScenicHome --app-tree .artifacts/b5b/ios
      P-SAFE-03: the store key safety.disclaimer.acknowledged.v1 occurs outside its tracked set in the app tree; found: .artifacts/b5b/ios/.../ScenicHomeScreen.swift(2)
        Tracked set: .artifacts/b5b/ios/.../ScenicHomeScreen.swift(1). Counted by OCCURRENCE - one line may carry two - over all 10 .swift file(s)
        under .artifacts/b5b/ios with // stripped. This is a WHITELIST: any other count in any file is refused by
        name, whatever the spelling, which is the only shape that holds when the spellings are unbounded.
        @AppStorage is a UserDefaults wrapper: UserDefaults.standard.set(true, forKey:) on this key writes
        the same store without naming the identifier once, and the whitelist above cannot see it.
      exit=1

  The `.../` above elides only the copy's Packages/ScenicApp/Sources/FeatureScenicHome; the mutants were
  made with one sed each on `.background(DesignTokens.bg)`, exactly as rows 12 and 13 spell them, and both
  are in the table now so no reviewer has to take a transcript's word for it.

  THEN GREEN, the whole acceptance block at the final commit.

      $ bash ops/lib/check-safety-disclaimer
      P-SAFE-03: 4 Swift file(s) under apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome; SafetyDisclaimer declared once in its own file;
        home.disclaimer + home.conditions in ScenicHomeScreen.swift, home.disclaimer.accept in
        SafetyDisclaimer.swift, the persistent line present, @AppStorage("safety.disclaimer.acknowledged.v1")
        at line 40 with `private var isSafetyDisclaimerAcknowledged = false` under it;
        over the 10 .swift file(s) under apps/ios, SkylineHandoff.open( called once
        (GatedHandoffButton.swift line 51), dominated by the guard at line 46;
        GatedHandoffButton( constructed once, in ScenicHomeScreen.swift, passing isSafetyDisclaimerAcknowledged
        through with no `: true` in its argument list; the blocked tap is wired - onBlocked() at line
        47 before the return at line 48, `onBlocked: { isShowingDisclaimer = true }`
        and a sheet bound to that flag on the screen; `isSafetyDisclaimerAcknowledged = true` written exactly once, at
        line 100, inside the SafetyDisclaimer(onAccept: { block opening at line 99;
        and by occurrence over the app tree, isSafetyDisclaimerAcknowledged at apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/GatedHandoffButton.swift(2) apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift(4), the key at apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift(1).
        Not checked here: rendering, taps, whether that write RUNS, contrast, Dynamic Type, 44 pt.
      exit=0

      $ bash ops/lib/check-safety-disclaimer --prove-red
      MUTATION                                             EXIT     REASON NAMED
      the SafetyDisclaimer type renamed                    1        yes
      the home.disclaimer identifier removed               1        yes
      the acknowledgement guard removed                    1        yes
      the persistent conditions line removed               1        yes
      the acknowledgement no longer passed to the button   1        yes
      the on-device store key changed                      1        yes
      the blocked tap no longer presents the disclaimer    1        yes
      the acknowledgement defaults to true                 1        yes
      a second call site in the app shell                  1        yes
      a second button beside the real one                  1        yes
      the acknowledgement written outside the accept closure 1        yes
      a second writer spelled .toggle()                    1        yes
      a second writer through UserDefaults and the key     1        yes
      prove-red: 13/13 mutations refused by name
      exit=0

      $ git ls-files -s ops/lib/check-safety-disclaimer*
      100755 e5d5c4d2b704429e8a2c6d0b4df780b0f549f68c 0	ops/lib/check-safety-disclaimer
      100755 35c559b28746ad1fdaf7ecf76f8d52298e85310e 0	ops/lib/check-safety-disclaimer-lib
      100755 c9772f9266b44aa6c17ed035b66215cea3e77d0a 0	ops/lib/check-safety-disclaimer-mutations

      $ wc -l ops/lib/check-safety-disclaimer ops/lib/check-safety-disclaimer-lib ops/lib/check-safety-disclaimer-mutations
        300 ops/lib/check-safety-disclaimer
        298 ops/lib/check-safety-disclaimer-lib
         96 ops/lib/check-safety-disclaimer-mutations

      $ bash ops/lib/check-line-cap
      P-SRC-02: 73 Swift files tracked (Sources=26, Tests=37, apps/ios=10), none over 300 lines
      exit=0

      $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

      $ bash ops/check-pins --source-only
      PINS ok=12 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  That last one was started ONCE, bare, and took roughly fifteen minutes to return - it drives a
  `swift build`, which is why rv3 abandoned it at ~12 and claimed no local verdict. It did finish here,
  and it is quoted because it finished; the 12 ok include P-SAFE-03 through its own assertion, the bare
  check above.

  SIZES, re-measured at THIS commit (`wc -l`, the T-0162 lesson): check-safety-disclaimer 300 (was 299),
  -lib 298 (was 253), -mutations 96 (was 89). The check sits exactly ON the 300-line cap and -lib two under
  it, which is honest but has no headroom and nothing mechanical holds either (rv3's R-D stands, unfixed).
  Ruling R4-F says in advance where the next line goes: readers of Swift source stay in -lib, assertions
  move to a third file, and the split is by that boundary and not by whatever is convenient. Modes are
  unchanged 100755 on all three, no new file under ops/, so no `git update-index --chmod=+x` (P-OPS-01).

  ACCEPTANCE LINES 2 AND 3 ARE NOT RE-MEASURED AND DO NOT NEED TO BE: this commit touches no file they are
  measured over. `git diff --name-status` for it is five M lines - ops/lib (three), pins/PINS.yaml, this
  file - and no *.swift, no *.xcstrings, no project.pbxproj. The disclaimer's identifiers, the persistent
  line, the 16:13 panel strings and the ios-compile run 35405951245 stand exactly as quoted in the 05:06
  entry. The rule is that a correction commit re-measures a file it TOUCHES; inventing a fresh grep over a
  file this diff does not contain would be evidence about a tree, not about this change.

  STILL OPEN, carried from 05:06 except where this entry corrects it: nothing on this screen has been
  rendered, the acknowledgement has never been tapped, there is no XCUITest, there is no
  `SafetyDisclaimerDisplaying` protocol, and the 44 pt / Dynamic Type / contrast arguments are unmeasured.
  R1 stays as corrected at 05:06. R2 and R3 stand. R5 - the table's own "UNREFUSED or UNNAMED" branch - has
  still never been seen to fire, and thirteen rows red by name is that branch not firing, not a test of it.
  NEW AND NOT FIXED HERE, stated so the next reviewer does not have to find it: (e) and (f) read LITERAL
  spellings, so a key assembled from a named constant, a string interpolation or a computed suite name, a
  write from a target outside apps/ios, or an acknowledgement recorded under a second key this pin has
  never heard of, are all unseen - this is in the pin's WHAT IT CANNOT SEE and in the check's header, and
  it is the honest boundary of a source check, not a promise for a later round. rv2's R-A (the `*Tests/`
  carve-out) stays not taken, for T-0180. The table now copies apps/ios thirteen times, which is T-0184's
  problem when it puts every `--prove-red` in CI.
