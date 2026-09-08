---
id: T-0086
title: the environment defeats every ops checker regardless of how the root is derived
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/boot.sh]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

[[T-0077]] moved every `ops/*` wrapper off `git rev-parse --show-toplevel` and onto `${BASH_SOURCE[0]}`, then
added `ops/lib/boot.sh`, which unsets fifteen `GIT_*` variables so "an ops/* script talks to the repo it lives
in, whatever the caller's environment says."

**A round-three adversary defeated that sentence three ways, with no source edit in any of them.**

**1. `GIT_CONFIG_PARAMETERS` — the one `GIT_CONFIG_*` name boot.sh does not unset**, and the mechanism
`git -c` itself uses. It is the immediate neighbour of the `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_0` pair the fix
DID clear and cited as its reason for closing the route:

    GIT_CONFIG_PARAMETERS="'core.autocrlf=true'" bash ops/sane     -> reproduces the fix's own demo verbatim
    GIT_CONFIG_PARAMETERS="'core.excludesFile=...'" bash ops/sane  -> SANE FAIL exit 2  becomes  SANE OK exit 0
                                                                       with the stray .swift still on disk

**2. `PYTHONPATH`.** T-0076 replaced "pick the interpreter by NAME" with "pick it by CAPABILITY", measured with
`importlib.util.find_spec()` — which searches `sys.path`, which the caller writes with `PYTHONPATH`. The
decision moved from a name the caller controls to an import the caller controls. Worse, `site` imports
`sitecustomize` from `sys.path` at interpreter startup, so a twelve-line `sitecustomize.py` on `PYTHONPATH`
produced:

    PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux    EXIT=0
    QUEUE OK (999 tasks)                                            EXIT=0

with zero pins loaded and zero assertions run. **Those are the exact two strings boot.sh's own header cites as
the measured proof of the original defect.** boot.sh unsets fifteen `GIT_*` variables and zero `PYTHON*` ones.

**3. `PATH`.** A fifteen-line shell script named `git`, earlier on `PATH`, passing everything through except
`git status` (and later `git ls-files`), from which it filters the evidence. Every `ops/*` checker and every
pin assertion resolves `git` from the caller. boot.sh never touches `PATH`.

**The shape is the finding, not the three names.** A denylist of environment variables is the same losing game
as a denylist of SQL keywords or a list of cannot-fail assertion texts, and this repository has now lost it
three times in three different files. Every fix so far has hardened the mechanism it was pointed at while the
caller kept a different lever.

- **Allowlist the environment instead.** Re-exec through `env -i` with an explicit, minimal set
  (`PATH`, `HOME`, `LANG`, `TMPDIR`, and whatever a specific script genuinely needs), rather than unsetting
  names somebody has to keep remembering. Anything not named is gone, including names invented after this task.
- **Resolve `git` and the interpreter by absolute path** once, at boot, and use those paths everywhere.
  A sanitized `PATH` is still a `PATH`.
- Decide what an ops script should do when the environment is hostile: refusing is defensible and cheap.
  Whatever it is, it must be a decision in the file, not an omission.
- The three demonstrations above are reproducible as written and belong in the log as the red run.
- **Do not close this by adding `GIT_CONFIG_PARAMETERS`, `PYTHONPATH` and `PATH` to the unset list.** That is
  the fourth round of the same mistake, and the next adversary will bring the fifth name.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-three adversarial verification of T-0077 and T-0076.
  Every command above was executed by an agent that did not write the fix, with no edit to any tracked source
  file.
