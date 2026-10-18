#!/usr/bin/env python3
"""P-SAFE-03 and P-ATTR-01: the views the sheet and the chip band MOUNT, frozen whole (T-0408, rv1-t-0408 B1).

check-safety-disclaimer-frozen freezes ScenicHomeScreen's sheetSummary, chips, sheetDetails, mapControls,
settingsButton and gatedHandoff as whole-line whitelists. That froze the LINES that mount a view and not the view:
`.frame(minHeight: 3000)` inside DriveOptionMeta, `.padding(.bottom, 3000)` inside DriveRows and `.frame(height:
2000)` inside DriveSelector pushed the button, the conditions line, the credit and the sheet off the screen with
every limb green and only the routine sha256 re-approval in -pinned. So this is a CLOSURE over WHITELISTS:

  FROZEN  every type in ops/lib/check-safety-disclaimer-frozen-views.txt (`@@ TypeName FileName` then the file's
          kept lines) is frozen WHOLE FILE: the file's kept lines are exactly the approved ones, imports included.
  CLOSED  every capitalised identifier on a root block's lines or on a frozen file's lines (string literals removed,
          import lines skipped) is a frozen type, a SYSTEM name (SwiftUI or the standard library; our tree may not
          declare it - a shadow), or an OURS name (a non-view type of ours: declared somewhere in the Swift trees, and
          no declaration or extension header of it, read up to its `{`, names View, and no typealias of it). Any
          other name - a NEW view mounted in sheetSummary, a frozen view's new child - is refused by name until it
          is frozen whole or classified here, in the same commit, where a reviewer reads it.
  REACHED every frozen type is named on a root line or a reached frozen file's line: the list is the mounted set.

Kept lines: trailing CR stripped, spaces and tabs trimmed, blank lines kept; only a line whose trimmed text STARTS
with // is dropped (source guards fail closed: nothing is cut inside a line).

WHAT IT CANNOT SEE: views injected as closures rather than named (SurpriseGateSlot's `card`, built by the frozen app
shell from FeatureSurpriseMe); a lowercase member a root names that is not itself a frozen block; modifiers
overloaded by an extension elsewhere (check-file-scope's depth-0 whitelist, T-0406); whether anything RENDERS.

    python ops/lib/frozen_views.py FEATURE_DIR APP_TREE          # reasons on stdout, exit 1 when any
    python ops/lib/frozen_views.py FEATURE_DIR APP_TREE --print T:F ...   # emit approved sections from the tree
"""
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
APPROVED = REPO / "ops/lib/check-safety-disclaimer-frozen-views.txt"
SCREEN = "ScenicHomeScreen.swift"
ROOTS = [
    "private var sheetSummary: some View {",
    "private var chips: some View {",
    "private var sheetDetails: some View {",
    "private var mapControls: some View {",
    "private var settingsButton: some View {",
    "private var gatedHandoff: GatedHandoffButton {",
]
SYSTEM = {
    "AnyLayout", "AnyView", "Binding", "Bool", "Button", "CGFloat", "Capsule", "Circle", "Color", "Environment",
    "ForEach", "HStack", "HStackLayout", "Image", "Int", "Logger", "Rectangle", "RoundedRectangle", "ScrollView",
    "Self", "State", "String", "Text", "UserDefaults", "VStack", "VStackLayout", "View", "Void",
}
OURS = {
    "Clipboard", "Copy", "Coordinate", "DesignTokens", "DriveCopy", "DriveMenu", "DriveMenuRow", "DriveRoute",
    "HandoffDrive", "OptionVia", "PlanPreview", "PostDriveAnswer", "PostDriveOpenModel", "PostDriveQuestion",
    "SkylineHandoff", "SurpriseGate",
}
STRING = re.compile(r'"(?:\\.|[^"\\])*"')
NAME = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")
DECL = re.compile(r"\b(struct|class|enum|actor|protocol|extension|typealias)\s+([A-Z][A-Za-z0-9_]*)\b([^{]*)")


