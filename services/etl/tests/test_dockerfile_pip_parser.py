"""Coverage for the pip-install guard in `test_dockerfile.py`, which had none.

`test_the_parser_is_not_silently_blind_to_an_indirect_pip_install` asserts over the *shipped* Dockerfile,
and the shipped Dockerfile contains exactly one RUN, an `apt-get`. So that test asserts over an empty set:
`pip_indirect_targets` - the whitelist engine and the entire security value of T-0046 - was invoked zero
times by the whole suite. reviewer-pr29 proved it by mutation in round 5: replacing the engine's body with
`return []`, so that nothing could ever be an offender again, left the suite byte-identical at 46 passed,
exit 0. Roughly 215 lines of parser were unreachable from any assertion, which is why three fail-open
bypasses survived four review rounds of hand-run red/green demos. Per CLAUDE.md, a check that has never
been seen red is untested; the demos were transcripts, not regression tests.

This file is those transcripts, committed. Every case below is a real construction from a real review
round, named by the round that found it, run through the same `pip_offenders_in` the Dockerfile check
itself calls - not a parallel re-implementation. The parser is a pure function over strings, so none of
this needs Docker, which matters: the pinned image is reachable only through WSL on the box this was
written on, and it contains no pip at all (apt `python3` + `python3-pytest`).
"""
import pytest

from tests.test_dockerfile import (
    PIP_FROM_NETWORK,
    PIP_OFFENDER_REASONS,
    REASON_BUNDLED_SHORT,
    REASON_NOT_A_SPECIFIER,
    REASON_SUBSTITUTION,
    REASON_UNPARSABLE,
    REASON_UNREADABLE_TARGET,
    REASON_UNRECOGNIZED_LONG,
    REASON_UNRECOGNIZED_SHORT,
    directive,
    pip_install_arglists,
    pip_offenders_in,
)

P = "RUN pip install --break-system-packages "

