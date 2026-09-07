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
        # `apt-get upgrade`/`dist-upgrade` pulls whatever is newest at build time, which reintroduces exactly
        # the drift the digest pin removes.
        body = " ".join(directive("RUN"))
        assert not re.search(r"apt-get\s+(-\w+\s+)*(dist-)?upgrade", body), body

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
