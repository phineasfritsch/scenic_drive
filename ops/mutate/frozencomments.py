#!/usr/bin/env python3
"""Mutation population for T-0407's rule (ops/lib/frozen_comments.py, called inside every frozen-block reader): a
/* */ comment that hides a frozen block while a twin draws instead is refused in every frozen file.

    python ops/mutate/frozencomments.py [--only R1,G7,C3,...]

The subject is a COPY of apps/ios at .build/mutate-frozencomments/ios (the tracked Swift must equal HEAD). Each row
mutates one frozen file of the copy, runs the SHIPPING reader that reads it - `require_frozen_blocks` (-frozen),
`require_preview_blocks` (-preview), `require_preview_wiring` (check-map-attribution's f4; `fail` records instead of
exiting, as each entry point's other limbs would `exit` first on a twin's duplicate lines), check-drive-display.py's
`frozen()` or check-estimate-badge.py's `check()` (its `{` blocks; its two one-line blocks live in SurpriseCard.swift,
which its `{` blocks already cover) - and restores the copy byte for byte. Before any row every reader must be silent on the pristine copy.
KILLED: a reader line names the mutated file with the block-comment reason. SILENT (printed, the main-red measure):
the reader refused nothing at all. R1 is rv2-t0405's mutant verbatim (PR #298): `/*` at the end of PlanPreviewCard's
typeSize line, `*/` at the start of titleRow's, a twin `var body: some View{` drawing title, ETA, why line and
hazards above it, no map and no PlanPreviewActions; swiftc compiles that shape (T-0407 Log). G rows are generated:
each frozen block x {eol: `/*` at the end of the code line above the approved ABOVE line (rv2's shape); own: `/*` on a
line of its own above ABOVE; first: `/*` opening on the block's first line; nested: `/* /* */` at the end of that
line, which a non-nesting reader would think closed} x {twin before the opener, twin after the closer}; the twin is
the block with its first line respaced (` {` -> `{`) so the reader's count of the approved line stays 1,
preceded by every other line the comment hides (an ABOVE `}` among them) so braces balance and the lexer reads it. Generated
rows exercise the guard, not the compiler. C rows are CONTROLS on each frozen file: `"/*"` in a string and `/*` in a
// line are not block comments and must NOT be refused by this rule. R2 and the T rows are the pre-review pass's M1
(T-0407 Log): the opener sits in a // tail (` // see below /*`, or a `// /*` line of its own), which neither swiftc nor
the lexer reads as a comment, and the `*/` below is a stray closer - R2 is R1 so spelled, T rows are each block x the
twin before/after; they are KILLED when the stray `*/` is refused. The floor is the literal MIN_MUTATIONS.
Exit 0 every row killed (controls passed) and at least MIN_MUTATIONS ran; 1 a survivor; 2 cannot tell; 64 --only.
Classified in ops/lib/mutate_population_table.py PROBES: its subject lives in ops/lib, outside MODULE_ROOTS.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import mutate_only  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / ".build" / "mutate-frozencomments" / "ios"
MIN_MUTATIONS = 292
REASON = "a /* */ block comment in a frozen file"
S = "Packages/ScenicApp/Sources/"
H, P = S + "FeatureScenicHome/", S + "FeaturePlanSheet/"
# (file under apps/ios, reader, the reader's approved array). The first line of each block is READ from that array
# (bash) or from drive_display_frozen.BLOCKS, never retyped here, so the population follows the readers' whitelists.
BLOCKS_BASH = (
    (H + "HomeSheet.swift", "frozen", "FROZEN_HOME_SHEET"),
    (H + "ScenicHomeScreen.swift", "frozen", "FROZEN_SCREEN_BODY"),
    (H + "ScenicHomeScreen.swift", "frozen", "FROZEN_CHIPS"),
    (H + "ScenicHomeScreen.swift", "frozen", "FROZEN_SHEET_DETAILS"),
    (H + "ScenicHomeScreen.swift", "frozen", "FROZEN_CONDITIONS"),
    ("ScenicDrive/ScenicDriveApp.swift", "frozen", "FROZEN_APP_SHELL"),
    (P + "PlanPreviewCard.swift", "preview", "FROZEN_PREVIEW_CARD_BODY"),
    (P + "PlanPreviewCard.swift", "preview", "FROZEN_PREVIEW_ETA_ROW"),
    (P + "PlanPreviewCard.swift", "preview", "FROZEN_PREVIEW_ESTIMATE_TAG"),
    (P + "PlanPreviewActions.swift", "preview", "FROZEN_PREVIEW_ACTIONS_BODY"),
    (P + "PlanPreviewActions.swift", "preview", "FROZEN_PREVIEW_CONDITIONS"),
    (H + "PlanPreviewMap.swift", "f4", "FROZEN_PREVIEW_MAP"),
    (P + "PlanSheetScreen.swift", "f4", "FROZEN_PLAN_BODY"),
    (P + "PlanSheetScreen.swift", "f4", "FROZEN_PLAN_CONTENT"),
    (P + "PlanSheetScreen.swift", "f4", "FROZEN_PLAN_SWITCH"),
)
LIBS = ("ops/lib/check-safety-disclaimer-frozen", "ops/lib/check-safety-disclaimer-preview",
        "ops/lib/check-map-attribution-preview")


def load_blocks() -> tuple[tuple[str, str, str], ...]:
    """(file, reader, first line) for every frozen block, the bash ones read from the sourced arrays."""
    script = "".join(f". {lib}; " for lib in LIBS) + 'for a in "$@"; do declare -n r="$a"; printf "%s\\n" "${r[0]}"; done'
    names = [a for _, _, a in BLOCKS_BASH]
    done = subprocess.run(["bash", "-c", script, "blocks", *names], cwd=ROOT, capture_output=True, text=True)
    firsts = done.stdout.split("\n")[:len(names)]
    if done.returncode != 0 or len(firsts) != len(names) or not all(firsts):
        raise CannotTell(f"cannot read the readers' arrays: exit {done.returncode} {done.stderr.strip()[:200]}")
    spec = importlib.util.spec_from_file_location("drive_display_frozen", ROOT / "ops/lib/drive_display_frozen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    drive = tuple((rel, "drive", want[0]) for _, rel, _, want in mod.BLOCKS)
    if len(drive) != 3:
        raise CannotTell(f"drive_display_frozen.BLOCKS holds {len(drive)} blocks, this population was built for 3")
    badge = tuple((rel, "estimate", decl) for rel, decl in estimate_reader().BLOCKS if decl.endswith(" {"))
    if len(badge) != 8:
        raise CannotTell(f"check-estimate-badge.py has {len(badge)} `{{` blocks, this population was built for 8")
    return tuple((rel, reader, first) for (rel, reader, _), first in zip(BLOCKS_BASH, firsts)) + drive + badge


def estimate_reader():
    spec = importlib.util.spec_from_file_location("check_estimate_badge", ROOT / "ops/lib/check-estimate-badge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
BASH = {"frozen": '. ops/lib/check-safety-disclaimer-frozen; fail() { printf "FAIL| %s\\n" "$@"; }; '
                  f'require_frozen_blocks "$W/{H.rstrip("/")}" "$W"',
        "preview": '. ops/lib/check-safety-disclaimer-frozen; . ops/lib/check-safety-disclaimer-preview; '
                   'fail() { printf "FAIL| %s\\n" "$@"; }; require_preview_blocks "$W"',
        "f4": '. ops/lib/check-safety-disclaimer-frozen; . ops/lib/check-map-attribution-sites; '
              '. ops/lib/check-map-attribution-preview; fail() { printf "FAIL| %s\\n" "$@"; }; APP_TREE="$W"; '
              'mapfile -t sw < <(find "$W" -name "*.swift" | LC_ALL=C sort); require_preview_wiring -- "${sw[@]}"'}
TWIN_R1 = ["    var body: some View{", "        VStack(alignment: .leading, spacing: 12) {", "            titleRow",
           "            etaRow", "            Text(preview.whyLine)", "            hazardStrip", "        }", "    }"]


class CannotTell(Exception):
    pass


def code(line: str) -> bool:
    t = line.strip()
    return bool(t) and not t.startswith("//")


def locate(lines: list[str], first: str) -> tuple[int, int, int, int | None]:
    """(first line, last line, the ABOVE line, the code line above ABOVE) of the block, as raw indexes."""
    at = [i for i, ln in enumerate(lines) if ln.strip() == first]
    if len(at) != 1:
        raise CannotTell(f"`{first}` occurs {len(at)} time(s) in the pristine copy, expected 1 (BLOCKS is stale)")
    a, depth = at[0], 0
    for b in range(a, len(lines)):
        if code(lines[b]):
            depth += lines[b].count("{") - lines[b].count("}")
            if depth <= 0:
                break
    p = next(i for i in range(a - 1, -1, -1) if code(lines[i]))
    q = next((i for i in range(p - 1, -1, -1) if code(lines[i])), None)
    return a, b, p, q


def generated(rel: str, first: str, lines: list[str], place: str, twin_at: str) -> list[str]:
    a, b, p, q = locate(lines, first)
    if not lines[a].endswith(" {"):
        raise CannotTell(f"`{first}` does not end in ` {{`, so no twin spelling is generated for it")
    # The twin repeats every line the comment hides: the lines between the opener and the block (an ABOVE line
    # `}` closing the member before it among them) and the block, its first line respaced - so braces still balance.
    # A tail opener hides nothing (it is a // comment), so its twin is the block alone.
    hidden = a if place in ("first", "tail") else p if place == "own" or q is None else q + 1
    twin = lines[hidden:a] + [lines[a][:-2] + "{"] + lines[a + 1:b + 1]
    out = list(lines)
    out.insert(b + 1, "*/")
    if place == "own" or (place in ("eol", "nested", "tail") and q is None):
        out.insert(p, {"nested": "/* /* */", "tail": "// /*"}.get(place, "/*"))
        opener = p
    elif place == "first":
        out[a] = lines[a].replace(first, "/* " + first)
        opener = a
    else:
        out[q] += {"eol": " /*", "nested": " /* /* */", "tail": " // see below /*"}[place]
        opener = q
    closer = out.index("*/", b + 1)
    if twin_at == "after":
        return out[:closer + 1] + twin + out[closer + 1:]
    return out[:opener] + twin + out[opener:]


def rows(blocks, files) -> list[tuple[str, str, str, object]]:
    out = [("R1", P + "PlanPreviewCard.swift", "preview", "r1")]
    for rel, reader, first in blocks:
        for place in ("eol", "own", "first", "nested"):
            for twin_at in ("before", "after"):
                out.append((f"G{len(out)}", rel, reader, (first, place, twin_at)))
    for rel, reader in files:
        for k, add in enumerate(('let frozenCommentControl = "/* not a comment */"', "// /* a line comment, not a block")):
            out.append((f"C{len(out)}", rel, reader, ("control", add)))
    out.append(("R2", P + "PlanPreviewCard.swift", "preview", "r2"))
    for rel, reader, first in blocks:
        for twin_at in ("before", "after"):
            out.append((f"T{len(out)}", rel, reader, (first, "tail", twin_at)))
    return out


def apply(row, lines: list[str]) -> list[str]:
    mid, rel, _, spec = row
    if spec in ("r1", "r2"):
        ts = [i for i, ln in enumerate(lines) if ln.strip() == "@Environment(\\.dynamicTypeSize) private var typeSize"]
        tr = [i for i, ln in enumerate(lines) if ln.strip() == "private var titleRow: some View {"]
        if len(ts) != 1 or len(tr) != 1:
            raise CannotTell("R1/R2's typeSize or titleRow line is not once in PlanPreviewCard.swift")
        out = list(lines)
        out[ts[0]] += " /*" if spec == "r1" else " // see titleRow /*"
        out[tr[0]] = out[tr[0]].replace("private var titleRow", "*/ private var titleRow")
        return out[:ts[0]] + TWIN_R1 + out[ts[0]:]
    if spec[0] == "control":
        return lines[:-1] + [spec[1]] + lines[-1:] if lines and lines[-1] == "" else lines + [spec[1]]
    return generated(rel, spec[0], lines, spec[1], spec[2])


def run_reader(reader: str) -> str:
    if reader == "drive":
        spec = importlib.util.spec_from_file_location("check_drive_display", ROOT / "ops/lib/check-drive-display.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return "\n".join(mod.frozen(WORK))
    if reader == "estimate":
        mod = estimate_reader()
        try:
            mod.check(WORK)
        except mod.Refusal as refusal:
            return str(refusal)
        return ""
    env = {**os.environ, "W": WORK.as_posix()}
    done = subprocess.run(["bash", "-c", BASH[reader]], cwd=ROOT, env=env, capture_output=True, text=True)
    if done.returncode != 0:
        raise CannotTell(f"the {reader} reader exited {done.returncode}: {done.stderr.strip()[:300]}")
    return "\n".join(ln[6:] for ln in done.stdout.splitlines() if ln.startswith("FAIL| "))


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    try:
        blocks = load_blocks()
    except CannotTell as e:
        print(f"MUTATE cannot tell  {e}")
        return 2
    files = tuple(dict.fromkeys((rel, reader) for rel, reader, _ in blocks))
    population = rows(blocks, files)
    only = mutate_only.select_only(argv, [r[0] for r in population])
    if len(argv) > 1 and only is None:
        print("MUTATE refuse  usage: python ops/mutate/frozencomments.py [--only R1,G7,C3]")
        return 2
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "apps/ios"], capture_output=True, text=True, cwd=ROOT)
    if dirty.returncode != 0 or dirty.stdout.strip():
        print(f"MUTATE refuse  apps/ios differs from HEAD; commit or stash first:\n{dirty.stdout}")
        return 2
    shutil.rmtree(WORK.parent, ignore_errors=True)
    shutil.copytree(ROOT / "apps" / "ios", WORK, ignore=shutil.ignore_patterns(".build", "DerivedData*", "*.xcassets"))
    picked = [r for r in population if only is None or r[0] in only]
    survivors, silent = [], []
    try:
        for reader in dict.fromkeys(r for _, r in files):
            if out := run_reader(reader):
                raise CannotTell(f"the {reader} reader is not silent on the pristine copy:\n{out}")
        for row in picked:
            mid, rel, reader, spec = row
            path = WORK / rel
            before = path.read_bytes()
            path.write_bytes("\n".join(apply(row, before.decode("utf-8").split("\n"))).encode("utf-8"))
            try:
                out = run_reader(reader)
            finally:
                path.write_bytes(before)
            named = [ln for ln in out.splitlines() if f"{path.name} line " in ln and REASON in ln]
            control = isinstance(spec, tuple) and spec[0] == "control"
            what = "control" if control else (spec if spec in ("r1", "r2") else "/".join(spec[1:]))
            if control:
                ok = not named
            else:
                ok = bool(named)
                if not out:
                    silent.append(mid)
            print(f"MUTATE {'killed' if ok and not control else 'passed' if ok else 'SURVIVED'}  {mid} {rel.split('/')[-1]}"
                  f" {what}{'' if out else ' (reader silent)'}")
            if not ok:
                survivors.append(mid)
    except CannotTell as e:
        print(f"MUTATE cannot tell  {e}")
        return 2
    shutil.rmtree(WORK.parent, ignore_errors=True)
    print(f"MUTATE silent  {len(silent)} row(s) no reader refused at all: {' '.join(silent) or 'none'}")
    if survivors or (only is None and len(picked) < MIN_MUTATIONS):
        print(f"MUTATE FAIL  survivors {survivors}; ran {len(picked)}, floor {MIN_MUTATIONS}")
        return 1
    print(f"MUTATE ok  {len(picked)}/{len(picked)} killed or passed (floor {MIN_MUTATIONS}, population "
          f"{len(population)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
