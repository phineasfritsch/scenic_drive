---
id: T-0038
title: services/etl/Dockerfile was never created - T-0023 shipped without the pinned ETL image
state: done
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:50:28Z
lease_expires_at: 2026-09-07T18:50:28Z
worktree: ../wt/T-0038
branch: task/T-0038
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-22
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`T-0023`'s brief required `services/etl/Dockerfile` pinned BY DIGEST with osmium-tool, osm2pgsql, GDAL and
python. It was never written. The file does not exist, `git ls-files services/etl` does not list it, and
reviewer-12 signed the task off anyway - nothing in the suite reads it, so nothing went red.

That matters for T-0024 onward: the Bay Area extract runs osmium/osm2pgsql, and without a pinned image every
agent runs a different toolchain and blames the data when the output differs.

- `services/etl/Dockerfile`, base image pinned by `@sha256:` digest (same rule as `swift:6.1-noble` in
  `.github/workflows/linux-core.yml`), with osmium-tool, osm2pgsql, GDAL/ogr2ogr and python3.
- A test that the Dockerfile exists and its `FROM` line carries a `@sha256:` digest - anchored on the file, not
  a comment, so "we'll pin it later" fails the suite instead of passing quietly.
- Demonstrate red: delete the digest from `FROM`, show the test fail, restore, show it pass.

## Log
- 2026-09-07T15:50:28Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:50:28Z

- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-21 is taken, so agent/reviewer-22.
  Branch stacked on `task/T-0023`, which owns `services/etl/` and is reviewed but not merged (CI is down).

- **The image.** `services/etl/Dockerfile`, `FROM ubuntu:24.04@sha256:33ceb719...987517`, resolved 2026-09-07
  with `docker buildx imagetools inspect ubuntu:24.04`. Ubuntu rather than a GDAL vendor image because noble
  ships osmium-tool, osm2pgsql and gdal-bin in one archive that pins them against each other, instead of three
  upstreams that do not.

- **Built it, rather than asserting it builds.** In WSL, against the real digest:

      $ docker build -q -t scenic-etl:t0038 .
      sha256:6055593233884b3c93dc7495a2d633edd9544ff4223bf2cd4e65307b68944cd6

      $ docker run --rm scenic-etl:t0038 ...
      osmium version 1.16.0
      osm2pgsql version 1.11.0
      GDAL 3.8.4, released 2024/02/08          (ogr2ogr and gdalinfo both)
      Python 3.12.3
      sqlite3 3.45.1
      pyyaml 6.0.1  pytest 7.4.4

- **Ran this repo's own ETL suite inside it**, which is the thing the image exists for:

      $ docker run --rm -v "$d/etl:/w" -w /w scenic-etl:t0038 python3 -m pytest -q
      ..................s........................                              [100%]

- **The tests** (`services/etl/tests/test_dockerfile.py`, 7 of them) read the Dockerfile's INSTRUCTIONS, never
  its comments: continuations joined, comments and blanks dropped, then assertions on FROM and RUN. Every one
  demonstrated red by mutating the Dockerfile and restoring it:

      RED: osmium-tool dropped from the package list -> exit 1  test_every_tool_the_pipeline_shells_out_to_is_installed
      RED: gdal-bin dropped                          -> exit 1  test_every_tool_the_pipeline_shells_out_to_is_installed
      RED: apt-get dist-upgrade added                -> exit 1  test_the_package_list_is_not_upgraded_out_from_under_the_pin
      RED: installs by piping the internet into a shell -> exit 1  test_nothing_is_installed_by_piping_the_internet_into_a_shell
      RED: a second FROM sneaks in                   -> exit 1  test_there_is_exactly_one_base_image (+2)
      RED: digest stripped from FROM                 -> exit 1  test_the_base_image_is_pinned_by_digest
      RED: FROM ubuntu:latest                        -> exit 1  test_the_base_image_is_pinned_by_digest, ..._not_a_floating_tag
      GREEN restored                                 -> exit 0, Dockerfile byte-identical to the start

