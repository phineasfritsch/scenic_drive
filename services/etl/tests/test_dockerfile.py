"""The ETL image is the toolchain every scenic-index run shares.

A moving tag is a silent toolchain change: two runs disagree, nothing in the diff explains why, and the first
place nobody looks is which osm2pgsql built the graph. `.github/workflows/linux-core.yml` already pins the
swift image by digest for the same reason. These tests fail if that discipline slips, and they read the
Dockerfile's INSTRUCTIONS rather than its comments - comments get stripped.
"""
import re
from pathlib import Path

# The pip argument grammar lives in its own module: it knows nothing about Docker, it is the larger
# half of what used to be one 436-line file, and only the two blind-spot tests below use it.
from tests.pip_install_grammar import pip_install_arglists, pip_indirect_targets

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"

# The tools the pipeline actually shells out to. Naming them here means deleting one from the image is a
# failing test rather than a confusing crash three stages into a 15-minute build.
REQUIRED_PACKAGES = ("osmium-tool", "osm2pgsql", "gdal-bin", "python3", "sqlite3")

# A download piped straight into a shell, in any of the shapes it is actually written.
PIPE_TO_SHELL = re.compile(r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z|k|da)?sh\b")

# Anything that moves packages off the versions the pinned base image froze. `apt` and `apt-get` are the same
# binary; `--only-upgrade` upgrades without ever saying the word as a verb; aptitude and unattended-upgrade
# are the same act under other names.

UPGRADES = re.compile(
    r"\b(apt|apt-get|aptitude)\b[^&|;]*\b(dist-upgrade|full-upgrade|safe-upgrade|upgrade)\b"
    r"|--only-upgrade\b"
    r"|\bunattended-upgrades?\b"
)

# pip reaching the network for something the digest does not cover: a URL, a VCS ref, or another index.
PIP_FROM_NETWORK = re.compile(
    r"\bpip3?\b[^&|;]*\binstall\b[^&|;]*(https?://|git\+|--index-url|--extra-index-url|--find-links)"
)



def instructions():
    """Dockerfile lines with comments and blank lines removed, continuations joined."""
    out, buf = [], ""
    for raw in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        out.append((buf + line).strip())
        buf = ""
    if buf:
        out.append(buf.strip())
    return out


def directive(name):
    return [i for i in instructions() if i.upper().startswith(name.upper() + " ")]


def pip_indirect_target_offenders():
    """`(RUN line, offending tokens)` for every RUN instruction with at least one pip install invocation
    this parser cannot vouch for - either because `pip_indirect_targets` names a specific offending token
    (see that function), or because `_shlex_tokens` could not tokenize the invocation's arguments at all
    (an unresolvable quoting shape, reported as such rather than silently skipped).
    """
    hits = []
    for line in directive("RUN"):
        for tokens, ok in pip_install_arglists(line):
            if not ok:
                hits.append((line, [("(unparsable)", "this invocation could not be tokenized - "
                                                       "unbalanced or nested quoting")]))
                continue
            offenders = pip_indirect_targets(tokens)
            if offenders:
                hits.append((line, offenders))
    return hits


