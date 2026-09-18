---
id: T-0157
title: ios-compile - a workflow_dispatch-only macOS simulator build of apps/ios, seen red then green, so the Apple tree is compiled by something before the human's Xcode Cloud step
state: claimed
owner: agent/claude-fable-5-1
owner_session: null
claimed_at: 2026-09-18T18:54:23Z
lease_expires_at: 2026-09-19T00:54:23Z
worktree: .worktrees/T-0157
branch: task/T-0157
exclusive: []
touches: [.github/workflows/ios-compile.yml, ops/lib/check-ios-compile-guardrails.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "python ops/lib/check-ios-compile-guardrails.py -> IOS-COMPILE-GUARDRAILS OK: ios-compile.yml equals the pinned workflow: dispatch-only, contents: read, ['macos-15'], time-boxed, and a build that cannot be skipped or fail green, exit 0"
  - "python ops/lib/check-ios-compile-guardrails.py --prove-red -> one '[red rc=1]' line per mutation naming what was removed and where (a named guardrail, or the first path at which the parsed workflow differs from the pinned structure), a '[green rc=0]' line for each legitimate spelling that must not be refused, '[refused rc=2] unreadable YAML', '[green rc=0] the shipped file', then PROVE-RED OK: 26 mutations red, 3 legitimate spellings green, 0 unexpected result(s), exit 0"
  - "bash ops/check-pins --source-only -> PINS ok=9 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only, exit 0"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 56 Swift files tracked (Sources=20, Tests=28, apps/ios=8), none over 300 lines, exit 0"
  - "bash ops/lib/check-pipe-consumers -> PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (54 scanned, 55 tracked, floor 42), exit 0"
  - "bash ops/queue-check -> QUEUE OK (152 tasks), exit 0"
  - "NOT RUN, on the record: the workflow itself. GitHub only offers workflow_dispatch for a file that exists on the default branch, so the first dispatch happens AFTER this PR merges; its red-then-green is recorded by the follow-up task filed at merge, not claimed here"
---
## Brief

Filed from the 2026-09-18 12:13 panel (STRATEGY lens, grounded; three of its guardrails corrected by the
grounding pass). `apps/ios` reached main in PR #88 and has NEVER been compiled: the only planned compiler is
Xcode Cloud, behind the human's App Store Connect step (T-0009). Three filed tasks (T-0151 waypoints, T-0152
copy, T-0153 disclaimer) all edit that tree. The plan's Mac-CI row (plan :65) lists "GitHub macOS runners"
as given up, but its stated reason is "a cloud Mac can't attach a phone" - device iteration, not compilation.
A dispatch-only compile job fills the gap that row leaves; it does not overturn it.

**Do:** `.github/workflows/ios-compile.yml`, its OWN file (never a job in `linux-core.yml`, whose `on:` is
push + pull_request):

- `on: workflow_dispatch:` ONLY - no push, no pull_request, no schedule. Never a required check: Linux CI
  stays the fleet's gate.
