---
id: T-0046
title: the Dockerfile pip check cannot see a URL that lives in a COPYed requirements file
state: claimed
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
