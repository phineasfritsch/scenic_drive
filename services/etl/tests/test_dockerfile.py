"""The ETL image is the toolchain every scenic-index run shares.

A moving tag is a silent toolchain change: two runs disagree, nothing in the diff explains why, and the first
place nobody looks is which osm2pgsql built the graph. `.github/workflows/linux-core.yml` already pins the
swift image by digest for the same reason. These tests fail if that discipline slips, and they read the
Dockerfile's INSTRUCTIONS rather than its comments - comments get stripped.
"""
import re
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

# The long `pip install` flags whose value IS the unreadable target: pip reads the file or path they
# name, and this parser has no way to read it too.
PIP_UNREADABLE_TARGET_FLAGS_LONG = ("--requirement", "--editable", "--constraint")

# Long flags confidently known to take a value that is NOT an install source - a destination directory, an
# index host, a timeout, ... Their value is skipped rather than examined, so a perfectly ordinary
# `pip install --target /opt/vendor requests` is never misread as installing from "/opt/vendor". This is
# a whitelist, not a blacklist: a long flag that is not on this list, the unreadable-target list, or the
# boolean list below is treated as unrecognized (see `pip_indirect_targets`), not assumed safe.
PIP_DESTINATION_VALUE_FLAGS_LONG = (
    "--target", "--root", "--prefix", "--src", "--build", "--cache-dir", "--log", "--python",
    "--platform", "--python-version", "--implementation", "--abi", "--proxy", "--retries", "--timeout",
    "--progress-bar", "--report", "--index-url", "--extra-index-url", "--find-links", "--trusted-host",
    "--cert", "--client-cert", "--upgrade-strategy", "--global-option", "--config-settings",
    "--no-binary", "--only-binary", "--exists-action", "--root-user-action",
)

# Long flags confidently known to take no value at all - stable, common, unambiguous. Also a whitelist:
# absence from this list is not evidence of danger, it is just not something this check will vouch for.
PIP_BOOLEAN_FLAGS_LONG = (
    "--user", "--upgrade", "--no-deps", "--no-cache-dir", "--no-compile", "--compile",
    "--no-build-isolation", "--use-pep517", "--check-build-dependencies", "--break-system-packages",
    "--force-reinstall", "--ignore-requires-python", "--no-warn-script-location", "--no-warn-conflicts",
    "--prefer-binary", "--no-clean", "--require-hashes", "--no-python-version-warning", "--no-input",
    "--no-index", "--pre", "--disable-pip-version-check", "--no-color", "--dry-run", "--ignore-installed",
    "--help",
)

# Single letters pip's `install` recognizes as short options, UNBUNDLED (see `pip_indirect_targets` for
# why a bundle of two or more is never resolved at all): which spell an unreadable target, which take a
# value that is a destination rather than a source, and which take no value.
PIP_UNREADABLE_TARGET_LETTERS = set("rce")  # -r requirement / -c constraint / -e editable
PIP_DESTINATION_VALUE_LETTERS = set("tifb")  # -t target / -i index-url / -b build / -f find-links
PIP_BOOLEAN_LETTERS = set("qvUIh")  # -q quiet / -v verbose / -U upgrade / -I ignore-installed / -h help


def pip_install_arglists(run_line):
    """The argument tokens following every `pip install` invocation in one RUN instruction (`pip`,
    `pip3`, or `python -m pip`/`python3 -m pip` all match, and so does a `pip` wrapped in `sh -c "..."` or
    given by its full path) - one token list per invocation, split at the &&/|/; boundaries the rest of
    this file already treats as command separators, so one command's flags can never leak into another's.
    """
    out = []
    for segment in re.split(r"&&|\||;", run_line):
        for m in re.finditer(r"\bpip3?\b[^&|;]*?\binstall\b", segment):
            out.append(segment[m.end():].split())
    return out


def _dequote(tok):
    """Strip one matched pair of leading/trailing shell quotes - Docker's shell form removes exactly
    this much before pip ever sees the argument, so `"./localpkg"` and `./localpkg` are the same install.
    Returns `(content, resolvable)`. `resolvable` is False when a quote character is present but does not
    form a clean matched pair around the whole token - almost always because the true, space-containing
    argument was torn into several fake tokens by this file's plain `.split()` tokenizer, which does not
    understand quoting well enough to reassemble it. That case is reported as unresolvable, not guessed at.
    """
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        return tok[1:-1], True
    if "'" in tok or '"' in tok:
        return tok, False
    return tok, True