- `permissions: contents: read`; `defaults: run: shell: bash` (the repo's pipefail convention; gates bare).
- `runs-on: macos-15` - the standard label only, pinned (not `macos-latest`), never `-large`/`-xlarge`
  (larger runners always bill). `timeout-minutes: 20` on the job: a hung xcodebuild must not run for hours.
- Steps: checkout; print `xcodebuild -version` and `swift --version`; then
  `xcodebuild -project apps/ios/ScenicDrive.xcodeproj -scheme ScenicDrive -destination 'generic/platform=iOS Simulator' -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" CODE_SIGNING_ALLOWED=NO build`
  (CLAUDE.md requires `-derivedDataPath` under the worktree; `DerivedData/` is already ignored at
  `.gitignore:12`). Tee the log to a file and upload it as an artifact on success AND failure.
- Last step: `git status --porcelain --untracked-files=all` printed (NOT `git diff --exit-code`, which cannot
  see an untracked file and so can never go red), and upload `Package.resolved` as an artifact if xcodebuild
  wrote one. No commit step, no push step. Committing `Package.resolved` is a follow-up under `exclusive:`
  (it is a serial-only file), filed only after the first green run, together with
  `-disableAutomaticPackageResolution`.

**Red then green, in the Log.** A workflow_dispatch workflow can only be dispatched once its file is on the
default branch, so: PR the file, review it (it is ~40 lines), merge, then `gh workflow run ios-compile.yml`
and read the run. The FIRST run is expected to be red for real reasons - nobody has compiled this tree -
and that red IS the deliverable's first half: paste the first compiler errors into the Log and file the
fixes as their own task(s) against `apps/ios/`. Green is a run that ends `** BUILD SUCCEEDED **`.

**What it does not prove:** signing, TestFlight, the plan's <=40 min push-to-phone gate (plan :281) - all
still T-0009 and the human. The panel also recorded that `gh repo view` reports this repository as PUBLIC
while plan :280 says "private repo"; standard runners on a public repository are not metered, which is why
the cost argument against this job falls - and the visibility itself is the human's to confirm.

## Log
- 2026-09-18T19:05:00Z filed by agent/claude-fable-5-1 from the 12:13 panel's grounded synthesis. Not started.
- 2026-09-18T18:54:23Z claimed by agent/claude-fable-5-1; lease until 2026-09-19T00:54:23Z
- 2026-09-18T19:07:14Z **Authored - agent/claude-fable-5-1 (owner).** `.github/workflows/ios-compile.yml`: its own file;
  `on: workflow_dispatch` only; `permissions: contents: read`; `defaults.run.shell: bash`; one job on the
  pinned standard label `macos-15` with `timeout-minutes: 20`; `xcodebuild ... -destination
  'generic/platform=iOS Simulator' -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" CODE_SIGNING_ALLOWED=NO
  build`, tee'd to a log; then, `if: always()`, `git status --porcelain --untracked-files=all` and an upload of
  the log and any `Package.resolved`. No commit step, no push step, not a required check.

  **The guardrails are data, and checked.** `ops/lib/check-ios-compile-guardrails.py` parses the workflow as
  YAML and refuses by the NAME of whichever guardrail is gone - anchored on keys, never on a comment. It is
  outside this task's original `touches:`; added there in this commit because a dispatch-only macOS job that
  quietly gains a `push:` trigger is the failure this task has to make impossible to miss. `--prove-red`
  ships with it: seven mutations, one per guardrail, each applied ALONE to a copy outside the tree, each
  required to apply exactly once (a stale anchor REFUSES rather than proving a no-op), plus an unreadable
  file that must exit 2, not 0. Output at this commit: `PROVE-RED OK: 7 guardrails mutated, 0 unexpected result(s)`.

  **What this PR cannot show.** The workflow has never run: `workflow_dispatch` needs the file on the default
  branch. The first dispatch is expected RED for real reasons - nobody has compiled `apps/ios` - and that
  red, the fixes, and the first `** BUILD SUCCEEDED **` belong to the follow-up filed at merge. Also not
  decided here: which Xcode the `macos-15` image selects by default (the job prints it) and whether the
  plan's "Xcode 26 / iOS 26 SDK" needs an explicit `xcode-select`; the first run's toolchain step answers it.

  **STILL OPEN.** The guardrail check is an acceptance command, not a pin: `pins/PINS.yaml` is outside
  touches and two open PRs are already contending for the next P-OPS id. Pin it with the follow-up.
  `Package.resolved` for the Apple package is still uncommitted (a serial-only file; its own `exclusive:`
  task after the first green run, with `-disableAutomaticPackageResolution`).
- 2026-09-18T19:18:23Z **Review FAIL - agent/rv1-pr90 (reviewer, not the owner).** PR #90 read at b736d05 in `.worktrees/rv1-pr90` (tip == `origin/task/T-0157`); nothing written in `.worktrees/T-0157`. Both acceptance lines for the check reproduce verbatim: `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml is dispatch-only, read-only, time-boxed, on ['macos-15']` (exit 0) and seven `[red rc=1]` lines + `[refused rc=2] unreadable YAML` + `[green rc=0] the shipped file` + `PROVE-RED OK: 7 guardrails mutated, 0 unexpected result(s)` (exit 0). The shipped workflow is right on every item checked: `on:` exactly `workflow_dispatch` (no push/pull_request/schedule, and `workflow_call` would itself be refused, so no reusable back door), `contents: read`, `macos-15`, `timeout-minutes: 20`, the `-project`/`-scheme ScenicDrive` pair matches the only shared scheme, `-derivedDataPath "$GITHUB_WORKSPACE/DerivedData"` (gitignored at .gitignore:12), `CODE_SIGNING_ALLOWED=NO`; under `shell: bash` (`-e -o pipefail`) the tee'd xcodebuild fails the step, and the `if: always()` steps cannot mask it (`always()` forces the step to run, it does not change the job conclusion).
  **BLOCKING, from ten mutations applied one at a time to copies outside the tree; three PASS the check.** (1) a job-level `permissions: write-all` inserted above `runs-on: macos-15` -> `IOS-COMPILE-GUARDRAILS OK: ... read-only ...` exit 0: job-level permissions replace the workflow-level map, so the check certifies "read-only" over a write token, and `FORBIDDEN_IN_RUN` only greps `run:` strings, never a `uses:` step or `gh api -X PUT`. --prove-red's "permissions widened" mutation edits the top-level key only. (2) a step-level `shell: sh`, and separately `continue-on-error: true`, on the xcodebuild step -> exit 0 both times: `shell:` on a step overrides `defaults.run.shell`, `sh -e` has no pipefail, so `xcodebuild | tee` reports tee's 0 and a failed build is a green step - precisely the sentence the check prints when it refuses ("or a failed build piped into tee reports success"). `problems()` reads workflow-level `permissions` and `defaults.run.shell` and never looks inside a job or a step.
  **RECORDABLE.** `on: workflow_dispatch` as a bare string (a legitimate dispatch-only spelling) is refused with `found 'workflow_dispatch'`; `runs-on: [macos-15]` crashes with `TypeError: unhashable type: 'list'` and exits 1 where the docstring reserves 2 for "cannot tell"; `timeout-minutes: true` would pass the integer range test; the artifact's mixed absolute/relative `path:` makes upload-artifact@v4 root the zip at `/Users/runner/work`. Stated in the record and therefore not findings: the check is an acceptance command, not a pin nor wired into CI, and the workflow has never run.
  **Not re-run here:** `ops/check-pins --source-only` locally (the single backgrounded run was still driving a swift build into `.build/` after 8 minutes and never printed; not killed - other agents share this box). CI at this head is the evidence instead: `gh pr checks 90` -> `core pass`, `pins-source-only pass`.
- 2026-09-18T19:33:26Z **ROUND 2 - agent/claude-fable-5-1 (owner), answering agent/rv1-pr90's FAIL above (verbatim).** Two blocking,
  both reproduced with the reviewer's exact mutants before anything changed, both the same mistake: the check
  read each guardrail at the WORKFLOW level only, and GitHub Actions lets a job or a step override every one.

  **BLOCKING 1 - a job-level `permissions:` block REPLACES the workflow-level one.** `permissions: write-all`
  under `jobs.simulator-build` passed, while the check's own OK line said "read-only". Now any job-level
  `permissions` key is refused by name; `uses:` is an ALLOWLIST (`actions/checkout@v4`,
  `actions/upload-artifact@v4`), because a third-party action is code this check cannot read; and `gh api`
  joined the forbidden run strings.
  **BLOCKING 2 - the pipefail guardrail did not survive a step-level key.** `shell: sh` on the build step, or
  `continue-on-error: true` on the step or the job, passed - and either turns `** BUILD FAILED **` into a green
  job, in a workflow whose first run is EXPECTED to be red. Now refused at every level: a job-level `defaults`,
  a step `shell` other than bash, `continue-on-error` on a step or a job.

  **Recordables, taken.** `on:` is normalised across its three legal shapes (string, list, mapping), so
  `on: workflow_dispatch` as a bare string is green and `on: [workflow_dispatch, push]` is red for the right
  reason; `runs-on: [macos-15]` is green instead of a TypeError, and any shape this check cannot judge is exit
  2 ("cannot tell"), never a traceback that reads as a verdict; `timeout-minutes: true` is refused (a bool is
  an int in Python); the log is tee'd under `DerivedData/` so the artifact has one workspace-relative root.
  NOT taken: wiring the check to a pin or to CI - still STILL OPEN below, for the reason given in round 1.

  **`--prove-red` now carries the reviewer's mutants and the legitimate spellings.** Every guardrail is mutated
  at every level it can be overridden at, each ALONE, each required to apply exactly once; the two legitimate
  spellings must stay GREEN - a check that refuses them teaches people to stop running it. At this commit:
  `PROVE-RED OK: 14 mutations red, 2 legitimate spellings green, 0 unexpected result(s)`.

  **STILL OPEN, unchanged:** the workflow has never run (dispatch needs the file on the default branch); the
  check is an acceptance command, not a pin; `Package.resolved` is uncommitted.
- 2026-09-18T19:38:36Z **Review FAIL (round 2) - agent/rv2-pr90 (reviewer, neither the owner nor the round-1 reviewer).** PR #90 read at e3c7345 in a detached `.worktrees/rv2-pr90` (== `origin/task/T-0157`), removed at the end; nothing written in `.worktrees/T-0157`. Both check acceptance lines reproduce verbatim: `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml is dispatch-only, read-only at every level, time-boxed, on ['macos-15']` (exit 0) and 14 `[red rc=1]` lines naming guardrail+level, 2 `[green rc=0]` legitimate spellings, `[refused rc=2] unreadable YAML`, `[green rc=0] the shipped file`, `PROVE-RED OK: 14 mutations red, 2 legitimate spellings green, 0 unexpected result(s)` (exit 0). Round 1's three mutants, re-applied by hand from the shipped text (not --prove-red's copies), are each refused BY NAME at their level: `jobs.simulator-build.permissions` (write-all), `jobs.simulator-build.steps[2].shell` ('sh'), `jobs.simulator-build.steps[2].continue-on-error`. Its recordables are closed too (bare-string `on:` green, `runs-on: [macos-15]` green, `timeout-minutes: true` refused, unjudgeable shapes exit 2, artifact path one workspace-relative root). By reading: `-project` exists, `-scheme ScenicDrive` == the only shared scheme `ScenicDrive.xcscheme`, generic simulator destination, `-derivedDataPath` under `$GITHUB_WORKSPACE` (`DerivedData/` ignored at .gitignore:12), `CODE_SIGNING_ALLOWED=NO`, `mkdir -p` before the tee, both `if: always()` steps cannot clear a failed job's conclusion, both `uses:` in the allowlist, no commit/push step.
  **BLOCKING, from six mutations nobody had written, applied one at a time to copies outside the tree; one breaks a guardrail and passes.** `set +o pipefail` prepended to the build step's run body (defaults untouched, no step `shell:`, no `continue-on-error`) -> exit 0, `IOS-COMPILE-GUARDRAILS OK: ... read-only at every level ...`. `shell: bash` is `bash --noprofile --norc -e -o pipefail {0}`, and `-o pipefail` is only the INITIAL state: demonstrated with a stub returning 65 through `| tee`, the shipped body exits 65 and the same body under `set +o pipefail` exits 0, so `** BUILD FAILED **` becomes a green job - the exact failure the check's own refusal text and the workflow's lines 26-27 name. Round 2 asserted the shell guardrail at the workflow, job (`defaults`) and step (`shell:`) levels but not in the run body, which is the level closest to the pipe; this is round 1's class, not a new one, and needs no new mechanism - `FORBIDDEN_IN_RUN` (which gained `gh api` this round) is where `set +o pipefail`, `set +e`, `|| true` and `; exit 0` belong, keyed to the step running xcodebuild. Only `set +o pipefail` was executed; note `set +e` alone would NOT mask it here, the pipeline being the body's last command.
  **RECORDABLE.** `env: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` plus `curl -X PUT -H "Authorization: Bearer $GH_TOKEN" https://api.github.com/repos/o/r/contents/x` passes - `api.github.com`/`curl` are not in the forbidden strings - but `permissions: contents: read` makes that PUT a 403 and every widening key is refused by name, so the read-only-token guardrail holds: a door the token scope already closes. Refused, for the record: job `permissions` as a mapping `{contents: write}`; a second clean `ubuntu-latest` job (every job-level guardrail applies to every job); `runs-on: ${{ matrix.os }}` with a matrix including `-xlarge` (by the unresolved literal, exit 1 not 2); `workflow_call:` beside `workflow_dispatch`. `ops/lib/check-ios-compile-guardrails.py` at 100644 is NOT a finding: every `.py` under `ops/lib/` is 100644 and every extensionless script 100755, and it is invoked as `python ops/lib/...`.
  **Not re-run here:** `bash ops/check-pins --source-only` locally - it drives a swift build into the default `.build/` and cost the round-1 reviewer 8+ minutes on a shared box. CI at this head is the evidence: `gh pr checks 90` (once, no polling) -> `core pass 2m21s`, `pins-source-only pass 1m37s`.
- 2026-09-18T19:47:06Z **ROUND 3 - agent/claude-fable-5-1 (owner), answering agent/rv2-pr90's FAIL above (verbatim).** One blocking,
  reproduced first: `set +o pipefail` prepended to the build step's run body passed the round-2 check, and the
  reviewer showed with a stub that under `bash -e -o pipefail` the shipped pipeline exits 65 on a failed build
  while the mutated one exits 0 - a green job over `** BUILD FAILED **`. Round 2's docstring said "every level"
  and had not looked inside the script, the level closest to the pipe it protects.

  **The fix is structural, not another substring.** Hunting `set +o pipefail`, `set +e`, `|| true`, `|| :`, a
  subshell, a trap... is the arms race PR #87 spent four rounds on. The check no longer scans run bodies: it
  holds the ONLY three scripts this job may run as literals (`EXPECTED_RUN`, keyed by step name) and compares
  each `run:` BY EQUALITY; a run step whose name is not pinned is refused; exactly one step may carry the build
  step's name. Changing what this job runs now means changing the check, deliberately, under review - which
  is the right cost for a job on a macOS runner.

  **Recordables, taken by name:** a job-level `strategy:` (the reviewer's matrix was refused only because the
  unresolved expression failed the label set); `env:` at workflow, job or step level; any `secrets.` reference
  in the file (a personal token would sit outside the read-only GITHUB_TOKEN, and nothing here needs one);
  `workflow_call` beside `workflow_dispatch` joined `--prove-red`. The reviewer's M5 (`curl` at the API with a
  handed-in token) is now red twice over - by `env:`/`secrets.` and by the script equality.

  **Measured at this commit:** `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml is dispatch-only, read-only, time-boxed, on ['macos-15'], and runs only its 3 pinned scripts`; `PROVE-RED OK: 20 mutations red, 2 legitimate spellings green, 0 unexpected result(s)`.

  **STILL OPEN, unchanged:** the workflow has never run; the check is an acceptance command, not a pin;
  `Package.resolved` is uncommitted. NEW, stated: the three pinned scripts live in two places (the workflow
  and the check) on purpose; an edit to one without the other is a red check, not a silent drift.
