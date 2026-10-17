"""Glyphs and sprites for the basemap's labels: pinned, built beside la.pmtiles, checked against the styles.

    python services/tiles/basemap_assets.py build --work services/tiles/work [--archive TARBALL]
    python services/tiles/basemap_assets.py check --work services/tiles/work
    python services/tiles/basemap_assets.py publish-list --work services/tiles/work

Every font stack and sprite sheet the committed styles name is computed FROM the styles and compared whole to
what is on disk: a stack the style names with no glyph directory is refused, and so is a directory no style
names. A glyphs URL whose files do not exist renders no labels while claiming it has them; this is the check
that the claim and the files agree. `ops/publish-tiles` runs `check` and then uploads exactly `publish-list`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = HERE / "basemap_assets.json"
STYLES = HERE / "styles"
APPEARANCES = ("light", "dark")
# MapLibre requests glyphs in 256-codepoint ranges over the Basic Multilingual Plane: 0-255 ... 65280-65535.
RANGES = tuple(f"{start}-{start + 255}" for start in range(0, 65536, 256))
SPRITE_SUFFIXES = (".json", ".png", "@2x.json", "@2x.png")
LICENCE = "glyphs/OFL.txt"


def committed_styles(styles_dir: Path = STYLES) -> list[dict]:
    return [json.loads((styles_dir / f"scenic-{a}.json").read_text(encoding="utf-8")) for a in APPEARANCES]


def assets_base() -> str:
    sys.path.insert(0, str(HERE))
    from make_styles import ASSETS_BASE  # noqa: PLC0415 - same directory, no package

    return ASSETS_BASE


def served_path(url: str, base: str) -> str:
    """The path under the publish prefix a style URL names. A URL off the base is refused, never followed."""
    if not isinstance(url, str) or not url.startswith(base):
        raise ValueError(f"{url!r} is not served from {base!r} - no third-party URL in a committed style")
    return url[len(base):]


def literal_strings(value, what: str) -> list[str]:
    """A layout value that must be a literal so the whitelist can be computed. An expression fails closed."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
        return value
    raise ValueError(f"{what} {value!r} is not a literal; the asset whitelist cannot be computed from it")


def font_stacks(doc: dict) -> set[str]:
    """MapLibre requests a stack as its fonts joined by commas, so that string is the directory it needs."""
    out = set()
    for layer in doc.get("layers", []):
        if "text-font" in layer.get("layout", {}):
            out.add(",".join(literal_strings(layer["layout"]["text-font"], f"{layer['id']} text-font")))
    return out


def icon_names(doc: dict) -> set[str]:
    out = set()
    for layer in doc.get("layers", []):
        if "icon-image" in layer.get("layout", {}):
            out.update(literal_strings(layer["layout"]["icon-image"], f"{layer['id']} icon-image"))
    return out


def required_files(docs: list[dict], base: str) -> list[str]:
    """Every file the styles' glyphs and sprite URLs will request, as a path under the publish prefix."""
    out = set()
    for doc in docs:
        stacks = font_stacks(doc)
        if stacks:
            template = served_path(doc.get("glyphs"), base)
            if "{fontstack}" not in template or "{range}" not in template:
                raise ValueError(f"glyphs {doc.get('glyphs')!r} lacks {{fontstack}} or {{range}}")
            out.update(template.replace("{fontstack}", s).replace("{range}", r) for s in stacks for r in RANGES)
        if "sprite" in doc:
            sheet = served_path(doc["sprite"], base)
            out.update(sheet + suffix for suffix in SPRITE_SUFFIXES)
    return sorted(out)


def sheets(docs: list[dict], base: str) -> set[str]:
    return {served_path(doc["sprite"], base) for doc in docs if "sprite" in doc}


def tree_digest(work: Path) -> tuple[str, int, int]:
    """sha256 over `path<TAB>sha256` of every file under glyphs/ and sprites/, sorted; with count and bytes."""
    lines, count, size = [], 0, 0
    for path in sorted(p for d in ("glyphs", "sprites") for p in (work / d).rglob("*") if p.is_file()):
        data = path.read_bytes()
        lines.append(f"{path.relative_to(work).as_posix()}\t{hashlib.sha256(data).hexdigest()}\n")
        count, size = count + 1, size + len(data)
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest(), count, size