class TestTheImageIsPinned:
    def test_the_dockerfile_exists(self):
        """T-0023's brief required this file and shipped without it; nothing in the suite noticed."""
        assert DOCKERFILE.is_file(), f"{DOCKERFILE} is missing"

    def test_there_is_exactly_one_base_image(self):
        assert len(directive("FROM")) == 1, directive("FROM")

    def test_the_base_image_is_pinned_by_digest(self):
        (line,) = directive("FROM")
        assert re.search(r"@sha256:[0-9a-f]{64}\b", line), (
            f"FROM is not digest-pinned: {line!r}. A tag moves; pin it with @sha256: or the toolchain "
            f"changes underneath us with nothing in the diff to show it."
        )

    def test_the_base_image_is_not_a_floating_tag(self):
        (line,) = directive("FROM")
        assert not re.search(r":latest\b", line), f"FROM names :latest - {line!r}"

    def test_every_tool_the_pipeline_shells_out_to_is_installed(self):
        body = " ".join(directive("RUN"))
        missing = [p for p in REQUIRED_PACKAGES if not re.search(rf"(?<![\w.-]){re.escape(p)}(?![\w.-])", body)]
        assert not missing, f"the image does not install: {missing}"

    def test_the_package_list_is_not_upgraded_out_from_under_the_pin(self):
        """Upgrading at build time pulls whatever is newest then, which reintroduces exactly the drift the
        digest pin removes.

        The first version matched only a literal `apt-get ... upgrade`. reviewer-22 got two upgrades past it
        with all seven tests green: `apt upgrade -y` (apt and apt-get are the same binary, and `apt` is
        Ubuntu's own documented spelling) and `apt-get install --only-upgrade libc6`, which never uses
        "upgrade" as a verb at all. Second decorative test of the same species in this one file - the lesson
        is that a check written as "does the bad string appear" is a check written against one spelling.
        """
        offenders = [i for i in directive("RUN") if UPGRADES.search(i)]
        assert not offenders, f"the image upgrades packages past its pin: {offenders}"

    def test_nothing_is_installed_by_piping_the_internet_into_a_shell(self):
        """`curl ... | bash` is an unpinned install: the digest pins the base image and this walks straight
        past it, fetching whatever that URL serves at build time.

        The first version of this test asked whether the literal string "curl | bash" appeared in the RUN
        body. It passed against `curl -fsSL https://example.org/x.sh | bash`, which is what the pattern
        actually looks like in the wild - a check that could not go red for the thing it was named after.
        Caught by running the red demonstration instead of assuming it.
        """
        offenders = [i for i in directive("RUN") if PIPE_TO_SHELL.search(i)]
        assert not offenders, f"unpinned install path in the image: {offenders}"

    def test_nothing_is_pip_installed_from_a_url_or_a_repo(self):
        """Same hole as curl-into-bash, wearing a python hat: `pip install <url>` or `pip install git+...`
        fetches whatever that address serves at build time, straight past the digest. reviewer-22, MINOR.
        Debian's python3 is externally-managed anyway, which is why the image takes python3-yaml from apt.
        """
        offenders = [i for i in directive("RUN") if PIP_FROM_NETWORK.search(i)]
        assert not offenders, f"unpinned pip install in the image: {offenders}"

    def test_the_parser_is_not_silently_blind_to_an_indirect_pip_install(self):
        """reviewer-22, reviewing T-0038: `COPY requirements.txt .` followed by
        `RUN pip install --break-system-packages -r requirements.txt` passed all nine tests in this file,
        9/9 green, while `requirements.txt` pinned `git+https://...`. PIP_FROM_NETWORK reads only the RUN
        text, and `-r requirements.txt` does not put a URL there - it puts a filename there, and the URL
        lives one COPY away, someplace this parser never opens.

        This test has been wrong twice trying to model pip's own argument grammar closely enough to tell
        a safe `pip install` from an unsafe one: version 1 matched `-r`/`-e`/`-c` as literal first-two
        characters and missed `pip install -qr requirements.txt` (short-flag bundling) and
        `pip install ./localpkg` (a local directory needs no `-e` at all). Version 2 added bundling and a
        bare-path check, and was wrong about the bundling itself - it assumed the LAST letter of a bundle
        draws its value from the next token, when pip actually resolves the FIRST value-taking letter
        against the REST OF THE SAME token; reviewer-29 proved `pip install -tf -r requirements.txt`
        resolves as `--target f` then a fully separate, ordinary `-r requirements.txt`, and it also missed
        `pip install "./localpkg"` / `'./localpkg'`, since a leading quote character defeats a
        `.startswith(("./", ...))` check. Two rounds, two new gaps, both genuine insights about a grammar
        this file does not control and that changes between pip versions - the same shape of loss already
        recorded in this file's docstrings for the curl-into-bash test and the upgrade test.

        Version 3 stops trying to keep up and fails closed instead, the same way
        `test_the_parser_is_not_silently_blind_to_a_heredoc_run` already does: `pip_indirect_targets` is a
        whitelist of small, confidently-understood shapes (a short list of known boolean flags, a short
        list of known destination-value flags, and a bare word that is not a flag/quote/`$`/path), and
        *anything else in a `pip install` invocation is itself the failure* - a bundled short flag
        (regardless of which letters - see that function's docstring for why bundling is not modeled at
        all anymore), an unresolvably-quoted argument, a `$` substitution, or a flag this check does not
        recognize. The Dockerfile does not use pip at all today, so the cost of this strictness is zero;
        the cost of being clever about pip's CLI grammar has now been paid three times. Adding a real pip
        install - bundled flags and all - means widening one of the three whitelists here, deliberately,
        in the same commit; that is the conversation this test exists to force. Fails closed today only
        because no RUN in this Dockerfile installs from pip.

        `pip install $SOME_VAR` with no flag at all is now caught too (previously left open, on the
        reasoning that a broader `$` match would false-positive on an `ARG`-substituted version pin like
        `pip install "requests==${PIN}"` - a real, legitimate pattern; that reasoning has not changed, a
        version pin like that would indeed now fail closed here). The decision changed because a bare
        variable in target position is indistinguishable, by this parser, from `-r $REQS` with the flag
        stripped off by a careless edit - and `--target $DIR`/`--prefix $DIR` (a `$` in a value this check
        already skips as a known destination, not examined at all) still pass, so the strictness lands
        specifically on install *sources*, not on every `$` anywhere in the invocation. See the task log
        for the full reasoning behind reversing course on this from the previous round.

        Version 4: the whitelist itself was the hole. `--build` was whitelisted as a safe destination flag
        - it is not a real pip flag at all, but pip's long-option parser accepts any unambiguous
          abbreviation of a real one, and `--build` unambiguously abbreviates `--build-constraint`, a
          genuine unreadable-target flag; `pip install --build constraints.txt requests` passed every test
          here. The fix is not "model pip's abbreviation rules" (that is a fourth grammar to chase); it is
          that this whitelist was never validated against a real pip and had no business vouching for a
          string nobody had confirmed was a real flag. Every entry across all three lists was re-checked,
          entry by entry, against `pip install --help` on the pip actually installed for this task
          (26.1.1) - three more invented entries came out (`--build`, `--use-pep517`,
          `--no-python-version-warning`), three real unreadable-target flags this file never knew about
          went in (`--build-constraint`, `--requirements-from-script`, `--group`), and this matching is
          still, and only ever, exact string equality - never a prefix, so an abbreviation of anything,
          safe or dangerous, simply is not on the list and fails closed as "unrecognized". Full validation
          method and the corrected lists are in `pip_indirect_targets`'s own docstring and the task log.

          Two more false positives came from the same round: `--quiet`/`--verbose` were whitelisted only
          as `-q`/`-v`, an asymmetry with no reason behind it (now both forms are listed), and `--isolated`
          had no entry in either form despite being real and common. Separately, `pip install "requests;
          python_version>='3.8'"` - an ordinary PEP 508 environment marker - failed closed, because
          `pip_install_arglists` split on *every* `;` in the raw RUN text, including the one inside that
          quoted marker, before this file had any notion of quoting; `_split_unquoted` now tracks quote
          state while looking for command boundaries, and tokenizing switched from a bare `.split()` plus
          a hand-rolled `_dequote` to the standard library's `shlex` (`_shlex_tokens`), which handles
          quoting the way a real shell does instead of the way this file's own code guessed it might.
        """
        offenders = pip_indirect_target_offenders()
        assert not offenders, (
            "this pip install invocation contains something this check cannot confidently resolve or "
            "vouch for - an unreadable target flag (-r/-c/-e/--build-constraint/"
            "--requirements-from-script/--group), a bundled short flag, an unparsable/unresolvable "
            "quoting shape, a $ substitution, an unrecognized flag, or a bare local path: "
            + repr(offenders)
        )

    def test_the_parser_is_not_silently_blind_to_a_heredoc_run(self):
        """BuildKit lets a RUN body live in a heredoc. This parser joins backslash continuations and knows
        nothing about heredocs, so every check above would read such a body as empty and pass.

        Failing closed is the honest answer while that is true: a Dockerfile written that way must be a
        red test asking someone to teach the parser, not seven green ones that read none of it.
        reviewer-22 found this; it fails closed today only because nothing here uses a heredoc.
        """
        offenders = [i for i in instructions() if "<<" in i]
        assert not offenders, (
            "this parser does not read heredoc RUN bodies, so it would check nothing in: " + repr(offenders)
        )