# (RUN text, the reason that must appear, which review round found it).
# Adding a row here is cheap; that is the point - the next bypass anyone finds becomes a committed test in
# the same edit that fixes it, instead of a paragraph in the task log.
BLIND_SPOTS = (
    # --- reviewer-22, the finding this task was filed for -----------------------------------------
    (P + "-r requirements.txt", REASON_UNREADABLE_TARGET, "r22: the original -r hole"),
    # --- round 1 ----------------------------------------------------------------------------------
    (P + "-qr requirements.txt", REASON_BUNDLED_SHORT, "r1: short-flag bundling"),
    (P + "./localpkg", REASON_NOT_A_SPECIFIER, "r1: a local dir needs no -e"),
    (P + "-e .", REASON_UNREADABLE_TARGET, "r1: editable install"),
    (P + ".", REASON_NOT_A_SPECIFIER, "r1: bare dot"),
    # --- round 2 ----------------------------------------------------------------------------------
    (P + "-tf -r requirements.txt", REASON_BUNDLED_SHORT, "r2: first-vs-last bundling letter"),
    (P + '"./localpkg"', REASON_NOT_A_SPECIFIER, "r2: quoting defeats startswith"),
    (P + "'./localpkg'", REASON_NOT_A_SPECIFIER, "r2: single-quoted local path"),
    # --- round 3 ----------------------------------------------------------------------------------
    (P + "$REQS", REASON_SUBSTITUTION, "r3: bare build-arg in target position"),
    (P + "--requirement=requirements.txt", REASON_UNREADABLE_TARGET, "r3: --flag=value form"),
    (P + "-c constraints.txt", REASON_UNREADABLE_TARGET, "r3: constraint file"),
    ('RUN sh -c "pip install -r requirements.txt"', REASON_UNPARSABLE, "r3: pip nested in sh -c"),
    # --- round 4: the whitelist itself was the hole ------------------------------------------------
    (P + "--build constraints.txt requests", REASON_UNRECOGNIZED_LONG,
     "r4: --build abbreviates --build-constraint; it was wrongly whitelisted"),
    (P + "--build-constraint c.txt requests", REASON_UNREADABLE_TARGET, "r4: the real flag behind --build"),
    (P + "--group dev", REASON_UNREADABLE_TARGET, "r4: pyproject dependency group"),
    (P + "--requirements-from-script s.py", REASON_UNREADABLE_TARGET, "r4: script-generated requirements"),
    (P + "-Z requests", REASON_UNRECOGNIZED_SHORT, "r4: any unlisted short flag"),
    (P + "-- requests", REASON_UNRECOGNIZED_LONG, "r4: end-of-options is not modeled"),
    # --- round 5, reviewer-pr29 (a): unquoted '#' truncated the argument list --------------------
    (P + "pkg#egg=z -r requirements.txt", REASON_NOT_A_SPECIFIER,
     "r5a: shlex commenters dropped everything after '#' and vouched for the remainder"),
    (P + "pkg#egg=z ./localpkg", REASON_NOT_A_SPECIFIER, "r5a: '#' also hid an otherwise-caught local path"),
    # --- round 5, reviewer-pr29 (b): '~' was not in the local-path tuple --------------------------
    (P + "~/localpkg", REASON_NOT_A_SPECIFIER, "r5b: /bin/sh -c expands ~ before pip sees it"),
    (P + "~otheruser/localpkg", REASON_NOT_A_SPECIFIER, "r5b: ~user form"),
    # --- round 5, reviewer-pr29 (c): non-http URL schemes matched neither guard -------------------
    (P + "file:///w/wheels/evil.whl", REASON_NOT_A_SPECIFIER, "r5c: file:// is an install source"),
    (P + "svn+ssh://example.org/pkg", REASON_NOT_A_SPECIFIER, "r5c: a VCS scheme with no https:// in it"),
    (P + "hg+https://example.org/pkg", REASON_NOT_A_SPECIFIER, "r5c: previously only incidental via https://"),
    # --- round 5, found while fixing (b)/(c): the same class, two more spellings -------------------
    (P + "`cat req.txt`", REASON_NOT_A_SPECIFIER, "r5: backtick substitution - not a '$', so '$' missed it"),
    (P + "mypkg-1.0-py3-none-any.whl", REASON_NOT_A_SPECIFIER,
     "r5: PEP 503 allows '.' in a name, so a bare wheel filename satisfies the name rule"),
    (P + "mypkg-1.0.tar.gz", REASON_NOT_A_SPECIFIER, "r5: same, sdist"),
    (P + "dist/mypkg-1.0-py3-none-any.whl", REASON_NOT_A_SPECIFIER, "r5: relative path with no ./ prefix"),
    (P + "-", REASON_NOT_A_SPECIFIER, "r5: '-' is stdin, and is too short for the short-flag branch"),
    (P + '""', REASON_NOT_A_SPECIFIER, "r5: the empty argument"),
    # --- the guard must survive the ways a pip invocation can be spelled ---------------------------
    ("RUN pip3 install -r requirements.txt", REASON_UNREADABLE_TARGET, "spelling: pip3"),
    ("RUN python3 -m pip install -r requirements.txt", REASON_UNREADABLE_TARGET, "spelling: python3 -m pip"),
    ("RUN apt-get update && pip install -r requirements.txt", REASON_UNREADABLE_TARGET,
     "spelling: second command in a && chain"),
)

# Installs a real Dockerfile might legitimately contain. A guard that fails these is a guard nobody can
# adopt, and round 4 shipped exactly that: a standard PEP 508 environment marker failed closed.
ORDINARY = (
    (P + "requests", "a plain package name"),
    (P + "requests==2.31.0", "an exact pin"),
    (P + "requests>=2.31.0", "r5: punctuation_chars split this into ['requests', '>', '=2.31.0']"),
    (P + "requests[security]>=2,<3", "extras plus a version range"),
    (P + '"requests; python_version>=\'3.8\'"', "r4: a PEP 508 environment marker"),
    (P + "zope.interface", "a dotted project name - PEP 503 allows it"),
    (P + "python-dateutil", "a hyphenated project name"),
    (P + "torch==2.0.1+cu118", "a local version label"),
    (P + "numpy==1.26.*", "a wildcard pin"),
    (P + "--target /opt/vendor requests", "a destination flag whose value is a path, not a source"),
    (P + "--prefix=/opt requests", "the same, in --flag=value form"),
    (P + "-q -U requests", "unbundled short flags"),
    (P + "--no-cache-dir --no-deps requests", "known boolean flags"),
    (P + "--find-links /wheels requests", "a local wheel dir as a flag value"),
)


