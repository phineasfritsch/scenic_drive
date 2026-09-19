"""The OSM XML stream between `osmium cat` and the tag pass - read one element at a time, write it back.

WHY XML AND NOT PYOSMIUM (ruling R6 in T-0168's log). `osmium tags` does not exist and osmium-tool 1.16.0
has no subcommand that adds a tag to an object, so something of ours has to write the tag. PyOsmium would be
that something, except it is not in the pinned image (services/etl/Dockerfile installs osmium-tool,
osm2pgsql, gdal-bin, python3, python3-pytest, python3-yaml, sqlite3, and tests/test_dockerfile.py pins that
list) and a writer that needs it could not be imported by the host suite at all - the byte-identical test
would have to skip, on the one property the whole rewrite exists to have. So osmium does every PBF encode
and decode, `osmium cat` converts in both directions, and this module is the only thing between them.

WHY IT IS A STREAM AND NOT A TREE. A region clip is hundreds of thousands of elements; `ET.parse` would hold
all of them. `iter_top_level` yields each child of `<osm>` as it ends and clears the root behind it, so
memory is one element deep. The element is REUSED - read what you need while you hold it.

WHAT MAKES TWO RUNS BYTE-IDENTICAL (ruling R3). Output order is input order, because this is a copy and not
a rebuild. Every element is serialised by ElementTree, whose attribute order is the order the attributes
were parsed in, so the input's own order survives. All whitespace is stripped and exactly one newline is
written between elements, so indentation in the input cannot vary the output. Nothing here reads a clock.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

NODE = "node"
WAY = "way"
RELATION = "relation"
TAG = "tag"
ND = "nd"

XML_DECLARATION = "<?xml version='1.0' encoding='UTF-8'?>"
OSM_VERSION = "0.6"
GENERATOR = "scenic-drive/etl.tagwriter"


def iter_top_level(path):
    """Every child of `<osm>`, in document order. The element is reused and cleared after the yield."""
    context = ET.iterparse(str(path), events=("start", "end"))
    _, root = next(context)
    depth = 1
    for event, elem in context:
        if event == "start":
            depth += 1
            continue
        depth -= 1
        if depth == 1:
            yield elem
            root.clear()


def tags_of(elem) -> dict:
    """The element's OSM tags as a dict. An OSM key is unique per object, so a dict loses nothing."""
    return {child.get("k"): child.get("v") for child in elem.findall(TAG)}


def refs_of(elem) -> list:
    """A way's node ids, in order."""
    return [int(child.get("ref")) for child in elem.findall(ND)]


def add_tags(elem, tags: dict) -> None:
    """Append tags to an element, in the order given. REFUSES a key the element already carries.

    Refuses rather than replaces because the only way that happens is a second pass over an already-written
    file, and an OSM object with two values for one key is not a file any consumer can be trusted to read
    the same way twice.
    """
    present = tags_of(elem)
    for key, value in tags.items():
        if key in present:
            raise ValueError("%s %s already carries %s=%s"
                             % (elem.tag, elem.get("id"), key, present[key]))
        ET.SubElement(elem, TAG, {"k": key, "v": str(value)})


def strip_whitespace(elem) -> None:
    """Drop every text node, so the output's shape comes from this writer and not from the input's layout."""
    elem.text = None
    elem.tail = None
    for child in elem:
        strip_whitespace(child)


class Writer:
    """An `<osm>` document written one element at a time. Use it as a context manager."""

    def __init__(self, path, generator: str = GENERATOR):
        self.path = Path(path)
        self.generator = generator
        self.handle = None
        self.written = 0

    def __enter__(self) -> "Writer":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" on purpose: this file is written on Windows and read by osmium in Linux, and a CR is
        # a byte the two runs of a byte-identical check would not agree about across boxes.
        self.handle = self.path.open("w", encoding="utf-8", newline="\n")
        self.handle.write(XML_DECLARATION + "\n")
        self.handle.write('<osm version="%s" generator="%s">\n' % (OSM_VERSION, self.generator))
        return self

    def write(self, elem) -> None:
        strip_whitespace(elem)
        self.handle.write(ET.tostring(elem, encoding="unicode") + "\n")
        self.written += 1

    def __exit__(self, *exc_info) -> bool:
        self.handle.write("</osm>\n")
        self.handle.close()
        self.handle = None
        return False
