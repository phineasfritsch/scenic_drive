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