def _ids(table):
    return [row[-1] for row in table]


@pytest.mark.parametrize("line, reason, _note", BLIND_SPOTS, ids=_ids(BLIND_SPOTS))
def test_every_known_blind_spot_is_refused(line, reason, _note):
    offenders = pip_offenders_in(line)
    assert offenders, f"fail-OPEN: nothing refused in {line!r}"
    assert reason in [r for _tok, r in offenders], (
        f"refused {line!r} for the wrong reason: expected {reason!r}, got {offenders!r}"
    )


@pytest.mark.parametrize("line, _note", ORDINARY, ids=_ids(ORDINARY))
def test_an_ordinary_pip_install_is_not_refused(line, _note):
    assert pip_offenders_in(line) == [], f"false positive on an ordinary install: {line!r}"


def test_every_case_reaches_the_parser():
    """Vacuity guard. If `pip_install_arglists` ever stops finding the invocation - a broken extraction
    regex, a segmentation change - `ORDINARY` would go green on an empty set and claim the guard works.
    Every case in both tables must produce at least one extracted `pip install`.
    """
    blind = [row[0] for row in BLIND_SPOTS]
    for line in blind + [row[0] for row in ORDINARY]:
        assert pip_install_arglists(line), f"no pip install extracted at all from {line!r}"


def test_the_case_tables_are_populated():
    """Vacuity guard. A parametrized test over an empty table passes without running once."""
    assert len(BLIND_SPOTS) >= 30, len(BLIND_SPOTS)
    assert len(ORDINARY) >= 12, len(ORDINARY)


def test_every_offender_reason_is_demonstrated_by_a_case():
    """Anti-decay guard: a new refusal reason added to `test_dockerfile.py` must arrive with a case here
    that shows it going red, so the next round's fix cannot repeat this one's mistake of landing
    uncovered.
    """
    demonstrated = {r for line, _reason, _note in BLIND_SPOTS for _tok, r in pip_offenders_in(line)}
    assert demonstrated == set(PIP_OFFENDER_REASONS), (
        f"reasons never demonstrated: {sorted(set(PIP_OFFENDER_REASONS) - demonstrated)}; "
        f"reasons produced but not in the declared vocabulary: {sorted(demonstrated - set(PIP_OFFENDER_REASONS))}"
    )


def test_a_run_with_no_pip_install_yields_nothing_to_check():
    line = "RUN apt-get update -q && apt-get install -y -q --no-install-recommends python3 && rm -rf /x"
    assert pip_install_arglists(line) == []
    assert pip_offenders_in(line) == []


def test_the_direct_url_check_still_owns_plain_url_installs():
    """Division of labour, so neither test is assumed to cover the other's cases. `--index-url` is a
    known destination-value flag, so this guard deliberately skips its value and returns nothing;
    `PIP_FROM_NETWORK`, behind `test_nothing_is_pip_installed_from_a_url_or_a_repo`, is what catches it.
    """
    line = P + "--index-url https://evil.example/simple requests"
    assert pip_offenders_in(line) == []
    assert PIP_FROM_NETWORK.search(line)
    for direct in (P + "https://evil.example/pkg.tar.gz", P + "git+https://evil.example/pkg"):
        assert PIP_FROM_NETWORK.search(direct)
        assert pip_offenders_in(direct), "the indirect guard should back the direct one up, not defer to it"


def test_the_shipped_dockerfile_contributes_no_coverage():
    """The honest statement of why this file exists, asserted rather than remembered. While this holds,
    `test_the_parser_is_not_silently_blind_to_an_indirect_pip_install` is vacuous and the tables above are
    the guard's only coverage. If this goes red, the Dockerfile grew a real pip install: good - delete
    this test and say so, but do it deliberately.
    """
    found = [(line, pip_install_arglists(line)) for line in directive("RUN") if pip_install_arglists(line)]
    assert not found, f"the Dockerfile now installs from pip, so this file's premise changed: {found!r}"