def kept(path):
    out = []
    for raw in path.read_text(encoding="utf-8").split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        line = line.strip(" \t")
        if line.startswith("//"):
            continue
        out.append(line)
    if out and out[-1] == "":
        out.pop()
    return out


def block(lines, decl):
    at = [i for i, line in enumerate(lines) if line == decl]
    if len(at) != 1:
        return None, f"the root `{decl}` occurs {len(at)} time(s) in {SCREEN}, expected exactly 1"
    depth, got = 0, []
    for line in lines[at[0]:]:
        got.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            return got, None
    return None, f"the root `{decl}` never closes in {SCREEN}"


def approved():
    sections, current = {}, None
    for line in APPROVED.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        if line.startswith("@@ "):
            name, file = line[3:].split(" ", 1)
            current = sections.setdefault(name, (file, []))[1]
        elif current is not None:
            current.append(line)
    for _, lines in sections.values():
        while lines and lines[-1] == "":
            lines.pop()
    return sections


def names(lines):
    found = set()
    for line in lines:
        if line.startswith("import "):
            continue
        found.update(NAME.findall(STRING.sub('""', line)))
    return found


def declarations(trees):
    found = {}
    for tree in trees:
        for path in sorted(pathlib.Path(tree).rglob("*.swift")):
            text = "\n".join(kept(path))
            for kind, name, header in DECL.findall(text):
                found.setdefault(name, []).append((kind, header, path))
    return found


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    feature, app_tree = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    screen = kept(feature / SCREEN)
    if "--print" in argv:
        for spec in argv[argv.index("--print") + 1:]:
            name, file = spec.split(":")
            print(f"@@ {name} {file}")
            print("\n".join(kept(feature / file)))
        return 0
    bad, roots = [], []
    for decl in ROOTS:
        got, why = block(screen, decl)
        bad += [why] if why else []
        roots += got or []
    frozen = approved()
    for name, (file, want) in sorted(frozen.items()):
        path = feature / file
        if not path.is_file():
            bad.append(f"{name}: no such file {path}")
            continue
        got = kept(path)
        if got != want:
            diff = next((i for i in range(max(len(got), len(want)))
                         if (got[i] if i < len(got) else None) != (want[i] if i < len(want) else None)), 0)
            bad.append(f"{name} ({file}) is frozen whole: line {diff + 1} approved "
                       f"`{want[diff] if diff < len(want) else '<end of file>'}`, found "
                       f"`{got[diff] if diff < len(got) else '<end of file>'}`")
    decls = declarations([app_tree, REPO / "Sources"])
    reached, todo, where = set(), [("the roots", roots)], {}
    while todo:
        label, lines = todo.pop()
        for name in sorted(names(lines)):
            where.setdefault(name, label)
            if name in frozen:
                if name not in reached:
                    reached.add(name)
                    path = feature / frozen[name][0]
                    todo.append((name, kept(path) if path.is_file() else []))
            elif name not in SYSTEM and name not in OURS:
                bad.append(f"`{name}`, named in {label}, is neither frozen whole nor an approved non-view: a view "
                           f"mounted from the sheet or the chip band is frozen in {APPROVED.relative_to(REPO).as_posix()} first")
    for name in sorted(set(frozen) - reached):
        bad.append(f"{name} is frozen but no root reaches it: remove it from {APPROVED.relative_to(REPO).as_posix()}")
    for name in sorted(SYSTEM & set(decls)):
        for kind, _, path in decls[name]:
            if kind != "extension":
                bad.append(f"`{kind} {name}` in {path} shadows the system name the frozen views call")
    for name in sorted(OURS & set(where)):
        if not any(kind != "extension" for kind, _, _ in decls.get(name, [])):
            bad.append(f"`{name}` (approved non-view, named in {where[name]}) is declared nowhere in our trees")
        for kind, header, path in decls.get(name, []):
            if kind == "typealias" or re.search(r"\bView\b", header):
                bad.append(f"`{kind} {name}{header.rstrip()}` in {path}: an approved non-view may not be a View")
    for reason in bad:
        print(reason)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