- 2026-09-18T19:54:30Z **Review FAIL (round 3) - agent/rv3-pr90 (reviewer, neither the owner nor the round-1 or round-2 reviewer).** PR #90 read at `d7537f9` in a detached `.worktrees/rv3-pr90` (== `origin/task/T-0157`), removed at the end with `git status --short` empty; nothing written in `.worktrees/T-0157` (clean, at `d7537f9`). Both check acceptance lines reproduce verbatim at the head of the output: `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml is dispatch-only, read-only, time-boxed, on ['macos-15'], and runs only its 3 pinned scripts` (exit 0), and 20 `[red rc=1]` lines each naming the guardrail and its level (workflow / job / step / the run body by equality), 2 `[green rc=0]` legitimate spellings, `[refused rc=2] unreadable YAML`, `[green rc=0] the shipped file`, `PROVE-RED OK: 20 mutations red, 2 legitimate spellings green, 0 unexpected result(s)` (exit 0); every mutation applies exactly once, so none proves over a no-op. Round 2's mutant re-applied by hand from the shipped text - `set +o pipefail` above `mkdir` in the build body, defaults untouched - is refused BY NAME as a script difference: `jobs.simulator-build.steps[2].run: the script of 'build for the iOS Simulator' differs from the text pinned in this check (compared by equality)`. By reading: `on:` exactly `workflow_dispatch`, `contents: read` with no job-level block, `defaults.run.shell: bash`, `macos-15` pinned, `timeout-minutes: 20`, `-derivedDataPath "$GITHUB_WORKSPACE/DerivedData"` (ignored at .gitignore:12), `CODE_SIGNING_ALLOWED=NO`, both `uses:` allowlisted, no commit/push step, and all three block scalars byte-equal to their `EXPECTED_RUN` literals.
  **BLOCKING, from five mutations nobody had written plus one extra probe, each applied ALONE to a copy outside the repo; three pass, one of them over a broken guardrail.** `if: false` on the build step -> exit 0, `IOS-COMPILE-GUARDRAILS OK: ... and runs only its 3 pinned scripts`. `problems()` never reads a step's `if:` (no `s.get("if")` in the file), while `if:` is legitimately in use in the shipped workflow (`if: always()` on the last two steps). In GitHub's semantics the step is SKIPPED, a skipped step does not fail a job, the two `if: always()` steps still succeed - so the dispatch ends `success` with no `xcodebuild` invocation and neither `** BUILD FAILED **` nor `** BUILD SUCCEEDED **` in the log: a GREEN job that compiled nothing, certified by a check whose OK line asserts three pinned scripts over one that never ran. The guardrail this file exists for - a failed OR ABSENT build fails the job - is asserted against a failed build (step/job `continue-on-error`, step `shell:`, `defaults`, `set +o pipefail`, `|| true`) and against a deleted build step (`count(BUILD_STEP) != 1`), but not against a present, byte-identical, never-executed one. The plausible spelling is not `if: false` but a condition that reads legitimate and is never true here (`if: github.event_name == 'push'`); only `if: false` was executed, both take the identical no-`if`-handling path. Same class as rounds 1-2 - a guardrail asserted at every level except the one closest to what it protects - now the step condition rather than the run body; equality over the script cannot see it, the script being untouched. It matters most because the FIRST dispatch is expected RED for real reasons: a green first run would be read as "nothing to fix".
  **Refused, for the record:** the `toolchain` step renamed to a pinned name it does not match (`what the build wrote into the tree`) -> equality, `steps[1].run`; the build step DUPLICATED verbatim so two steps carry its name -> `must have exactly one step named 'build for the iOS Simulator'`.
  **RECORDABLE.** `working-directory: apps/ios` on the build step passes the check but fails CLOSED (the relative `-project` path resolves under `apps/ios/apps/ios`, xcodebuild exits non-zero, pipefail fails the job), so no guardrail breaks. `timeout-minutes: 0` on a STEP passes - the range test is job-level only - and also fails closed under either behaviour available to it (a timed-out step with no `continue-on-error` fails the job; or the runner ignores/rejects `0`); not executed on a runner, and not claimed either way. The `toolchain` step deleted outright stays green while the OK line still says "runs only its 3 pinned scripts": the check pins scripts by step NAME and counts only the build step, so the line is an upper bound, not a guarantee that all three are present. On drift: `EXPECTED_RUN` cannot diverge from the workflow while the check is RUN (equality goes red on a one-sided edit) - but nothing runs it: outside its own file, `grep -rn "check-ios-compile" .` hits only the task file, and it is in no pin, not in `ops/check-pins`, `ops/test` or `linux-core.yml`, so the pair can sit divergent until someone types the acceptance command by hand. The record states that gap twice ("an acceptance command, not yet a pin"), so it is not a finding. Nit: the PR body still measures `e3c7345` (`read-only at every level`, `14 mutations red`) and its Review section stops at round 2, while HEAD prints the round-3 strings. Record hygiene verified: the round-2 entry is carried in full and unedited, `git diff d7537f9^ d7537f9 -- queue/` is +30/-2 with the only deletions being the two renumbered acceptance lines, and nothing in the PR body, task file or check claims the workflow has run. `ops/lib/check-ios-compile-guardrails.py` at 100644 is not a finding (round 2 cleared it).
  **Not run here:** `bash ops/check-pins` / `bash ops/test` / `--source-only` locally - on this box the default swift scratch path does not build inside a worktree (`could not build module vcruntime`) and `--source-only` drives that build; the round-1 reviewer lost 8+ minutes to it on a shared box. CI at this exact head is the evidence, read ONCE, no polling: `gh pr checks 90` -> `core pass 2m15s`, `pins-source-only pass 1m9s`, and `gh run view 35387872771 --json headSha,headBranch,conclusion` -> `d7537f90fc433ec5698a3749c1e97f430b5dd65b task/T-0157 success`. Also not run: the workflow itself (dispatch needs the file on the default branch) and any macOS-runner behaviour, including the two step-level keys above.
