---
id: T-0167
title: ios-compile follow-up - commit Package.resolved, build with Xcode 26 (the plan's SDK), and pin the guardrail check
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:58Z
lease_expires_at: 2026-09-19T04:32:58Z
worktree: .worktrees/T-0167
branch: task/T-0167
exclusive: [package-resolved]
touches: [.github/workflows/ios-compile.yml, .github/workflows/linux-core.yml, ops/lib/check-ios-compile-guardrails.py, apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0157]
verify: [ops/check-pins]
acceptance: []
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
