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