def pip_indirect_targets(args):
    """Everything in one `pip install` invocation's argument list that this parser cannot confidently
    read, resolve, or vouch for.

    This is a whitelist, not a blacklist: a token is only ever treated as safe when it is positively
    recognized as one of a small number of confidently-understood shapes (a known boolean flag, a known
    destination-value flag, or a bare word that is not a flag, not quoted, not a `$` substitution, and
    does not look like a local path). Everything else fails closed, including:

    - `-r`/`-c`/`-e`, long or short, unbundled - the actual unreadable-target flags this check exists for.
    - **any bundled short flag at all** (two or more letters after a single `-`), regardless of which
      letters. reviewer-29 proved short-option bundling resolves via the FIRST value-taking letter
      consuming the rest of that same token, not - as an earlier version of this function assumed - the
      LAST letter consuming the next token: `pip install -tf -r requirements.txt` resolves as `--target f`
      then a fully separate `-r requirements.txt`, confirmed against a real pip. Modeling that correctly
      for every letter pip might ever add is exactly the game of catch-up this file's docstrings already
      record losing three times (the curl-into-bash test, the upgrade test, and this test's own first two
      versions). Refusing to parse a bundle at all closes the whole class at once, at the cost of also
      failing on harmless bundles like `-qt` - a trade this file takes deliberately; see the task log.
    - a bare positional path (`.`, `..`, or anything starting `./`, `../` or `/`) after quote-stripping -
      pip installs a local directory as a plain positional argument with no flag required at all.
    - a token whose quoting cannot be confidently resolved by stripping one matched pair (see `_dequote`).
    - a token containing `$` - a shell/build-time substitution (`ARG`/`ENV`) this parser cannot resolve;
      it could name a URL, a `git+` ref, or a `-r` file just as easily as a version pin.
    - a long or short flag that is not on one of the three small, explicitly-curated lists above - an
      "unrecognized flag" is a flag this check does not know it can vouch for, not a flag assumed safe.

    None of this reads what a target *contains* - only whether the argument list names one this parser
    cannot see into, or contains something it cannot confidently classify at all.
    """
    offenders = []
    skip_next = False
    for raw_tok in args:
        if skip_next:
            skip_next = False
            continue

        tok, resolvable = _dequote(raw_tok)
        if not resolvable:
            offenders.append((raw_tok, "a quoted argument this check cannot confidently resolve"))
            continue
        if "$" in tok:
            offenders.append((raw_tok, "a shell/build-arg substitution this parser cannot resolve"))
            continue

        if tok.startswith("--"):
            head = tok.split("=", 1)[0]
            if head in PIP_UNREADABLE_TARGET_FLAGS_LONG:
                offenders.append((raw_tok, "an unreadable target flag"))
                skip_next = "=" not in tok
                continue
            if head in PIP_DESTINATION_VALUE_FLAGS_LONG:
                skip_next = "=" not in tok
                continue
            if head in PIP_BOOLEAN_FLAGS_LONG:
                continue
            offenders.append((raw_tok, "a long flag this check does not recognize"))
            continue

        if tok.startswith("-") and len(tok) > 1:
            letters = tok[1:]
            if len(letters) > 1:
                offenders.append((raw_tok, "a bundled short flag - bundling order is not modeled"))
                continue
            letter = letters
            if letter in PIP_UNREADABLE_TARGET_LETTERS:
                offenders.append((raw_tok, "an unreadable target flag"))
                skip_next = True
                continue
            if letter in PIP_DESTINATION_VALUE_LETTERS:
                skip_next = True
                continue
            if letter in PIP_BOOLEAN_LETTERS:
                continue
            offenders.append((raw_tok, "a short flag this check does not recognize"))
            continue

        if tok in (".", "..") or tok.startswith(("./", "../", "/")):
            offenders.append((raw_tok, "a local path"))
            continue
        # else: an ordinary requirement specifier - a package name, optionally pinned or extras'd - and
        # therefore safe as far as this check goes.
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
    """`(RUN line, offending tokens)` for every RUN instruction with at least one pip install target this
    parser cannot read into - see `pip_indirect_targets`.
    """
    hits = []
    for line in directive("RUN"):
        for args in pip_install_arglists(line):
            offenders = pip_indirect_targets(args)
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
        """
        offenders = pip_indirect_target_offenders()
        assert not offenders, (
            "this pip install invocation contains something this check cannot confidently resolve or "
            "vouch for - an unreadable target flag (-r/-c/-e), a bundled short flag, an unresolvably "
            "quoted argument, a $ substitution, an unrecognized flag, or a bare local path: "
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
