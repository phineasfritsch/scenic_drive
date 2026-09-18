"""The inputs manifest: every external file this pipeline consumes, with how to verify it and what we may do
with it.

Two verification modes, because the sources genuinely differ:

  sha256        A static file. The digest is pinned here and must match byte-for-byte. Used for anything that
                does not change under us (USGS 3DEP tiles, NLCD/TCC rasters, a dated byway shapefile).
  upstream-md5  A file the publisher refreshes on a schedule and publishes a checksum sidecar for (Geofabrik
                rebuilds its extracts DAILY). Pinning a digest here would break the fetcher every day and teach
                everyone to bypass it; instead we fetch the publisher's sidecar and verify against that.

There is deliberately no "none" mode. An input with no way to verify it is an input we do not take.

`license` is required on every entry. An agent must not be able to add a source without recording what we are
allowed to do with the data - that question is much harder to answer six months later, and getting it wrong is
the one class of mistake that can end the project rather than cost a day.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

VERIFY_MODES = ("sha256", "upstream-md5")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
# Licences we have actually reasoned about. Adding one means deciding what it permits, not typing a string.
KNOWN_LICENSES = (
    "ODbL-1.0",              # OpenStreetMap. Attribution + share-alike on derived databases.
    "US-PD-17USC105",        # US federal government work, public domain (USGS, USFS/MRLC, FHWA, NPS).
    "CC0-1.0",
    "CDLA-Permissive-2.0",   # Overture
    "Apache-2.0",            # Foursquare OS Places
    "CA-OpenData",           # State of California open data terms
    "CC-BY-4.0",             # ESA WorldCover. Attribution required; carried in LICENSE-DATA.
)


def _url_ok(url: str) -> bool:
    """https everywhere, with one narrow exception: loopback over plain http, so the fetcher's own tests can
    run against a local server without a TLS certificate. Anyone who controls your loopback interface already
    owns the machine, so this carve-out grants nothing. It is deliberately not widened to 'any private IP'."""
    if url.startswith("https://"):
        return True
    return bool(re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?/", url))


@dataclass
class Input:
    # Every field defaults, so a manifest entry that OMITS a required one is reported as a validation problem
    # with a useful message rather than crashing the parser with a TypeError. A stack trace tells the operator
    # nothing about which entry is wrong or why.
    name: str = ""
    url: str = ""
    verify: str = ""
    license: str = ""
    purpose: str = ""
    sha256: str | None = None
    checksum_url: str | None = None
    bytes: int | None = None
    retrieved: str | None = None
    consumed_by: str | None = None          # the task id that introduced it
    notes: str = ""
    problems: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        p: list[str] = []
        if not self.name or not re.match(r"^[a-z0-9][a-z0-9._-]*$", self.name):
            p.append(f"{self.name!r}: name must be lowercase [a-z0-9._-]")
        if not _url_ok(self.url):
            p.append(f"{self.name}: url must be https (plain http is allowed only for 127.0.0.1/localhost, "
                     f"which exists so the fetcher's tests can run against a local server)")
        if self.verify not in VERIFY_MODES:
            p.append(f"{self.name}: verify must be one of {VERIFY_MODES}, got {self.verify!r}")
        if not self.license:
            p.append(f"{self.name}: license is required - what are we allowed to do with this data?")
        elif self.license not in KNOWN_LICENSES:
            p.append(f"{self.name}: license {self.license!r} is not in KNOWN_LICENSES; add it there deliberately")
        if not self.purpose:
            p.append(f"{self.name}: purpose is required - why does the pipeline need this file?")
        if self.verify == "sha256":
            if not self.sha256:
                p.append(f"{self.name}: verify=sha256 needs a pinned sha256 "
                         f"(fetch once with --record-digest, then commit the digest)")
            elif not SHA256_RE.match(self.sha256):
                p.append(f"{self.name}: sha256 must be 64 lowercase hex chars")
        if self.verify == "upstream-md5" and not self.checksum_url:
            p.append(f"{self.name}: verify=upstream-md5 needs checksum_url")
        self.problems = p
        return p


def parse(text: str) -> list[Input]:
    """Parse the manifest. Same deliberately-small YAML subset as the queue: a list of flat mappings."""
    items: list[Input] = []
    cur: dict[str, object] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^-\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            cur = {}
            items.append(cur)  # type: ignore[arg-type]
            cur[m.group(1)] = _scalar(m.group(2), m.group(1))
            continue
        m = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m and cur is not None:
            cur[m.group(1)] = _scalar(m.group(2), m.group(1))
            continue
        raise ValueError(f"manifest: cannot parse line: {raw!r}")
    out = []
    for d in items:
        known = {f for f in Input.__dataclass_fields__ if f != "problems"}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"manifest: unknown field(s) {sorted(unknown)} in entry {d.get('name')!r}")
        out.append(Input(**d))  # type: ignore[arg-type]
    return out


# Only these fields are numbers. Coercing every all-digit string to int turned a sha256 of 64 zeros into
# int 0, which is falsy, so validation reported "needs a pinned sha256" instead of "that digest is malformed" -
# a type confusion that hides the real problem behind a misleading message.
NUMERIC_FIELDS = ("bytes",)


def _scalar(v: str, field: str = ""):
    v = v.strip()
    if v in ("", "null", "~"):
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if field in NUMERIC_FIELDS and re.fullmatch(r"\d+", v):
        return int(v)
    return v


def validate_all(inputs: list[Input]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for i in inputs:
        if i.name in seen:
            problems.append(f"{i.name}: duplicate entry")
        seen.add(i.name)
        problems.extend(i.validate())
    if not inputs:
        problems.append("manifest is empty - an empty manifest must not read as 'all inputs verified'")
    return problems