- **One of those tests was decorative and the red run is what caught it.** The pipe-to-shell check originally
  asked whether the literal string `"curl | bash"` appeared in the RUN body. It passed against
  `RUN curl -fsSL https://example.org/x.sh | bash` - which is what the pattern looks like in the wild - so it
  could not go red for the thing it was named after. Replaced with a regex over each RUN instruction
  separately, then re-demonstrated red. The harness script now asserts that each mutation actually changed the
  file before running pytest, so a demo can never silently test nothing.

- **Running the suite in the image found a real bug in T-0023's work, which is mine.**
  `test_the_manifest_is_actually_tracked_by_git` computed the repo root as `Path(__file__).parents[3]`. That
  arithmetic is right in a checkout and wrong everywhere else: inside the image, where only `services/etl` is
  mounted, it raised `IndexError: 3` out of pathlib without ever mentioning the manifest. reviewer-18 checked
  the "git missing from PATH" case and found it errored loudly; nobody checked "not inside a work tree", and
  the two fail differently.

  Fixed here rather than filed, because it is a live crash in a file this task's `touches:` already covers and
  this branch already contains T-0023: ask git for the root (`git rev-parse --show-toplevel`), skip LOUDLY
  when there is no work tree or no git binary, and keep failing when git IS present and the file is untracked.
  The missing-binary case needed its own arm - `subprocess.run` raises `FileNotFoundError` rather than
  returning non-zero, so the first version of the fix still died with a traceback in the image.

  Both behaviours re-demonstrated:

      in a checkout, manifest un-staged:  FAILED ...::test_the_manifest_is_actually_tracked_by_git   (still red)
      in a checkout, restored:            1 passed
      in the image (no git):              SKIPPED [1] tests/test_manifest.py:47: git is not installed here,
                                          cannot check tracking: [Errno 2] No such file or directory: 'git'

  A skip is not as good as a check. It is visible in the report, `ops/test` counts skips separately, and
  `ops/test` always runs in a checkout - so the branch CI takes is the one that enforces. Whoever reviews this
  should push on whether that is good enough, or whether the ETL image should simply ship git.

- **Verification, all local** (GitHub Actions has been refusing to execute since ~15:11 UTC: a recent run
  reports "recent account payments have failed or your spending limit needs to be increased", so every job on
  every branch dies in seconds with zero steps):

      $ bash ops/test        -> TESTS linux=93/76 ios=skipped failed=0 skipped=0 / OK      exit 0
      $ bash ops/check-pins  -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0          exit 0
      $ bash ops/queue-check -> QUEUE OK (39 tasks)                                        exit 0

  linux goes 86 -> 93: seven new Dockerfile tests.

- Handing to agent/reviewer-22; state -> review.

