"""The ETL image is the toolchain every scenic-index run shares.

A moving tag is a silent toolchain change: two runs disagree, nothing in the diff explains why, and the first
place nobody looks is which osm2pgsql built the graph. `.github/workflows/linux-core.yml` already pins the
swift image by digest for the same reason. These tests fail if that discipline slips, and they read the
Dockerfile's INSTRUCTIONS rather than its comments - comments get stripped.
"""
import re
import shlex
from pathlib import Path

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

# Every flag name below was validated against a real, installed pip - not written from memory - after
# round 4 found a hallucinated entry (`--build`) that created a real bypass; see pip_indirect_targets's
# docstring and the task log for how, and for what "validated" means here.

# Flags that read an external file (or a `pyproject.toml` dependency group) whose *content* decides what
# gets installed - the actual unreadable-target class this whole check exists for.
PIP_UNREADABLE_TARGET_FLAGS_LONG = (
    "--requirement", "--editable", "--constraint", "--build-constraint",
    "--requirements-from-script", "--group",
)

# Long flags confidently known to take a value that is NOT an install source - a destination directory, an
# index host, a timeout, ... Their value is skipped rather than examined, so a perfectly ordinary
# `pip install --target /opt/vendor requests` is never misread as installing from "/opt/vendor". This is
# a whitelist, not a blacklist: a long flag that is not on this list, the unreadable-target list, or the
# boolean list below is treated as unrecognized (see `pip_indirect_targets`), not assumed safe.
PIP_DESTINATION_VALUE_FLAGS_LONG = (
    "--target", "--root", "--prefix", "--src", "--cache-dir", "--log", "--python",
    "--platform", "--python-version", "--implementation", "--abi", "--proxy", "--retries", "--timeout",
    "--progress-bar", "--report", "--index-url", "--extra-index-url", "--find-links", "--trusted-host",
    "--cert", "--client-cert", "--upgrade-strategy", "--config-settings",
    "--no-binary", "--only-binary", "--exists-action", "--root-user-action",
    "--all-releases", "--only-final", "--uploaded-prior-to", "--keyring-provider",
    "--use-feature", "--use-deprecated", "--resume-retries",
)

# Long flags confidently known to take no value at all - stable, common, unambiguous. Also a whitelist:
# absence from this list is not evidence of danger, it is just not something this check will vouch for.
PIP_BOOLEAN_FLAGS_LONG = (
    "--user", "--upgrade", "--no-deps", "--no-cache-dir", "--no-compile", "--compile",
    "--no-build-isolation", "--check-build-dependencies", "--break-system-packages",
    "--force-reinstall", "--ignore-requires-python", "--no-warn-script-location", "--no-warn-conflicts",
    "--prefer-binary", "--no-clean", "--require-hashes", "--no-input",
    "--no-index", "--pre", "--disable-pip-version-check", "--no-color", "--dry-run", "--ignore-installed",
    "--help", "--quiet", "--verbose", "--isolated", "--debug", "--require-virtualenv", "--version",
)

# Single letters pip's `install` recognizes as short options, UNBUNDLED (see `pip_indirect_targets` for
# why a bundle of two or more is never resolved at all): which spell an unreadable target, which take a
# value that is a destination rather than a source, and which take no value.
PIP_UNREADABLE_TARGET_LETTERS = set("rce")  # -r requirement / -c constraint / -e editable
PIP_DESTINATION_VALUE_LETTERS = set("tCif")  # -t target / -C config-settings / -i index-url / -f find-links
PIP_BOOLEAN_LETTERS = set("qvUIhV")  # -q quiet / -v verbose / -U upgrade / -I ignore-installed / -h help / -V version

# A PEP 508 dependency specification and nothing else: a PEP 503 project name, optional extras, optional
# version specifiers, optional environment marker. This is the *positional* half of the same whitelist
# discipline round 3 applied to flags, and round 5 is where it was finally applied here too - see
# `pip_indirect_targets` for why enumerating bad positional shapes kept losing. Deliberately excluded, so
# each fails closed: `@` (PEP 508 direct URL references, `pkg @ https://...`), `:` and `/` (URLs of every
# scheme and absolute paths), `~` (home-relative paths, which `/bin/sh -c` expands for pip), `#`
# (fragments like `#egg=`), backticks and `$` (command substitution), and the empty string.
PIP_REQUIREMENT_SPECIFIER = re.compile(
    r"""^
    [A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?              # PEP 503 project name
    (?:\[\s*[A-Za-z0-9][A-Za-z0-9._,\s-]*\])?               # optional extras
    (?:\s*(?:===|==|!=|~=|<=|>=|<|>)\s*[A-Za-z0-9][A-Za-z0-9.*+!_-]*
       (?:\s*,\s*(?:===|==|!=|~=|<=|>=|<|>)\s*[A-Za-z0-9][A-Za-z0-9.*+!_-]*)*
    )?                                                      # optional version specifiers
    (?:\s*;\s*\S.*)?                                        # optional PEP 508 environment marker
    $""",
    re.VERBOSE,
)