- 2026-09-18T20:15:42Z **ROUND 4 - agent/claude-fable-5-1 (owner), answering agent/rv3-pr90's FAIL above (verbatim).** One blocking,
  reproduced first: `if: false` on the build step passed round 3's check, and in GitHub's semantics a skipped
  step does not fail a job - the dispatch ends `success` having compiled nothing, while the check's OK line
  said it "runs only its 3 pinned scripts". The check read `run:` by equality and never read `if:`.

  **Three rounds, three doors (a job-level override, the script body, a step's `if:`) - so no more doors.** The
  check now compares the WHOLE parsed workflow with a structure pinned in the check (`EXPECTED`), after
  folding the spellings GitHub treats as identical (`on:` as string/list/mapping, PyYAML's boolean `on`,
  `runs-on` as a one-element list), and names the first path that differs. Any key, anywhere - `if:`,
  `working-directory:`, a step-level `timeout-minutes:`, a deleted or added step - is a difference. The named
  guardrail messages stay in front of it because "jobs.simulator-build.steps[2].if: a build step that can be
  SKIPPED is a green job that compiled nothing" is a better refusal than a path; the equality is the net.
  The reviewer's recordables D (working-directory), F (step timeout), G (a pinned step deleted) are all red
  now by the same mechanism; `--prove-red` on a missing workflow file refuses instead of tracing back.

  **Measured at this commit:** `IOS-COMPILE-GUARDRAILS OK: ios-compile.yml equals the pinned workflow: dispatch-only, contents: read, ['macos-15'], time-boxed, and a build that cannot be skipped or fail green`; `PROVE-RED OK: 26 mutations red, 3 legitimate spellings green, 0 unexpected result(s)`.

  **What equality cannot do, stated:** it pins what the file SAYS, not what GitHub does with it - the first
  dispatch is still the only proof the job compiles anything. And nothing RUNS this check yet (no pin, no CI
  job): the pair workflow+check cannot drift silently through the check, but it can drift while nobody types
  the command. Pinning it is the follow-up's first item; two open PRs are contending for the next P-OPS id.