def check(work: Path, docs: list[dict], base: str, pin: dict) -> list[str]:
    """Every problem with the built assets against these styles; [] means the styles' URLs all resolve."""
    problems = []
    named_stacks = set().union(*(font_stacks(doc) for doc in docs))
    on_disk_stacks = {p.name for p in (work / "glyphs").iterdir() if p.is_dir()} if (work / "glyphs").is_dir() else set()
    if on_disk_stacks != named_stacks:
        problems.append(f"glyph stacks on disk {sorted(on_disk_stacks)} != named by the styles {sorted(named_stacks)}")
    absent = [rel for rel in required_files(docs, base) if not (work / rel).is_file()]
    if absent:
        problems.append(f"{len(absent)} requested file(s) not built, first {absent[0]}")
    on_disk_sheets = {p.relative_to(work).as_posix()[:-len(".json")] for p in (work / "sprites").rglob("*.json")
                      if not p.name.endswith("@2x.json")}
    named_sheets = sheets(docs, base)
    if on_disk_sheets != named_sheets:
        problems.append(f"sprite sheets on disk {sorted(on_disk_sheets)} != named by the styles {sorted(named_sheets)}")
    for doc in docs:
        if "sprite" not in doc:
            continue
        index = work / (served_path(doc["sprite"], base) + ".json")
        have = set(json.loads(index.read_text(encoding="utf-8"))) if index.is_file() else set()
        missing_icons = sorted(icon_names(doc) - have)
        if missing_icons:
            problems.append(f"{doc.get('name')}: icon-image(s) not in {index.name}: {missing_icons}")
    digest, _, _ = tree_digest(work)
    if digest != pin["tree_sha256"]:
        problems.append(f"tree digest {digest} != pinned {pin['tree_sha256']}")
    return problems


def fetch(pin: dict, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(pin["url"], timeout=120) as response, dest.open("wb") as out:  # noqa: S310
        shutil.copyfileobj(response, out)
    return dest


def build(work: Path, archive: Path, docs: list[dict], base: str, pin: dict) -> str:
    """Extract exactly the files the styles request (plus the font licence) out of the pinned archive."""
    data = archive.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != pin["sha256"] or len(data) != pin["bytes"]:
        raise ValueError(f"{archive.name}: sha256 {digest} / {len(data)} B != pinned {pin['sha256']} / {pin['bytes']} B")
    wanted = {}
    for rel in required_files(docs, base) + [LICENCE]:
        top, rest = rel.split("/", 1)
        wanted[("fonts/" if top == "glyphs" else "sprites/") + rest] = rel
    for directory in ("glyphs", "sprites"):
        shutil.rmtree(work / directory, ignore_errors=True)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            inner = member.name.split("/", 1)[-1]
            if member.isfile() and inner in wanted:
                target = work / wanted.pop(inner)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
    if wanted:
        raise ValueError(f"the pinned archive lacks {len(wanted)} file(s), e.g. {sorted(wanted)[0]}")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build, check and list the basemap glyphs and sprites.")
    parser.add_argument("command", choices=("build", "check", "publish-list"))
    parser.add_argument("--work", type=Path, required=True, help="the directory beside la.pmtiles")
    parser.add_argument("--archive", type=Path, help="the pinned tarball; fetched from the pin's url if absent")
    parser.add_argument("--styles", type=Path, default=STYLES)
    parser.add_argument("--pin", type=Path, default=PIN)
    args = parser.parse_args(argv)
    pin = json.loads(args.pin.read_text(encoding="utf-8"))
    docs, base = committed_styles(args.styles), assets_base()
    try:
        if args.command == "build":
            archive = args.archive or fetch(pin, args.work / f"basemap-assets-{pin['commit'][:7]}.tar.gz")
            build(args.work, archive, docs, base, pin)
        if args.command == "publish-list":
            print("\n".join(required_files(docs, base) + [LICENCE]))
            return 0
        problems = check(args.work, docs, base, pin)
    except (OSError, ValueError, KeyError) as error:
        print(f"basemap_assets: REFUSED: {error}", file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print(f"basemap_assets: REFUSED: {problem}", file=sys.stderr)
        return 1
    digest, count, size = tree_digest(args.work)
    stacks = sorted(set().union(*(font_stacks(d) for d in docs)))
    print(f"basemap_assets: OK {len(stacks)} font stack(s) {stacks} x {len(RANGES)} ranges, "
          f"{len(sheets(docs, base))} sprite sheet(s), {count} files {size} bytes, tree {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