# The suffixes above are the one place the name rule is not enough: PEP 503 allows `.` in a project name,
# so `foo-1.0.tar.gz` and `evil.whl` both satisfy `PIP_REQUIREMENT_SPECIFIER` while naming a local archive
# whose contents this parser cannot read. The set is fixed by the packaging specs (wheel, plus the sdist
# formats pip accepts), not by pip's CLI, so unlike the flag lists it does not drift with pip releases.
PIP_DISTRIBUTION_ARCHIVE_SUFFIXES = (".whl", ".egg", ".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")

# The complete vocabulary of reasons this file gives for refusing to vouch for a pip install argument.
# `tests/test_dockerfile_pip_parser.py` asserts its case table exercises every one, so a new offender
# class cannot be added here without a committed case that demonstrates it going red.
REASON_SUBSTITUTION = "a shell/build-arg substitution this parser cannot resolve"
REASON_UNREADABLE_TARGET = "an unreadable target flag"
REASON_UNRECOGNIZED_LONG = "a long flag this check does not recognize"
REASON_BUNDLED_SHORT = "a bundled short flag - bundling order is not modeled"
REASON_UNRECOGNIZED_SHORT = "a short flag this check does not recognize"
REASON_NOT_A_SPECIFIER = (
    "not a PEP 508 requirement - a path, URL, archive, fragment or other install source whose contents "
    "decide what gets installed"
)
REASON_UNPARSABLE = "this invocation could not be tokenized - unbalanced or nested quoting"
PIP_OFFENDER_REASONS = (
    REASON_SUBSTITUTION, REASON_UNREADABLE_TARGET, REASON_UNRECOGNIZED_LONG, REASON_BUNDLED_SHORT,
    REASON_UNRECOGNIZED_SHORT, REASON_NOT_A_SPECIFIER, REASON_UNPARSABLE,
)


def _split_unquoted(text, seps=("&&", "|", ";")):
    """Split `text` on `&&`, `|`, or `;` - the boundaries the rest of this file treats as command
    separators - but never inside a single- or double-quoted region.

    Round 3's `re.split(r"&&|\\||;", run_line)` split on *every* `;` in the raw text, including one
    sitting inside an ordinary quoted argument - `pip install "requests; python_version>='3.8'"`, a
    completely standard PEP 508 environment marker, was torn into two fake command segments before this
    file ever got a chance to recognize the quoting, and round 3's "unresolvable quoting fails closed"
    rule then rejected the fragments. This function tracks quote state with a single pass and one
    character of lookahead - no backslash-escape handling - which is enough for ordinary Dockerfile RUN
    text; anything stranger either still segments correctly by luck or surfaces later as an "unparsable"
    `pip_install_arglists` result via `_shlex_tokens`, which is the fail-closed outcome this file wants
    regardless.
    """
    out, buf, quote = [], [], None
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        sep = next((s for s in seps if text.startswith(s, i)), None)
        if sep:
            out.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