- 2026-09-07 reviewed by agent/reviewer-22. **FAIL** - one bypass of the upgrade-guard test is real and
  concrete, not theoretical; leaving it in `queue/review/`.

  **What I re-derived vs. took on trust.** Everything below was independently re-derived, not read off the
  log and believed: pulled the current `ubuntu:24.04` digest myself, built the image from the worktree's
  actual `Dockerfile` in a WSL-native temp dir, ran every tool inside the built container, ran the 7
  Dockerfile tests against ~10 hand-mutated Dockerfiles I wrote, did the `git rm --cached`/`git reset` red
  demonstration on `test_manifest.py` myself, and ran `bash ops/test`, `bash ops/check-pins`,
  `bash ops/queue-check` fresh in this worktree. Only the "GitHub Actions is down" claim is taken on trust
  (matches what I was told; not independently checked, and out of scope per the task brief).

  - **Digest: real and current.** `docker buildx imagetools inspect ubuntu:24.04` ->
    `sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517` - byte-identical to
    `services/etl/Dockerfile:14`. Built clean from a WSL-native copy (`docker build -q` ->
    `sha256:6055...`), ran inside it: osmium 1.16.0, osm2pgsql 2026-09-07 build (v1.11.0), GDAL 3.8.4
    (`ogr2ogr`/`gdalinfo` both), Python 3.12.3, sqlite3 3.45.1. All confirmed, not asserted.

  - **BLOCKER - `test_the_package_list_is_not_upgraded_out_from_under_the_pin`
    (`services/etl/tests/test_dockerfile.py:66-70`) is a second decorative test, same species as the
    curl|bash one the owner already caught.** The regex is `apt-get\s+(-\w+\s+)*(dist-)?upgrade` - it only
    matches the literal token `apt-get` immediately followed by `upgrade`/`dist-upgrade`. Two RUN bodies that
    achieve exactly the version drift this test exists to prevent both leave all 7 tests green:
      1. `RUN apt-get update -q && apt upgrade -y -q && apt-get install ...` - `apt` (not `apt-get`) is the
         same binary, ships in every Ubuntu image since 16.04, and is Debian/Ubuntu's own documented
         interactive-preferred alias; an agent patching this image for a CVE is more likely to type `apt`
         than `apt-get`.
      2. `RUN apt-get update -q && apt-get install ... && apt-get install --only-upgrade -y libc6` - never
         uses the word "upgrade" as a command verb at all, so the regex's `(dist-)?upgrade` anchor never
         fires, while `--only-upgrade` does precisely what `apt-get upgrade` does for the named package(s).
      Both reproduced live: full pytest run, `.......  [100%]`, 7/7 green, against a Dockerfile that reintroduces
      the exact toolchain drift the digest pin exists to close. Failure scenario: a future agent bumps a CVE'd
      library with either form, ships it, `ops/test` stays green, and the next Bay Area extract silently runs a
      different libc/apt package set than the one the pin claims to guarantee - which is precisely the bug
      T-0023/T-0038 exist to prevent, reintroduced through the test meant to catch it.

  - **MAJOR - the "should the image ship git" question has a sharper answer than "yes": shipping git alone
    does not close the loophole for this project's own workflow.** Every task in this repo runs in a linked
    worktree (`wt/<task-id>`, this review included) whose `.git` is a file pointing at
    `<main-repo>/.git/worktrees/<task-id>`. I installed git at container-runtime (`apt-get install -y git`
    inside a throwaway build of the shipped image) and re-ran
    `test_the_manifest_is_actually_tracked_by_git` two ways:
      - mounting only `services/etl` (as T-0038's own demo does): `git rev-parse --show-toplevel` still fails
        (no `.git` in scope at all) -> skip, as expected.
      - mounting the *entire* worktree (`-v .../wt/T-0038:/repo`): still skips -
        `fatal: not a git repository: /repo/C:/Users/phineasf/.../scenic_drive/.git/worktrees/T-0038` - because
        the worktree's `.git` file points at an absolute host path *outside* the mounted tree (the sibling
        `scenic_drive` checkout), which a container can never see unless that sibling is also mounted at the
        identical absolute path.
      So "ship git" converts the `FileNotFoundError` skip into a `not inside a git work tree` skip for any
      containerized run against a worktree checkout - i.e. every task this repo runs - not into a real check.
      **This does not weaken the current gate**: `ops/test` runs pytest natively on the host, never inside the
      image, and I confirmed natively (from `wt/T-0038` directly) that `git rev-parse --show-toplevel`
      resolves the worktree root correctly and the test enforces for real - see below. The gap only bites if a
      future CI job builds this image and runs `pytest` *inside* it as its own gate (the natural next step
      after this task, and literally what the task log's own demo just did by hand). If that happens, ship a
      `.git`-independent tracking check (e.g. bake a manifest checksum at build time) rather than relying on
      git-in-container against a worktree mount, or explicitly document that in-container test runs are
      demonstrations only and never a gate.

  - **Re-derived the manifest fix's red/green claims directly** (not from the log): on the host, in this
    worktree, `git rev-parse --show-toplevel` -> `C:/Users/phineasf/Documents/GitHub/wt/T-0038` (correct).
    `git rm --cached services/etl/inputs/manifest.yaml` then `python -m pytest -q
    tests/test_manifest.py::TestRealManifest::test_the_manifest_is_actually_tracked_by_git` -> **red**,
    `AssertionError: ... is not tracked by git: ... did not match any file(s) known to git`. `git reset
    services/etl/inputs/manifest.yaml` -> green again, `git status --short` empty. Confirms the fix genuinely
    fails closed in the path that actually gates (`ops/test`, native), independent of the container-skip
    question above.

  - **Re-derived the Dockerfile red demonstrations myself, not from the log** - built ~10 adversarial
    Dockerfiles (comment-hidden `FROM`, multi-stage build, `ARG BASE=ubuntu:latest` + `FROM $BASE`, a
    BuildKit `RUN <<EOF` heredoc hiding `curl|bash` and the package list, a package name present only in a
    trailing `#` comment, tab-indented continuations, a fake-but-well-formed all-zero `@sha256:` digest) and
    ran the real test suite against each inside the built image. All of these correctly go red or fail closed
    **except** the two `apt`/`--only-upgrade` bypasses above. Two MINOR observations, not blocking: (1) the
    heredoc `RUN <<EOF` body is invisible to `directive("RUN")` (lines inside it don't start with `RUN `), so
    it fails closed for a hidden `curl|bash` but would also give a confusing "the image does not install:
    [...]" false failure for a legitimate future heredoc-style `RUN`; (2) nothing forbids an unpinned `pip
    install <url>` - same class of gap as the already-fixed curl|bash test, just a different tool, not
    currently exploited since the Dockerfile has no pip step today. Also confirmed the digest-pin test checks
    only the `@sha256:[0-9a-f]{64}` *shape*, not that the digest actually resolves to the named tag (a
    syntactically valid but fabricated digest passes) - not scoring this as a defect since that verification
    needs a registry round-trip and is explicitly the reviewer's manual job per this task's own brief.

  - Mutated and restored `services/etl/Dockerfile` directly in this worktree (stripped the digest, confirmed
    red, `git checkout --` to restore, confirmed green); `git status --short` is clean before and after every
    experiment above - all mutation/attack work happened in WSL-native temp copies or was restored
    immediately.

  - **Verification, exact output, this worktree, fresh (`npm ci --no-audit --no-fund` run first in
    `services/api`, per the known T-0040 gap):**

        $ bash ops/test
        TESTS linux=93/76 ios=skipped failed=0 skipped=0
        OK                                                  exit 0

        $ bash ops/check-pins
        PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux    exit 0

        $ bash ops/queue-check
        QUEUE OK (39 tasks)                                              exit 0

    All three match the owner's claimed numbers exactly. `skipped=0` in `ops/test` confirms the manifest
    test's skip path is *not* being taken in the path that actually gates this repo right now.

  - **Verdict: FAIL.** The image itself is solid (digest verified live against the registry, every required
    tool confirmed running inside a real build, the manifest-tracking fix is a genuine improvement and
    re-verified independently both ways). But the task brief said "assume there is another" decorative test
    after the curl|bash one, and there is one: `test_the_package_list_is_not_upgraded_out_from_under_the_pin`
    does not catch `apt upgrade` or `apt-get install --only-upgrade`, both of which defeat the exact thing the
    test is named for and are more natural to write than the pattern it does catch. Fix the regex (or match
    on tokens rather than a literal `apt-get ... upgrade` string) and re-demonstrate red against both shapes
    above, then resubmit. The worktree-mount finding on the manifest skip is logged for whoever picks up the
    "should we run pytest inside the built image in CI" follow-up; it does not block this task since the
    current gate is unaffected.

- Sending back to agent/claude-opus-5; state stays `review` (left in `queue/review/`, not moved to `done/`).

### 2026-09-07 - owner response to reviewer-22: the BLOCKER was real, and there was a third

**BLOCKER - `test_the_package_list_is_not_upgraded_out_from_under_the_pin` was decorative.** reviewer-22 got
two upgrades past it with all seven tests green: `apt upgrade -y` (apt and apt-get are the same binary, and
`apt` is Ubuntu's own documented spelling) and `apt-get install --only-upgrade libc6`, which never uses the
word as a verb. That is the second test of this species in one file, and the lesson is now written into the
docstring: a check spelled "does the bad string appear" is a check against one spelling.

Replaced with a pattern over each RUN instruction covering apt/apt-get/aptitude with any of
dist-upgrade/full-upgrade/safe-upgrade/upgrade, plus `--only-upgrade` and `unattended-upgrade`. Demonstrated
red on all five shapes, including both of reviewer-22's:

    RED: apt upgrade (same binary, Ubuntu's own spelling)          -> exit 1
    RED: apt-get install --only-upgrade (never says the verb)      -> exit 1
    RED: apt-get dist-upgrade                                      -> exit 1
    RED: aptitude safe-upgrade                                     -> exit 1
    RED: unattended-upgrade                                        -> exit 1
    GREEN restored                                                 -> exit 0, Dockerfile byte-identical

**MINOR (pip from the network) - added, and it caught me writing a third decorative check.** The first version
of `PIP_FROM_NETWORK` was written through a shell one-liner, so its `\b` word boundaries were interpreted as
literal backspace bytes (0x08) before Python ever saw them. The regex compiled, the test passed, and it could
never have matched anything. Found by looking at the file with `cat -A` rather than trusting that it worked;
rewritten from a script file. Three decorative checks in one task is a pattern, not bad luck: every one of
them passed on first write and only the red run exposed it.

Demonstrated red on three shapes:

    RED: pip install from a URL          -> exit 1
    RED: pip install from a git ref      -> exit 1
    RED: pip install from another index  -> exit 1

**MINOR (heredoc RUN bodies) - now fails closed loudly rather than quietly.** The parser joins backslash
continuations and knows nothing about BuildKit heredocs, so a `RUN <<EOT` body would read as empty and every
check above would pass on it. A Dockerfile written that way now fails with "this parser does not read heredoc
RUN bodies, so it would check nothing in: ..." - a red test asking someone to teach the parser, instead of
seven green ones that read none of it. Demonstrated red with `RUN <<EOT bash / apt-get -y upgrade / EOT`.

**MAJOR (the skip, and whether the image should ship git) - reviewer-22's answer is better than mine and I am
taking it.** They installed git in the container, mounted the full worktree, and it STILL skipped:
`not a git repository: .../scenic_drive/.git/worktrees/T-0038`, because a worktree's `.git` is a file pointing
at an absolute host path outside any single-worktree mount. So "just add git" would not close the skip for this
project's own layout - it would only move where it fails. Leaving the image without git, with the skip, and
with reviewer-22's finding recorded here: the enforcing path is `ops/test`, which runs natively in a checkout,
resolves worktrees correctly, and reports `skipped=0`. Anyone who later wants the ETL suite gated from inside
a container has to solve the worktree mount, not the git binary.

**Verification after the fixes, all local:**

    $ cd services/etl && python -m pytest -q tests/   -> 45 passed
    $ bash ops/test        -> TESTS linux=95/76 ios=skipped failed=0 skipped=0 / OK   exit 0
    $ bash ops/check-pins  -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0       exit 0
    $ bash ops/queue-check -> QUEUE OK (39 tasks)                                     exit 0

linux goes 93 -> 95: the two new tests. Back to agent/reviewer-22 in `review/`.

- 2026-09-07 re-reviewed by agent/reviewer-22. **PASS** - `git mv` to `queue/done/`.

  **What I re-derived vs. took on trust.** Rebuilt the image fresh from this commit's `Dockerfile` (unchanged
  in this diff) in a WSL-native temp dir; confirmed no bytes changed by diffing against the digest verified
  last round. Checked the regex source for control bytes myself rather than trusting the fix description:

      $ python -c "import pathlib; print(pathlib.Path('services/etl/tests/test_dockerfile.py').read_bytes().count(b'\x08'))"
      0
      $ cat -A services/etl/tests/test_dockerfile.py | sed -n '17,33p'   # no ^H, no stray control chars, plain $ line endings

    `UPGRADES` and `PIP_FROM_NETWORK` (`services/etl/tests/test_dockerfile.py:24-33`) are what they appear to
    be - not re-trusting the "found and fixed a backspace-byte regex" claim, verified it directly.

  - **Re-derived both of my original BLOCKER bypasses: both now RED.**
    `RUN apt-get update -q && apt upgrade -y -q && ...` ->
    `AssertionError: the image upgrades packages past its pin: [...'apt upgrade -y -q'...]`.
    `RUN ... && apt-get install --only-upgrade -y libc6` -> same assertion, `--only-upgrade` branch. Both
    reproduced live against a rebuilt image, not re-read from the log.

  - **Attacked the new `UPGRADES` pattern (`test_dockerfile.py:24-28`) with four more shapes; all four RED,
    none slip through:**
      - `RUN apt-get -o APT::Get::AllowUnauthenticated=true upgrade -y` - red (option string between the verb
        and "upgrade" contains no `&|;`, so `[^&|;]*` still spans it).
      - `RUN apt-get update -q ; apt-get upgrade -y -q` (semicolon instead of `&&`) - red (the regex retries
        from every start position; the second `apt-get` sits directly before `upgrade`).
      - `RUN ["apt-get", "upgrade", "-y"]` (JSON exec form) - red (`\b` matches across the quote characters
        fine).
      - `RUN sh -c "apt-get update && apt-get upgrade -y"` - red (the whole line, quotes included, is still
        scanned as one RUN instruction).

  - **Attacked the new `PIP_FROM_NETWORK` pattern (`test_dockerfile.py:31-33`) with three shapes from the
    coordinator's list:**
      - `pip install --break-system-packages -f https://example.org/wheels somepkg` (`-f` short flag) - red,
        because any URL that would actually function as a `--find-links` target still contains a literal
        `https?://` that the pattern already matches. Also tried `-f10.0.0.5:8080/wheels` (short flag,
        attached, no scheme) - this one is GREEN (evades the regex), but I don't score it as a working bypass:
        `urlparse` requires a scheme starting with a letter, so a token starting with a digit is not parsed as
        a URL by pip's find-links handling and is treated as a (non-existent) local path, not a network fetch.
        On paper it evades the pattern; in practice it doesn't reach the network either. Noting it, not
        blocking on it.
      - **`COPY requirements.txt /tmp/requirements.txt` + `RUN pip install -r /tmp/requirements.txt`, with
        the URL/`git+` pin living inside `requirements.txt` rather than the `RUN` line - GREEN. This is a real,
        functioning bypass**, not a paper one: none of the 9 Dockerfile tests read any file other than the
        Dockerfile itself (confirmed by source: `DOCKERFILE = Path(__file__).resolve().parents[1] /
        "Dockerfile"` is the only file any test opens), so an unpinned dependency moved one file sideways is
        completely invisible to this suite regardless of how it's spelled. Reproduced live, 9/9 green with the
        Dockerfile containing a `COPY` + `-r requirements.txt` and no direct URL/`git+` text anywhere in it.

  **Severity call on the requirements.txt finding: MAJOR, not BLOCKER, filed rather than blocking this PASS.**
  Difference from the three prior "decorative" bugs (curl|bash literal string, `apt-get`-only literal, the
  backspace-byte regex): those checks were each internally broken - they matched nothing like what their name
  promised, on the exact shape the Dockerfile actually uses. This one does exactly what it says (catches a
  URL/`git+`/index literal in the RUN text) - the gap is that the whole test file's design is "read the
  Dockerfile's instructions," and a requirements file is not the Dockerfile. Same category as "the digest-pin
  test checks shape, not registry truth" from last round: a real, worth-logging scope boundary, not a broken
  promise. It also doesn't touch the load-bearing invariant (toolchain version pinning via the digest + the
  upgrade guard) - `pip`/`COPY requirements.txt` do not appear anywhere in the current `Dockerfile`, so this is
  prospective, not live. Recommend whoever picks this up make `test_nothing_is_pip_installed_from_a_url_or_a_repo`
  fail closed on `pip install (-r|-e|\.)\S` the same way `test_the_parser_is_not_silently_blind_to_a_heredoc_run`
  fails closed on `<<` - "I cannot see into this" is the honest answer, not silence.

  **Verification, this worktree, fresh (`npm ci` re-run in `services/api`):**

      $ bash ops/test
      TESTS linux=95/76 ios=skipped failed=0 skipped=0
      OK                                                  exit 0

      $ bash ops/check-pins
      PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux    exit 0

      $ bash ops/queue-check
      QUEUE OK (39 tasks)                                              exit 0

  All three match the owner's claimed numbers exactly.

  **Verdict: PASS.** The BLOCKER is genuinely fixed and does not merely move - re-derived against a freshly
  built image, not trusted from the log. Four additional adversarial shapes against the upgrade guard all go
  red; the regex fix generalizes rather than patching my two specific examples. The claimed backspace-byte
  regex bug is verified absent by inspecting the committed bytes directly. The worktree-mount finding from
  last round is correctly recorded as the reason the image stays without git. One real, MAJOR, non-blocking
  gap found and logged (pip install indirected through a COPYed requirements file) - filed for a follow-up,
  not grounds to send this back a third time over a test that is itself MINOR-severity and does exactly what
  it claims to.
