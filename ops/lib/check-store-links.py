"""P-STORE-01, the source half (T-0271): the paywall and Settings carry what App Review 3.1.2 asks for.

    python ops/lib/check-store-links.py              the shipped tree; exit 0 green, 1 naming every refusal
    python ops/lib/check-store-links.py --prove-red  each named mutant applied ALONE to a copy, each refused BY NAME,
                                                     and each legitimate edit still green; exit 0 only if all hold

WHAT IT DECIDES, over the Swift source - fail closed, whole-line WHITELISTS keyed on identifiers, never on a comment
(CLAUDE.md; memory source-guards-fail-closed). Every line under apps/ios naming `SubscriptionStoreView`,
`restorePurchases`, `termsOfUseURL`, `privacyPolicyURL`, `AppStore.sync()`, `manageSubscriptionsSheet`, the screens'
constructors, `onSettings` or `import Entitlements` is one of the approved (file, whole line) pairs in
store_links_pinned.py, with multiplicity; every `import`, `accessibilityIdentifier`, `#` directive and
`UserDefaults` line under Sources/Entitlements likewise; the store view's modifier chain with the inset that mounts
the links, Settings' List of sections, the shell's Settings sheet and the DEBUG fence are runs of consecutive
non-blank lines; Sources/Entitlements is frozen - exactly its five files, each matching an approved sha256 of its
non-blank kept lines, so a modifier that hides or disarms a control, a `/* */` block or a view extension there is
refused; and the in-app ODbL notice equals LICENSE-DATA's OpenStreetMap section line for line.

WHAT IT CANNOT SEE, so nobody reads more into a green than is there: whether any of it RENDERS or is reachable by a
tap (the XCUITest half, T-0180's, on the identifiers checked here); whether StoreKit loads products (no group exists
in App Store Connect - ruling R3); whether the URLs resolve; a modifier or extension OUTSIDE Sources/Entitlements
(DesignSystem, say) that changes what the frozen source draws.
"""
import hashlib
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store_links_pinned as pinned  # noqa: E402  (this directory is sys.path[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_REL = "apps/ios"


def kept_lines(path):
    """Every line: trailing CR stripped, trimmed, blank lines kept; only a line STARTING with // is dropped."""
    out = []
    for raw in path.read_text(encoding="utf-8").split("\n"):
        line = raw.rstrip("\r").strip()
        if not line.startswith("//"):
            out.append(line)
    return out


def population(root, rel):
    pop = []
    for path in sorted((root / rel).rglob("*.swift")):
        pop.extend((path.relative_to(root).as_posix(), line) for line in kept_lines(path))
    return pop


def whitelist(needle, pop, approved, bad):
    extra = sorted((f, line) for f, line in pop if needle in line)
    missing = []
    for item in sorted(approved):
        if item in extra:
            extra.remove(item)
        else:
            missing.append(item)
    bad.extend(f"{needle}: the approved line is missing from {f}: `{line}`" for f, line in missing)
    bad.extend(f"{needle}: an unapproved line in {f}: `{line}`" for f, line in extra)


def sequences(root, bad):
    for label, rel, run in pinned.SEQUENCES:
        path = root / rel
        kept = [line for line in kept_lines(path) if line] if path.is_file() else []
        hits = sum(kept[i:i + len(run)] == run for i in range(len(kept)))
        if hits != 1:
            bad.append(f"{label}: the run `{' / '.join(run)}` occurs {hits} time(s) in {rel}, expected exactly 1")


def frozen(root, bad):
    label = "the frozen Entitlements source"
    have = sorted(p.relative_to(root).as_posix() for p in (root / pinned.ENT).rglob("*.swift"))
    for rel in sorted(set(have) ^ set(pinned.FROZEN)):
        bad.append(f"{label}: {rel} is {'not an approved file' if rel in have else 'missing'}")
    for rel in sorted(set(have) & set(pinned.FROZEN)):
        text = "\n".join(line for line in kept_lines(root / rel) if line)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != pinned.FROZEN[rel]:
            bad.append(f"{label}: {rel}'s non-blank kept lines hash {digest}, approved {pinned.FROZEN[rel]} - a reviewed "
                       f"commit re-approves it in store_links_pinned.FROZEN")