def _shlex_tokens(text):
    """Tokenize `text` the way a POSIX shell would - quotes grouped and their delimiters stripped - using
    the standard library's `shlex` rather than a hand-rolled quote parser, so `"./localpkg"` arrives as
    one token, `./localpkg`, with no separate quote-stripping step needed downstream, and a quoted PEP 508
    marker like `"requests; python_version>='3.8'"` arrives as one token instead of being split on its own
    whitespace.

    Returns `(tokens, ok)`. `ok` is False when `text` cannot be tokenized at all - almost always an
    unbalanced quote, which happens when this text was extracted from inside a *still larger* quoted
    context this function never saw, such as a `pip install` written inside `sh -c "..."` (the extraction
    keeps everything from "install" to the end of that segment, which ends mid-quote when the segment
    itself was quoted from the outside). That failure is reported as unparsable, not silently ignored or
    guessed at - the same fail-closed answer this file gives a heredoc it cannot read into.

    Round 5 found both of `shlex`'s defaults wrong for this job, in opposite directions:

    - `commenters` defaults to `'#'`, so the lexer *dropped the rest of the line* at the first `#` and
      still returned `ok=True`. `pip install pkg#egg=z -r requirements.txt` tokenized to `['pkg']`, and
      the caller then vouched for an argument list two thirds of which it had never seen - the exact
      "reads a partial input and reports it as whole" failure this whole file exists to prevent, sitting
      inside the tokenizer. It is also simply wrong about shell: `#` opens a comment only at the start of
      a word, so a real `/bin/sh -c` passes `pkg#egg=z` to pip intact. Cleared outright rather than
      taught the word-start rule: a `#` anywhere in a pip invocation now survives into a token, matches
      nothing on any whitelist, and fails closed. That over-refuses a genuine trailing `# comment` inside
      a RUN - a cost this file takes knowingly, and zero today, since no RUN here installs from pip.
    - `punctuation_chars=True` split on `<`, `>`, `(`, `)` etc. even mid-token, so the single most common
      argument pip ever gets, `requests>=2.31.0`, arrived as `['requests', '>', '=2.31.0']` - three
      fragments, none of them a requirement, none of them recognizable as anything. It was harmless only
      while every fragment fell through to a permissive "not a flag, therefore fine" default; it makes
      the positive `PIP_REQUIREMENT_SPECIFIER` check below impossible to state. The command separators it
      was presumably enabled for (`&&`, `|`, `;`) are already handled by `_split_unquoted`, before this
      function is ever called, and handled with quote-awareness that `punctuation_chars` does not have.
    """
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=False)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer), True
    except ValueError:
        return [], False


def pip_install_arglists(run_line):
    """`(tokens, ok)` for every `pip install` invocation in one RUN instruction (`pip`, `pip3`, or
    `python -m pip`/`python3 -m pip` all match, and so does a `pip` wrapped in `sh -c "..."` or given by
    its full path) - split at unquoted &&/|/; boundaries (`_split_unquoted`) so one command's flags can
    never leak into another's, and so a `;` inside a quoted argument never manufactures a fake boundary.
    """
    out = []
    for segment in _split_unquoted(run_line):
        for m in re.finditer(r"\bpip3?\b[^&|;]*?\binstall\b", segment):
            out.append(_shlex_tokens(segment[m.end():]))
    return out


