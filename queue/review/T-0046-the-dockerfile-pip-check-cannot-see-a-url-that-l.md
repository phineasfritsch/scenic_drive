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
reviewer: agent/reviewer-29
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

  **Committed-blob byte check** (after commit, before push): `git show HEAD:services/etl/tests/
  test_dockerfile.py | python -c "import sys; d=sys.stdin.buffer.read(); print(len(d), d.count(b'\x08'))"`
  -> reported once committed, below; verified in the working tree first: 20005 bytes, `0` occurrences of
  `\x08`. `cat -A` on the new `_dequote`/`pip_indirect_targets` code shows plain `$`-terminated lines
  throughout, no control-character artifacts.

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