def notice(root, bad):
    src = (root / "LICENSE-DATA").read_text(encoding="utf-8").replace("\r", "").split("\n")
    if src.count(pinned.NOTICE_HEADING) != 1:
        bad.append(f"ODbL notice: LICENSE-DATA has `{pinned.NOTICE_HEADING}` {src.count(pinned.NOTICE_HEADING)} times")
        return
    start = src.index(pinned.NOTICE_HEADING) + 1
    section = []
    for line in src[start:]:
        if not line.strip() or line.startswith("#"):
            break
        section.append(line)
    want = ['"' + line.replace("\\", "\\\\").replace('"', '\\"') + '",' for line in section]
    path = root / pinned.NOTICE_FILE
    kept = kept_lines(path) if path.is_file() else []
    if not section or kept.count(pinned.NOTICE_OPEN) != 1:
        bad.append(f"ODbL notice: `{pinned.NOTICE_OPEN}` must occur once in {pinned.NOTICE_FILE} over a non-empty "
                   f"LICENSE-DATA section ({len(section)} lines)")
        return
    at = kept.index(pinned.NOTICE_OPEN) + 1
    got = kept[at:at + len(want) + 1]
    if got != want + ["]"]:
        bad.append(f"ODbL notice: {pinned.NOTICE_FILE}'s odblNotice is not LICENSE-DATA's "
                   f"`{pinned.NOTICE_HEADING}` section line for line (then `]`): found {got}")


def run(root):
    bad = []
    app = population(root, APP_REL)
    ent = population(root, pinned.ENT)
    for needle, approved in pinned.APP_WIDE.items():
        whitelist(needle, app, approved, bad)
    for needle, approved in pinned.ENTITLEMENTS.items():
        whitelist(needle, ent, approved, bad)
    sequences(root, bad)
    frozen(root, bad)
    notice(root, bad)
    return bad


def copy_tree(dest):
    for path in (ROOT / APP_REL).rglob("*.swift"):
        target = dest / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    shutil.copyfile(ROOT / "LICENSE-DATA", dest / "LICENSE-DATA")


def prove_red():
    if run(ROOT):
        print("check-store-links --prove-red: the shipped tree is not green; fix that first")
        return 1
    failures = 0
    rows = [(r, True) for r in pinned.MUTATIONS] + [(r, False) for r in pinned.STILL_GREEN]
    for (name, rel, old, new, reason), must_fail in rows:
        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp)
            copy_tree(dest)
            path = dest / rel
            if old is None:
                if path.exists():
                    print(f"  HARD FAIL  {name}: {rel} already exists")
                    failures += 1
                    continue
                path.write_text(new, encoding="utf-8", newline="\n")
            else:
                text = path.read_text(encoding="utf-8") if path.is_file() else ""
                if text.count(old) != 1:
                    print(f"  HARD FAIL  {name}: its anchor occurs {text.count(old)} times in {rel}, not once")
                    failures += 1
                    continue
                path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
            bad = run(dest)
        if must_fail:
            named = [b for b in bad if b.startswith(reason + ":")]
            ok = bool(named)
            print(f"  {'RED  ' if ok else 'MISSED'}  {name}" + (f"  <- {named[0]}" if ok else f"  (refusals: {bad})"))
        else:
            ok = not bad
            print(f"  {'GREEN' if ok else 'BROKE'}  {name}" + ("" if ok else f"  (refusals: {bad})"))
        failures += 0 if ok else 1
    total = len(rows)
    print(f"check-store-links --prove-red: {total - failures}/{total} rows as required "
          f"({len(pinned.MUTATIONS)} mutants refused by name, {len(pinned.STILL_GREEN)} legitimate edits green)")
    return 1 if failures else 0


def main(argv):
    if argv[1:] == ["--prove-red"]:
        return prove_red()
    if argv[1:]:
        print("usage: check-store-links.py [--prove-red]")
        return 2
    bad = run(ROOT)
    if bad:
        print(f"P-STORE-01 (ops/lib/check-store-links.py): {len(bad)} refusal(s)")
        for line in bad:
            print("  " + line)
        return 1
    print("P-STORE-01 source half: paywall and Settings links, Restore, SubscriptionStoreView and the ODbL notice "
          "at exactly their approved sites, mounted, in a frozen Entitlements module")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