def pip_indirect_targets(args):
    """Everything in one `pip install` invocation's (already quote-resolved) argument list that this
    parser cannot confidently read, resolve, or vouch for.

    This is a whitelist, not a blacklist: a token is only ever treated as safe when it is positively
    recognized as one of a small number of confidently-understood shapes (a known boolean flag, a known
    destination-value flag, or a bare word that is not a flag, not a `$` substitution, and does not look
    like a local path). Everything else fails closed, including:

    - `-r`/`-c`/`-e`/`--build-constraint`/`--requirements-from-script`/`--group`, long or short,
      unbundled - flags that read an external file or `pyproject.toml` group whose *content* decides what
      gets installed. Round 4 added the last three: a real pip only has three single-letter flags of this
      shape (`-r`/`-c`/`-e`), but its long-form flag set has six, and this file only knew about half of
      them until reviewer-29's round-4 finding forced actually reading `pip install --help` instead of
      recalling it.
    - **any bundled short flag at all** (two or more letters after a single `-`), regardless of which
      letters. reviewer-29 proved short-option bundling resolves via the FIRST value-taking letter
      consuming the rest of that same token, not the LAST letter consuming the next token, and modeling
      that correctly for every letter pip might ever add is exactly the game of catch-up this file's
      docstrings already record losing repeatedly. Refusing to parse a bundle at all closes the whole
      class at once, at the cost of also failing on harmless bundles like `-qt` - a trade this file takes
      deliberately; see the task log.
    - **any positional argument that is not a PEP 508 dependency specification** (`PIP_REQUIREMENT_SPECIFIER`),
      and any that is one but ends in a distribution-archive suffix. Round 5 is where this half of the
      function stopped being a blacklist. Until then a positional was refused only if it was `.`/`..` or
      started `./`, `../`, `/` - an enumeration of remembered bad shapes, and rounds 1, 2 and 5 each found
      another shape that was not on it: `pip install ./localpkg` (round 1), `"./localpkg"` (round 2), and
      then `~/localpkg`, `file:///w/wheels/evil.whl` and `` `cat req.txt` `` (round 5) - a home-relative
      path that `/bin/sh -c` expands before pip sees it, a non-http URL scheme that `PIP_FROM_NETWORK`'s
      `https?://` never matched, and backtick command substitution, which `$`-matching missed because
      backticks are not `$`. Three more prefix characters, findable only by thinking of them. The fix is
      the same inversion round 3 made for flags: say what a safe positional *is* - a project name with
      optional extras, version specifiers and marker - and refuse everything else, so the next prefix
      character nobody thought of fails closed without this file having to have heard of it.
    - a token containing `$` - a shell/build-time substitution (`ARG`/`ENV`) this parser cannot resolve;
      it could name a URL, a `git+` ref, or a `-r` file just as easily as a version pin. (Now redundant
      with the rule above for positionals, and kept because it also fires inside flag values and gives a
      more specific reason than "not a requirement".)
    - a long or short flag that is not on one of the three small, explicitly-curated lists above - an
      "unrecognized flag" is a flag this check does not know it can vouch for, not a flag assumed safe.
      round 4 removed three entries from those lists (`--build`, `--use-pep517`,
      `--no-python-version-warning`) that were never real pip flags to begin with - `--build` in
      particular is what let `pip install --build constraints.txt requests` through: pip does not have a
      `--build` flag, but its long-option parser accepts any unambiguous prefix of a real one, and
      `--build` is an unambiguous prefix of `--build-constraint`. Whitelisting a flag name that was never
      validated against a real pip whitelisted a bypass without anyone writing one on purpose. This
      whitelist stays sound only because every entry is an *exact, complete* name copied from a real
      `pip install --help`, matched here with plain string equality - never a prefix, never a guess - so
      the abbreviation feature that created the `--build` hole has nothing to attach to on this side: an
      abbreviated or unvalidated spelling of *any* flag, safe or dangerous, is simply not on the list and
      therefore always falls through to "unrecognized" and fails closed.

    None of this reads what a target *contains* - only whether the argument list names one this parser
    cannot see into, or contains something it cannot confidently classify at all.
    """
    offenders = []
    skip_next = False
    for tok in args:
        if skip_next:
            skip_next = False
            continue

        if "$" in tok:
            offenders.append((tok, REASON_SUBSTITUTION))
            continue

        if tok.startswith("--"):
            head = tok.split("=", 1)[0]
            if head in PIP_UNREADABLE_TARGET_FLAGS_LONG:
                offenders.append((tok, REASON_UNREADABLE_TARGET))
                skip_next = "=" not in tok
                continue
            if head in PIP_DESTINATION_VALUE_FLAGS_LONG:
                skip_next = "=" not in tok
                continue
            if head in PIP_BOOLEAN_FLAGS_LONG:
                continue
            offenders.append((tok, REASON_UNRECOGNIZED_LONG))
            continue

        if tok.startswith("-") and len(tok) > 1:
            letters = tok[1:]
            if len(letters) > 1:
                offenders.append((tok, REASON_BUNDLED_SHORT))
                continue
            letter = letters
            if letter in PIP_UNREADABLE_TARGET_LETTERS:
                offenders.append((tok, REASON_UNREADABLE_TARGET))
                skip_next = True
                continue
            if letter in PIP_DESTINATION_VALUE_LETTERS:
                skip_next = True
                continue
            if letter in PIP_BOOLEAN_LETTERS:
                continue
            offenders.append((tok, REASON_UNRECOGNIZED_SHORT))
            continue

        # Positional. Safe only if positively recognized as a PEP 508 dependency specification that is
        # not also the filename of a distribution archive; everything else - `.`, `~/pkg`, `./localpkg`,
        # `file:///x.whl`, `pkg#egg=z`, `` `cat req.txt` ``, `-` (stdin), `>` (a redirection this parser
        # does not model), `""` - fails closed without this check needing to recognize it individually.
        if not PIP_REQUIREMENT_SPECIFIER.match(tok) or tok.lower().endswith(PIP_DISTRIBUTION_ARCHIVE_SUFFIXES):
            offenders.append((tok, REASON_NOT_A_SPECIFIER))
    return offenders


def pip_offenders_in(run_line):
    """Every offending token in one RUN instruction's text, from whatever `pip install` invocations it
    contains - the whole guard behind one pure function of a string, so that
    `tests/test_dockerfile_pip_parser.py` exercises the same code path the Dockerfile check below runs
    rather than a parallel re-implementation of it.
    """
    offenders = []
    for tokens, ok in pip_install_arglists(run_line):
        if not ok:
            offenders.append(("(unparsable)", REASON_UNPARSABLE))
            continue
        offenders.extend(pip_indirect_targets(tokens))
    return offenders


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
        offenders = pip_offenders_in(line)
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
