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

# Long flags that also take a value, but the value is not an install source - a destination directory, an
# index host, a timeout, ... Their value must be skipped when looking for a bare local-path target, or a
# perfectly ordinary `pip install --target /opt/vendor requests` would be misread as installing from
# "/opt/vendor".
PIP_VALUE_FLAGS_LONG = PIP_UNREADABLE_TARGET_FLAGS_LONG + (
    "--target", "--root", "--prefix", "--src", "--build", "--cache-dir", "--log", "--python",
    "--platform", "--python-version", "--implementation", "--abi", "--proxy", "--retries", "--timeout",
    "--progress-bar", "--report", "--index-url", "--extra-index-url", "--find-links", "--trusted-host",
    "--cert", "--client-cert", "--upgrade-strategy", "--global-option", "--config-settings",
    "--no-binary", "--only-binary", "--exists-action", "--root-user-action",
)

# Single letters pip's `install` recognizes as short options, split the same way: which spell an
# unreadable target, and which (that or any other) consume a value. Short options bundle - `pip install
# -qr requirements.txt` really does parse as `-q` (boolean) then `-r requirements.txt`, confirmed against
# a real pip: `pip install -qr /tmp/nonexistent_req.txt` fails with "Could not open requirements file".
# Bundling order does not matter for *whether* -r/-c/-e fired (either letter still triggers it whether it
# lands mid-bundle, taking the rest of that token as its value, or last, taking the next token) - only for
# which token holds the value, which is what PIP_SHORT_VALUE_LETTERS is for.
PIP_SHORT_UNREADABLE_LETTERS = set("rce")  # -r requirement / -c constraint / -e editable
PIP_SHORT_VALUE_LETTERS = set("rcetibf")  # + -t target / -i index-url / -b build / -f find-links


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


def pip_indirect_targets(args):
    """Everything in one `pip install` invocation's argument list that this parser cannot read the
    contents of: a `-r`/`-c`/`-e` flag in long form, short form, or bundled with other short flags in
    either order (`-qr`, `-rq`, ...); or a bare positional path - `.`, `..`, or anything starting with
    `./`, `../` or `/` - naming a local project with no flag in front of it at all (pip installs a local
    directory as a plain positional argument; `-e` makes it editable, it does not make it readable).

    Flag values that are not themselves install sources (`--target DIR`, `--index-url URL`, ...) are
    skipped so they can never be mistaken for one - this is what keeps `pip install --target /opt/vendor
    requests` green.
    """
    offenders = []
    skip_next = False
    for tok in args:
        if skip_next:
            skip_next = False
            continue
        head = tok.split("=", 1)[0]
        if head in PIP_UNREADABLE_TARGET_FLAGS_LONG:
            offenders.append(tok)
            skip_next = "=" not in tok
            continue
        if head in PIP_VALUE_FLAGS_LONG:
            skip_next = "=" not in tok
            continue
        if tok.startswith("--"):
            continue
        if tok.startswith("-") and len(tok) > 1:
            letters = tok[1:]
            if any(c in PIP_SHORT_UNREADABLE_LETTERS for c in letters):
                offenders.append(tok)
            skip_next = bool(letters) and letters[-1] in PIP_SHORT_VALUE_LETTERS
            continue
        if tok in (".", "..") or tok.startswith(("./", "../", "/")):
            offenders.append(tok)
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

        First version of this test only matched `-r`, `-e` and `-c` as the literal first two characters
        after a word boundary, and a bare `.` as an isolated token. reviewer-29 got two ordinary
        constructions past it, both 10/10 green: `pip install -qr requirements.txt` (pip bundles short
        options - `-qr` really is `-q` then `-r requirements.txt`, confirmed against a real pip) and
        `pip install ./localpkg` (pip installs a local project directory as a bare positional argument;
        `-e` makes it editable, it is not required to make it a local, unreadable target at all - the
        docstring claiming "editable/local path" coverage for `-e` alone was itself a decorative-check
        defect, describing coverage the code did not have).

        This version tokenizes each `pip install` invocation's argument list (`pip_install_arglists`) and
        walks it (`pip_indirect_targets`) rather than pattern-matching the raw text, so it can tell a flag
        from its value and a bundled short option from an unrelated one - see those two docstrings for
        exactly what is and is not covered. It still fails closed on the flag or the bare path, not on
        what either points to, so adding a genuine indirect target stays a conversation (the check grows
        to read the file, deliberately) rather than becoming a silent hole again. Fails closed today only
        because no RUN in this Dockerfile installs from pip.

        Known, deliberately out of scope: `pip install $SOME_VAR` with no `-r`/`-e`/`-c` flag at all - a
        bare shell variable that could resolve to anything - is not caught. Resolving `ARG`/`ENV`
        substitution is a different, much larger parser than "read the RUN text"; see the task log for why
        that was left unfixed here rather than papered over with a broader match.
        """
        offenders = pip_indirect_target_offenders()
        assert not offenders, (
            "this parser cannot read the contents of a pip install target named this way - "
            "-r/--requirement, -e/--editable, -c/--constraint (long, short, or bundled with other short "
            "flags), or a bare local path ('.', '..', './x', '../x', '/x'): " + repr(offenders)
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
