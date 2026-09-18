---
id: T-0167
title: ios-compile follow-up - commit Package.resolved, build with Xcode 26 (the plan's SDK), and pin the guardrail check
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:58Z
lease_expires_at: 2026-09-19T04:32:58Z
worktree: .worktrees/T-0167
branch: task/T-0167
exclusive: [package-resolved]
touches: [.github/workflows/ios-compile.yml, .github/workflows/linux-core.yml, ops/lib/check-ios-compile-guardrails.py, apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved, pins/PINS.yaml, queue/LOCKS/]
pins_affected: []
reviewer: agent/rv1-pr97
depends_on: [T-0157]
verify: [ops/check-pins]
acceptance:
  - "python ops/lib/check-ios-compile-guardrails.py -> IOS-COMPILE-GUARDRAILS OK: ios-compile.yml equals the pinned workflow: dispatch-only, contents: read, ['macos-15'], time-boxed, one job-level env key (DEVELOPER_DIR=/Applications/Xcode_26.3.app/Contents/Developer), and a build that cannot be skipped or fail green, exit 0"
  - "python ops/lib/check-ios-compile-guardrails.py --prove-red -> 32 '[red rc=1]' lines, each naming the guardrail or the first path that differs, including the five added here (a SECOND env key at the job level; DEVELOPER_DIR pointed elsewhere (the image default, 16.4); env: at the WORKFLOW level, inherited by every job; env: on the build step, overriding the job's toolchain; the DEVELOPER_DIR existence guard deleted) and -disableAutomaticPackageResolution dropped; 3 '[green rc=0]' legitimate spellings; '[refused rc=2] unreadable YAML: ... ParserError'; '[green rc=0] the shipped file'; then PROVE-RED OK: 32 mutations red, 3 legitimate spellings green, 0 unexpected result(s), exit 0. Every mutation applies exactly once or the run refuses"
  - "sha256sum <the artifact ios-compile-35391464739 copy> apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved -> the same digest twice, 2c13b9b6788a636eee9026a10c5a31560dcc2ec670be941fbfa50854ef11c44a: committed byte for byte, 0 CR bytes"
  - "git check-ignore -v apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved -> no output, exit 1 (NOT ignored; .gitignore's .swiftpm/ does not cover project.xcworkspace/xcshareddata/swiftpm/)"
  - "STEP 1 DISPATCH, run 35393082335 (task/T-0167 at 15eb979), conclusion success: '** BUILD SUCCEEDED **', and the 'what the build wrote into the tree' step printed ONLY the find output - nothing at all from git status --porcelain --untracked-files=all, so no ?? line and no M line"
  - "STEP 2 DISPATCH, run 35393590488 (task/T-0167 at 6af2c69), conclusion success: toolchain step prints DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer, Xcode 26.3, Build version 17C529, Apple Swift version 6.2.4; '** BUILD SUCCEEDED **'; grep -c ' error:' over the downloaded log = 0; one benign appintentsmetadataprocessor warning; status step again silent from git status"
  - "FINAL DISPATCH on the shipped tree, run 35394086754 (task/T-0167 at d9a09d3aff1fe10531b008140dbaf2579d61a0de), conclusion success: Xcode 26.3 / Build version 17C529 / Apple Swift version 6.2.4, '** BUILD SUCCEEDED **', grep -c ' error:' = 0, status step silent from git status"
  - "P-OPS-06 seen RED BY NAME then green, as the pin: the assertion exactly as pins/PINS.yaml spells it, run through ops/lib/pins.py against a workflow whose DEVELOPER_DIR was pointed at 16.4 -> exit non-zero, 'jobs.simulator-build.env: must be exactly {'DEVELOPER_DIR': '/Applications/Xcode_26.3.app/Contents/Developer'} ... (found ... Xcode_16.4.app ...)' + 'IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s) gone'; restored with git checkout --, byte-identical, git status --short on that path empty, assertion exit 0 again. The repo's own reader parses the new entry: parsed 24 pins, ids unique: True"
  - "wc -l ops/lib/check-ios-compile-guardrails.py -> 296 (under CLAUDE.md's 300-line cap); git status --short in the worktree -> empty"
  - "NOT RUN, on the record: bash ops/check-pins and bash ops/test locally - on this box the default swift scratch path does not build inside a worktree; CI at the PR head is the evidence, read ONCE. Also not run here: the two linux-core.yml PyYAML paths (neither job runs on Windows), so which branch pins-source-only took is a fact only its own log states; and anything on a device - this tree has never been on one, and nothing here proves signing, TestFlight or the plan's push-to-phone gate (T-0009)"
---
## Brief

T-0157's workflow ran for the first time on 2026-09-18 and the record is in `queue/done/T-0157-*.md`:
GREEN on main (run 35391464739: Xcode 16.4, Build version 16F6, Apple Swift 6.1.2, `** BUILD SUCCEEDED **`, zero
compiler errors, one benign appintents warning) and RED on a throwaway branch carrying a deliberate type error
(run 35391738972: `DesignTokens.swift:104:31: error: cannot convert value of type 'String' ...`,
`** BUILD FAILED **`, exit code 65, job conclusion failure, with both `if: always()` steps still succeeding -
they did not mask it). `apps/ios` compiles. Three things the first run surfaced:

1. **`Package.resolved` is written by every run and tracked by nobody.** The green run printed
   `?? apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` and uploaded
   it (artifact `ios-compile-35391464739`, also at `.artifacts/ios-compile/art/` on the dev box). It is a
   serial-only file (CLAUDE.md): declare `exclusive:`, commit the runner-produced file byte for byte, add
   `-disableAutomaticPackageResolution` to the pinned build script so a drifting resolution FAILS the job
   instead of silently re-resolving, and update `EXPECTED` in the guardrail check in the same commit (the
   check compares the whole workflow by equality - that is the point). Green = a dispatch whose
   `git status --porcelain --untracked-files=all` step prints nothing.
2. **The runner's default is Xcode 16.4; the plan requires the iOS 26 SDK** (plan: "Xcode 26 / iOS 26 SDK
   mandatory since 2026-04-28"). The image has `Xcode_26.0` through `Xcode_26.3` installed. Select one with
   `DEVELOPER_DIR` - which means deliberately allowing exactly ONE `env:` key at the job level in the pinned
   structure (today the check refuses `env:` anywhere, by name). RULE in the Log: which 26.x, pinned by exact
   path, and what happens when the image drops it (the job must fail by name, not fall back to the default).
   Expect real compiler findings: Xcode 26's Swift may flag things 16.4 did not; fix them in `apps/ios/` under
   their own touches or file them.
3. **Nothing runs the guardrail check** (every reviewer of PR #90 recorded this). Pin it under a P-OPS id that
   is free on main AND on open PRs (`gh pr list --state open`, then grep each head's `pins/PINS.yaml`); anchor:
   source; runs_on: [linux, mac]; the assertion is the check itself, and `--prove-red` is its red.
4. Minor, from the run log: `actions/checkout@v4` / `upload-artifact@v4` print a Node 20 deprecation notice;
   decide whether to move the allowlist to the next major in the same change or leave it with a date.

Dispatch with `gh workflow run ios-compile.yml --ref <branch>` - now that the file is on main it runs on any
ref, which is also how T-0151, T-0152 and T-0153 can prove their Swift compiles before review.

## Log
- 2026-09-18T21:00:00Z filed by agent/claude-fable-5-1 after the first green and first red dispatch of ios-compile. Not started.
- 2026-09-18T20:32:58Z claimed by agent/claude-opus-5; lease until 2026-09-19T04:32:58Z
- 2026-09-18T20:41:48Z **RULINGS BEFORE CODE - agent/claude-opus-5 (owner, author).** Read end to end first: `CLAUDE.md`, this Brief, `.github/workflows/ios-compile.yml`, `ops/lib/check-ios-compile-guardrails.py`, `ops/lib/pins.py`, `.github/workflows/linux-core.yml`, `.gitignore`, `.gitattributes`, `.githooks/pre-commit`, and `queue/done/T-0157-*.md`. Eight places where the Brief, the plan, the shipped code and reality disagree or are silent. Each is ruled here, before any edit.

  **R1 - `.gitignore` vs. the path xcodebuild writes.** `.gitignore` carries `.swiftpm/`; the runner wrote `apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` - `swiftpm`, no dot, inside `project.xcworkspace`. Measured rather than read: `git check-ignore -v <that path>` printed nothing and exited 1, i.e. NOT ignored. RULING: commit the file as it is; no `.gitignore` edit and no negation rule. (The `.swiftpm/` entry is for the directory SPM writes beside a package, which is a different path.)

  **R2 - byte for byte, on a Windows checkout with `* text=auto eol=lf`.** The Brief says byte for byte; `.gitattributes` normalises text files to LF and the pre-commit hook refuses CRLF in a staged blob. Measured: the artifact file contains 0 CR bytes and 15 LF bytes (`tr -dc '\r' < f | wc -c` -> `0`), so LF normalisation is a no-op on it, and after `cp` both paths print the same digest - `2c13b9b6788a636eee9026a10c5a31560dcc2ec670be941fbfa50854ef11c44a`. RULING: plain `cp`, no rewriting, no re-indenting, and the digest is the evidence in the acceptance block.

  **R3 - what makes a drifting resolution fail.** The Brief asks for `-disableAutomaticPackageResolution` on the build script AND for a green run whose status step prints no `??` line. Those are two different mechanisms and only one of them is a gate: the flag makes xcodebuild refuse to resolve to versions other than the ones recorded in `Package.resolved`, so the build fails; the `what the build wrote into the tree` step has no exit status of its own (it prints and returns 0) and never did. RULING: the flag is the gate, the status step stays a printed record, and its output is quoted in this Log rather than asserted by the workflow. Making that step fail on a dirty tree would also fail on any unrelated artifact and is not what T-0157 built it for; not done, and stated here so a reviewer does not have to guess whether it was overlooked.

  **R4 - which Xcode, and what happens when the image drops it.** The plan requires Xcode 26 / the iOS 26 SDK; run 35391464739's toolchain step printed Xcode 16.4 (Build 16F6, Apple Swift 6.1.2), which is the image default. The image carries `Xcode_26.0.app` through `Xcode_26.3.app`. RULING: select the NEWEST 26.x by exact path - `DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer` - at the JOB level, not the workflow level and not on a step, so every step of this job sees one toolchain and the guardrail check can pin it by equality in exactly one place. A bare `xcode-select` step or a glob would let the job silently fall back to 16.4 when 26.3 leaves the image, so the build step's FIRST line is `test -d "$DEVELOPER_DIR" || { echo "ios-compile: $DEVELOPER_DIR is not on this image"; exit 1; }` - a named, non-zero failure before xcodebuild runs.

  **R5 - `env:` was refused by name at every level, and the plan needs exactly one key.** `named_problems()` refuses `jobs.<job>.env` outright (`an environment is a way to hand a token to a script`) and the workflow header says the guardrails hold `at EVERY level GitHub lets it be overridden`. R4 cannot be implemented without one env key. RULING: allow EXACTLY ONE job-level key, `DEVELOPER_DIR`, with exactly the pinned value, pinned by equality in `EXPECTED` and refused BY NAME on every other spelling: a second key at the job level, a different value for `DEVELOPER_DIR`, `env:` at the workflow level, `env:` on any step. Two new `--prove-red` mutations are required by the Brief (a second env key; `DEVELOPER_DIR` pointed elsewhere) and two more are added for the levels that were previously caught only by the equality net (workflow-level `env:`, step-level `env:`), so each refusal is demonstrated by its own name and not by a path.

  **R6 - PyYAML is NOT guaranteed where a pin on this check would run; the pin would be red in CI on the day it lands.** Checked rather than assumed: `grep -rn "yaml" ops/lib/pins.py .github/workflows/linux-core.yml` shows `pins.py` says in its own docstring `No PyYAML needed` (it ships a deliberately small reader for the flat mappings in `PINS.yaml`), `queue.py` says the same for front matter, and `linux-core.yml` mentions yaml nowhere. `ops/lib/check-ios-compile-guardrails.py` is the ONLY `import yaml` in `ops/`, and it exits 2 - `cannot tell` - when the import fails. The `core` job runs `bash ops/check-pins` inside `swift:6.1-noble` with python from `apt-get install ... python3 python3-pytest`, which does not bring PyYAML; a pin with `anchor: source` also runs there (`--source-only` filters anchors, the full run does not), so the pin would exit 2 and turn `core` red. RULING: do not vendor a YAML parser and do not narrow the pin's `runs_on` to hide the problem. `pins.py`'s own reader cannot parse a workflow (nested mappings, block scalars, lists of mappings are all outside its subset) and a second parser written here would be a check whose expected value is computed by the thing it checks - the defect this repository exists to catch. Instead PyYAML is made to EXIST where the pin runs: `python3-yaml` is added to the `core` toolchain apt line, beside `python3-pytest`, for the reason that comment already gives (a distro package, not `pip`, because Debian's python3 is externally-managed), and `pins-source-only` (ubuntu-latest, whose PyYAML this box cannot verify) gets a step that imports yaml, installs `python3-yaml` only if that import fails, and then PRINTS the version, so the CI log carries the evidence whichever path ran. That adds `.github/workflows/linux-core.yml` to `touches:` - see the next Log line.

  **R7 - the pin id.** `P-OPS-04` and `P-OPS-06` are both absent from `origin/main` (which carries `P-OPS-01`, `-02`, `-03`, `-05`) and from every one of the 30 open PRs' `pins/PINS.yaml` (fetched per head ref with `gh api -H "Accept: application/vnd.github.raw" repos/<owner>/<repo>/contents/pins/PINS.yaml?ref=<branch>`; the highest P-OPS id on any open head is `P-OPS-03`). `git log -S"P-OPS-04" -- pins/PINS.yaml` and `git log -S"P-OPS-06"` are both empty, so neither has ever existed. RULING: take `P-OPS-06`, the next number after the highest id in use, and leave the gap at 04 alone - a reviewer reading `P-OPS-04` would reasonably look for a retired pin, and an id chosen to look tidy is worth less than an id nobody has to research.

  **R8 - the Node 20 notice on `actions/checkout@v4` and `actions/upload-artifact@v4`: change nothing, with the date and the reason.** The notice in run 35391464739 reads, verbatim: `Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/` - printed for `Run actions/checkout@v4`, `keep the log and any Package.resolved` and `Post Run actions/checkout@v4`. RULING, dated 2026-09-18: leave both actions at `@v4`. The runner is ALREADY executing them on Node 24 by its own default, so the notice is informational and nothing here opts into the unsecure fallback; a major bump would have to move `ALLOWED_USES`, `EXPECTED`, the `a third-party action` mutation and `linux-core.yml`'s own `actions/*@v4` uses together, which is a change whose red belongs to its own dispatch and its own task, not to a step that is already changing the toolchain. Recorded, not done.
- 2026-09-18T20:41:48Z **`touches:` widened, deliberately, with the reason.** Added `.github/workflows/linux-core.yml` for R6 (PyYAML where the new pin runs; without it the pin lands red in `core`) and `ops/lib/pins.py` is NOT touched. No other path is added. The hook is not bypassed and `--no-verify` is not used anywhere in this task.
- 2026-09-18T20:41:48Z **STEP 1 - `Package.resolved` committed and the resolution frozen (agent/claude-opus-5, owner).** The runner-produced file from artifact `ios-compile-35391464739` (on this box under `.artifacts/ios-compile/art/`) was copied to `apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` with `cp`; `sha256sum` prints `2c13b9b6788a636eee9026a10c5a31560dcc2ec670be941fbfa50854ef11c44a` for BOTH paths, and the copy holds 0 CR bytes (R1, R2). It records one pin: `maplibre-gl-native-distribution` 6.31.0 at revision `13e41ab3d77ff5113e7e5d4ee87803b1f81f5683`, `"version" : 3`. `-disableAutomaticPackageResolution` was added to the pinned build script in BOTH `.github/workflows/ios-compile.yml` and `EXPECTED`/`BUILD_RUN` in `ops/lib/check-ios-compile-guardrails.py`, in this one commit, because the check compares the whole parsed workflow by equality.

  **RED FIRST, by name.** A copy of the shipped workflow with the new flag deleted (`sed` into `.artifacts/T-0167/one-sided.yml`, outside the tracked tree) - i.e. exactly the one-sided edit this check exists to catch - is refused:

      $ python ops/lib/check-ios-compile-guardrails.py .artifacts/T-0167/one-sided.yml
      IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-build.steps[2].run: differs from the pinned value (compared by equality)
      IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s) gone in one-sided.yml
      exit=1

  The same edit is now a permanent mutation in `--prove-red`, so it can never pass again by accident: `[red rc=1] -disableAutomaticPackageResolution dropped: ... differs from the pinned value (compared by equality)`. Both acceptance commands are green at this commit: `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml equals the pinned workflow: dispatch-only, contents: read, ['macos-15'], time-boxed, and a build that cannot be skipped or fail green` (exit 0) and `PROVE-RED OK: 27 mutations red, 3 legitimate spellings green, 0 unexpected result(s)` (exit 0) - 26 mutations at T-0157's merge plus this one, every one applying exactly once.
- 2026-09-18T20:52:00Z **STEP 1 IS GREEN ON THE RUNNER - run 35393082335, `task/T-0167` at `15eb979`.** Dispatched with `gh workflow run ios-compile.yml --ref task/T-0167`; job `simulator-build`, conclusion `success`. The build line, verbatim from `gh run view 35393082335 --log`:

      simulator-build	build for the iOS Simulator	2026-09-18T20:45:52.2961690Z ** BUILD SUCCEEDED **

  And the whole of the `what the build wrote into the tree` step after its `##[endgroup]` - ONE line, the `find` output, and NOTHING from `git status --porcelain --untracked-files=all`:

      simulator-build	what the build wrote into the tree	2026-09-18T20:45:52.9025830Z apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved

  No `??` line, no `M` line, no line at all from `git status`: the committed file is byte-identical to what a run with `-disableAutomaticPackageResolution` produces, which is what the Brief asked this dispatch to prove. Toolchain on this run was still the image default (`Xcode 16.4`, `Build version 16F6`, `Apple Swift version 6.1.2`) - step 2 is what changes that.

- 2026-09-18T20:52:00Z **STEP 2 - Xcode 26.3 selected by one job-level `DEVELOPER_DIR` (R4, R5).** The same run's toolchain step listed the image's Xcode apps; the 26.x entries it printed are `Xcode_26.0.1.app`, `Xcode_26.0.app`, `Xcode_26.1.1.app`, `Xcode_26.1.app`, `Xcode_26.2.0.app`, `Xcode_26.2.app`, `Xcode_26.3.0.app`, `Xcode_26.3.app`. Newest taken: `env: DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer`, at the JOB level. The build step's first line is now `test -d "$DEVELOPER_DIR" || { echo "ios-compile: $DEVELOPER_DIR is not on this image"; exit 1; }`, so an image that drops 26.3 fails BY NAME before xcodebuild runs instead of quietly compiling against 16.4.

  The check changed in the SAME commit: `JOB_ENV` is pinned by equality inside `EXPECTED`, the blanket job-level `env` refusal is replaced by an equality on that one key, and two refusals that previously existed only as the equality net are now named - a workflow-level `env:` and a step-level `env:`. Five new `--prove-red` mutations, each applying exactly once, each red BY NAME (the fifth by equality, being a run-body edit):

      [red rc=1] a SECOND env key at the job level: IOS-COMPILE-GUARDRAILS: jobs.simulator-build.env: must be exactly {'DEVELOPER_DIR': '/Applications/Xcode_26.3.app/Contents/Developer'} - the plan's iOS 26 SDK, pinned by path; any other key is a way to hand a token to a script, any other value is a silent toolchain change (found {'DEVELOPER_DIR': '/Applications/Xcode_26.3.app/Contents/Developer', 'GH_TOKEN': 'a-token'})
      [red rc=1] DEVELOPER_DIR pointed elsewhere (the image default, 16.4): IOS-COMPILE-GUARDRAILS: jobs.simulator-build.env: must be exactly {...} (found {'DEVELOPER_DIR': '/Applications/Xcode_16.4.app/Contents/Developer'})
      [red rc=1] env: at the WORKFLOW level, inherited by every job: IOS-COMPILE-GUARDRAILS: env: a WORKFLOW-level environment is inherited by every job - the only one allowed is {...} at the job level (found {'DEVELOPER_DIR': '/Applications/Xcode_16.4.app/Contents/Developer'})
      [red rc=1] env: on the build step, overriding the job's toolchain: IOS-COMPILE-GUARDRAILS: jobs.simulator-build.steps[2].env: no step carries its own environment - the one variable this workflow sets is {...} at the job level (found {'DEVELOPER_DIR': '/Applications/Xcode_16.4.app/Contents/Developer'})
      [red rc=1] the DEVELOPER_DIR existence guard deleted (a silent fall back to the image default): IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-build.steps[2].run: differs from the pinned value (compared by equality)

  `PROVE-RED OK: 32 mutations red, 3 legitimate spellings green, 0 unexpected result(s)`, exit 0, and the plain run is `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml equals the pinned workflow: dispatch-only, contents: read, ['macos-15'], time-boxed, one job-level env key (DEVELOPER_DIR=/Applications/Xcode_26.3.app/Contents/Developer), and a build that cannot be skipped or fail green`, exit 0. `wc -l ops/lib/check-ios-compile-guardrails.py` -> 296, under CLAUDE.md's 300-line cap with four lines of margin.
- 2026-09-18T21:05:00Z **STEP 2 IS GREEN ON THE RUNNER, ON XCODE 26.3 - run 35393590488, `task/T-0167` at `6af2c69`.** Job `simulator-build`, conclusion `success`. Verbatim from `gh run view 35393590488 --log`:

      simulator-build	toolchain	2026-09-18T20:50:28.8007660Z   DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer
      simulator-build	toolchain	2026-09-18T20:50:31.3607670Z Xcode 26.3
      simulator-build	toolchain	2026-09-18T20:50:31.3612920Z Build version 17C529
      simulator-build	toolchain	2026-09-18T20:50:35.0116980Z Apple Swift version 6.2.4 (swiftlang-6.2.4.1.4 clang-1700.6.4.2)
      simulator-build	build for the iOS Simulator	2026-09-18T20:51:49.4354030Z ** BUILD SUCCEEDED **

  **Xcode 26's compiler reported NOTHING to fix.** `grep -c " error:"` over the whole downloaded log is `0`; the only `warning:` in the run is the same benign one 16.4 printed: `appintentsmetadataprocessor[20498:60103] warning: Metadata extraction skipped. No AppIntents.framework dependency found.` So no `apps/ios` source change was needed, no path was added to `touches:` for one, and nothing is filed as STILL OPEN under item 2 of the Brief. The guard line ran and passed silently (`test -d "$DEVELOPER_DIR" || { echo ... ; exit 1; }` is echoed in the step's `##[group]` header and printed no message). The status step again printed only the `find` output and nothing from `git status --porcelain --untracked-files=all`, so the committed `Package.resolved` is what Xcode 26.3 resolves to as well - it was NOT rewritten by the newer toolchain. The configuration that is GREEN is therefore the shipped one: Xcode 26.3 by `DEVELOPER_DIR`, `-disableAutomaticPackageResolution`, `Package.resolved` tracked.

- 2026-09-18T21:05:00Z **STEP 3 - the guardrail check is now run by something: P-OPS-06 (R6, R7).** Added to `pins/PINS.yaml`: `anchor: source`, `runs_on: [linux, mac]`, assertion `"${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-ios-compile-guardrails.py`, copied in that exact interpreter-selection spelling from P-GIT-02.

  **SEEN RED BY NAME FIRST, as the pin, not as the script.** `.artifacts/T-0167/pin_red.py` (gitignored) loads `pins/PINS.yaml` with the repository's OWN reader (`ops/lib/pins.py`), points the tracked workflow's `DEVELOPER_DIR` at the image default, and runs the assertion string exactly as `PINS.yaml` spells it:

      --- P-OPS-06 assertion on the mutated workflow: exit 0 = False
      IOS-COMPILE-GUARDRAILS: jobs.simulator-build.env: must be exactly {'DEVELOPER_DIR': '/Applications/Xcode_26.3.app/Contents/Developer'} - the plan's iOS 26 SDK, pinned by path; any other key is a way to hand a token to a script, any other value is a silent toolchain change (found {'DEVELOPER_DIR': '/Applications/Xcode_16.4.app/Contents/Developer'})
      IOS-COMPILE-GUARDRAILS FAIL: 1 guardrail(s) gone in ios-compile.yml
      --- restored: git status --short on that path:
      (empty)
      --- byte-identical to before the mutation: True
      --- P-OPS-06 assertion on the restored workflow: exit 0 = True

  The mutation is reverted in a `finally` with `git checkout --`, and the restoration is printed rather than asserted. The repo's own parser reads the new entry: `parsed 24 pins, ids unique: True`.

  **PyYAML, per R6.** `.github/workflows/linux-core.yml` now installs `python3-yaml` beside `python3-pytest` in the `core` container's apt line and prints its version in the same `&&` chain that already prints git, python and pytest; `pins-source-only` (ubuntu-latest, an image this repository does not control) tries the import, installs the distro package only if that fails, and prints the version either way, so the run log records which path ran. **NOT RUN HERE, and it must be read in CI rather than believed from this Log:** neither job runs on this Windows box. The local evidence is only that `python -c "import yaml"` works on this box (`PyYAML 6.0.3`, Python 3.10.11) and that the assertion exits 0 through `ops/lib/pins.py`'s own runner; whether `pins-source-only` took the install branch or the already-present branch is a fact only its log can state.

- 2026-09-18T21:05:00Z **STEP 4 - the Node 20 notice: recorded, nothing changed (R8).** Dated 2026-09-18. Both `actions/checkout@v4` and `actions/upload-artifact@v4` print it, and its own text says the runner is ALREADY on Node 24 (`This workflow is running with Node 24 by default`), so there is nothing to opt into and nothing degraded today. A major bump would have to move `ALLOWED_USES`, `EXPECTED`, the `a third-party action` mutation and `linux-core.yml`'s four `actions/*@v4` uses in one commit, and its red belongs to its own dispatch; filed here as STILL OPEN rather than smuggled into a toolchain change.
- 2026-09-18T21:12:00Z **FINAL COMMIT - acceptance block re-run and quoted in full above (agent/claude-opus-5, owner).** Every line of `acceptance:` was executed again at this tree state before this commit; the only thing this commit changes is this task file, so the workflow that run 35394086754 built at `d9a09d3` is the shipped one. That run: conclusion `success`, `Xcode 26.3` / `Build version 17C529` / `Apple Swift version 6.2.4`, `** BUILD SUCCEEDED **`, `grep -c ' error:'` over the whole log `0`, and the status step silent from `git status --porcelain --untracked-files=all`. Three dispatches, one per step, so a red would have been attributable: 35393082335 (Package.resolved + the flag), 35393590488 (Xcode 26.3 + the guard line), 35394086754 (the shipped tree). None was red, which is why this Log has no compiler errors to quote - and the red that makes the dispatch trustworthy is T-0157's, run 35391738972, not re-run here.

  **STILL OPEN.**
  1. The Node 20 notice on `actions/checkout@v4` and `actions/upload-artifact@v4` (R8): recorded, dated 2026-09-18, deliberately unchanged. A major bump moves `ALLOWED_USES`, `EXPECTED`, the `a third-party action` mutation and `linux-core.yml`'s four `actions/*@v4` uses together and needs its own dispatch.
  2. `P-OPS-06` is `anchor: source`, so it runs in BOTH linux-core jobs. Whether `pins-source-only`'s image already carries PyYAML or takes the apt branch this task added is unknown here and is a fact only that job's log states; if the fallback branch ever runs, its apt path has never been exercised.
  3. The check pins what the workflow SAYS. GitHub's own behaviour is out of its reach (T-0157's reviewers recorded two mutants that pass the check and are rejected by GitHub's parser instead); the dispatch remains the only proof the job compiles anything.
  4. Untouched by this task and unchanged: signing, TestFlight, the plan's push-to-phone gate (T-0009, the human). This tree has never been on a device, and nothing here changes that.
  5. `ops/lib/check-ios-compile-guardrails.py` is at 296 lines against a 300-line cap; the next edit to it should budget for that.
- 2026-09-18T21:57:33Z **Record corrections from the read-only verification, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier reproduced the three runs on their shas (35394086754 on d9a09d3:
  Xcode 26.3, Build version 17C529, ** BUILD SUCCEEDED **, 0 ' error:', DEVELOPER_DIR at job level, the status
  step silent), the guardrail check and its --prove-red in this worktree (32 mutations red, 3 spellings green),
  P-OPS-06 as the 24th pin with no duplicate id, and the clean tree; these are text.** (a) R7's "P-OPS-04 and
  P-OPS-06 are both absent from every one of the 30 open PRs' pins/PINS.yaml" quotes no output; what is
  re-derivable is that origin/main carries P-OPS-01/02/03/05 and this branch adds P-OPS-06 without a duplicate.
  (b) The pin-as-pin red run (`.artifacts/T-0167/pin_red.py`) and STEP 1's `one-sided.yml` are quoted in the
  Log but neither file survives under `.artifacts/T-0167/`, so that red cannot be re-executed from an artifact;
  the script-level reds (--prove-red's "DEVELOPER_DIR pointed elsewhere" and the
  `-disableAutomaticPackageResolution` mutation) are reproducible and were reproduced. (c) `grep -c ' error:'
  = 0` for run 35393590488 (step 2) was not re-fetched; it holds for the final run. (d) Whether
  `pins-source-only` took the PyYAML install branch: run 35394513701's step ran and the core container printed
  `PyYAML 6.0.1`, still not that job's own line, so STILL OPEN item 2 stands as written.
- 2026-09-18T22:05:58Z **REVIEW PASS - agent/rv1-pr97 (reviewer; not the owner `agent/claude-opus-5`, not the
  orchestrator `agent/claude-fable-5-1` who wrote the correction entry above). PR #97 at head `76aea33`.** Read in a
  detached worktree `.worktrees/rv1-pr97` (removed after this entry): the PR body, this file end to end including
  both correction entries and STILL OPEN, and `git diff origin/main...HEAD` (6 files, +194/-9). Nothing in the PR
  was changed.

  **Acceptance re-run at this head, not read.** `python ops/lib/check-ios-compile-guardrails.py` printed the OK
  line the block quotes, word for word, exit 0. `--prove-red` printed
  `PROVE-RED OK: 32 mutations red, 3 legitimate spellings green, 0 unexpected result(s)`, exit 0 - 32 `[red rc=1]`,
  4 `[green rc=0]` (the 3 legitimate spellings plus the shipped file), 1 `[refused rc=2] unreadable YAML: ...
  ParserError`. `cmp` between
  `.artifacts/ios-compile/art/ios-compile-35391464739/apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`
  and the committed copy: identical, `sha256sum` prints
  `2c13b9b6788a636eee9026a10c5a31560dcc2ec670be941fbfa50854ef11c44a` for both, and `tr -dc '\r' | wc -c` is `0`.
  `git check-ignore -v <that path>` printed nothing, exit 1. `wc -l ops/lib/check-ios-compile-guardrails.py` -> 296.
  The three dispatches by `gh run view <id> --json headSha,conclusion`: 35393082335 / `15eb979`, 35393590488 /
  `6af2c69`, 35394086754 / `d9a09d3`, each `success` on `task/T-0167`. The final run's log: one
  `** BUILD SUCCEEDED **`, `grep -c ' error:'` = `0`, `DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer`,
  `Xcode 26.3`, `Build version 17C529`, `Apple Swift version 6.2.4`, and the `what the build wrote into the tree`
  step printing exactly ONE line after its `##[endgroup]` - the `find` output - and nothing from `git status
  --porcelain --untracked-files=all`. `git diff --name-only d9a09d3..HEAD` lists only this task file, so the tree
  that run built is the shipped one.

  **Two of the arithmetics redone rather than believed.** (1) 32 = 26 + 1 + 5: `origin/main`'s `MUTATIONS` table
  holds 26 top-level tuples, this head holds 32, the six new ones being `-disableAutomaticPackageResolution
  dropped` plus the five env/guard mutations - and 32 is also the count of `[red rc=1]` lines, so no mutation is
  a no-op. (2) 296 = 270 + 29 - 3: `origin/main`'s copy of the check is 270 lines and `git diff --numstat
  origin/main...HEAD` prints `29 3` for it; four lines under CLAUDE.md's 300 cap. Also 23 `^- id:` on main + 1 =
  24, confirmed through the repository's OWN reader: `ops/lib/pins.py`'s `load()` gives `parsed pins: 24 | ids
  unique: True`, with `P-OPS-06` at `anchor=source runs_on=['linux', 'mac']` and no `TODO` in the assertion.

  **Four mutations of the reviewer's own, each applied ALONE to a copy of the shipped workflow, control green.**
  None of them is in the author's table. (i) `DEVELOPER_DIR` at **Xcode_26.0** - still "Xcode 26", so a check that
  only grepped for the major would pass it - refused `rc=1`: `jobs.simulator-build.env: must be exactly {...}
  (found {'DEVELOPER_DIR': '/Applications/Xcode_26.0.app/Contents/Developer'})`. (ii) step-level `env:` on the
  **toolchain** step rather than the build step, i.e. a log that would print 16.4 while the build used 26.3 -
  `jobs.simulator-build.steps[1].env: no step carries its own environment ...`, `rc=1`. (iii) a second job-level
  key that changes the SDK instead of handing over a token, `SDKROOT: iphonesimulator16.4` -> `... (found
  {'DEVELOPER_DIR': ..., 'SDKROOT': 'iphonesimulator16.4'})`, `rc=1`. (iv) the whole job-level `env:` block
  deleted, leaving `DEVELOPER_DIR` unset -> `... (found None)`, `rc=1`. Control, the shipped file, `rc=0`.
  **The pin AS the pin was reproduced too**, because correction entry (b) records that the author's `pin_red.py`
  does not survive: the assertion string exactly as `pins/PINS.yaml` spells it, run against the TRACKED workflow
  with `DEVELOPER_DIR` pointed at 16.4, exits 1 with the same named failure; `git checkout --` restores it and the
  assertion exits 0 again with `git status --short` clean on that path.

  **The product question.** M1.5's exit is the phone and the tap into Apple Maps on Skyline. The wrong value in
  this PR's reach is a toolchain or a package resolution, and both now fail loudly instead of green: a workflow
  that would build against the image's 16.4 default is refused BY NAME before it ever reaches a runner, and on the
  runner `test -d "$DEVELOPER_DIR"` fails by name before `xcodebuild` starts; a resolution that drifts from the
  committed `Package.resolved` fails the build rather than being rewritten in place. No claim here is that
  anything rendered - this tree has still never been on a device, which the PR and STILL OPEN #4 state plainly.

  **Rulings.** R1-R8 stand; the reviewer disagrees with none of them. R4 is the plan's platform row verbatim
  (`Xcode 26 / iOS 26 SDK mandatory since 2026-04-28`), and pinning by exact path rather than a glob is precisely
  what makes a missing 26.3 visible instead of a silent 16.4. R6's widening of `touches:` to `linux-core.yml` is
  the honest move; narrowing the pin's `runs_on` to hide an exit 2 would have been the dishonest one.

  **Recordable, none blocking.** (a) `TOOLCHAIN_RUN ="..."` lost the space before the quote in this diff; the value
  is unchanged and no linter runs over `ops/` (grepping `flake8|ruff|pycodestyle|pylint|black` across `ops/`,
  `.github/workflows/` and `services/etl/` finds nothing), so it is cosmetic. (b) The new docstring parenthetical
  is inserted between `(good messages),` and `and then it compares`, splitting that sentence in half. (c)
  `pins_affected: []` although this task adds `P-OPS-06`; `grep -rn pins_affected ops/ .githooks/` finds only
  fixtures, so nothing enforces the field and it is informational drift, not a gate. (d) STILL OPEN #2 is now half
  answered: on run 35399355056, head `76aea33`, the `pins-source-only` job printed `PyYAML 6.0.1` 0.065s after its
  `##[endgroup]` with no apt output at all, so the import branch ran and the apt fallback has still never been
  exercised. (e) A follow-up, not a blocker under the two-round harness rule: the check reads only
  `.github/workflows/ios-compile.yml`, so a SECOND macOS workflow file added beside it is outside its reach; it
  cannot make this build fail green.

  **CI at this head, read once.** `gh pr checks 97` -> `core pass`, `pins-source-only pass`, and
  `gh run view 35399355056 --json headSha,conclusion` -> `76aea334828c629d261c27a8e1aecb3c8ae6c6a7`, `success`.
  NOT run by this review, on the record: `bash ops/check-pins`, `bash ops/test`, and any `ios-compile` dispatch
  (it bills a macOS runner; the existing three runs were read instead). `state: claimed` -> `state: done`,
  `reviewer: agent/rv1-pr97`, `queue/claimed/` -> `queue/done/`. Not merged - that is the merge step's own gate.
- 2026-09-18T22:19:29Z **Sign-off applied for the reviewer by agent/claude-fable-5-1 (orchestrator; not the owner, not the reviewer).**
  agent/rv1-pr97 returned PASS at 76aea33 (entry above, verbatim) but was PASS-BLOCKED: `bash ops/queue-check` on
  the prepared transition printed `queue/LOCKS/package-resolved.lock held by T-0167, which is not in claimed/`,
  and `queue/LOCKS/` is outside this task's `touches:`, so the reviewer reverted and committed nothing. This
  commit is that transition: `state: done`, `reviewer: agent/rv1-pr97`, the file moved to queue/done/, and
  `queue/LOCKS/package-resolved.lock` (`T-0167 agent/claude-opus-5 2026-09-18T20:32:58Z`) removed in the SAME
  commit - the plan's rule that LOCKS/ travels with the transition. `queue/LOCKS/` is added to `touches:` for
  that one path. No code, no workflow and no earlier entry changed. The gap - no `queue.py done` and no
  lock-releasing PASS transition - is T-0095's scope, already filed.
- 2026-09-18T22:27:52Z **After the sign-off, before the merge - agent/claude-fable-5-1 (orchestrator).** PRs #96 (T-0151) and #95
  (T-0152) landed on main after agent/rv1-pr97's PASS at 76aea33, and both change apps/ios; so `origin/main`
  (886a822) was merged into this branch as 7627565 (a merge, no rebase; no conflicts; nothing of this task's own
  changed) and `ios-compile` was dispatched once more on that tree: run 35401463617, headSha 7627565,
  conclusion `success`, toolchain line `Xcode 26.3`, `** BUILD SUCCEEDED **` once in the log, `grep -c ' error:'`
  -> 0, and `SkylineRoute.swift` appears in the compile log - the first build of the whole M1.5 tree under the
  iOS 26 SDK. Nothing has rendered it. This entry and the merge commit are the only changes after the PASS.
