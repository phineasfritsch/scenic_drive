"""P-SAFE-03 (T-0336 R4): every `-screen` rehearsal is DEBUG-only - a release build opens on home and carries no
rehearsal state.

ios-screenshot opens each screen with a `-screen <name>` launch argument, read from UserDefaults' argument domain by a
feature type (LaunchScreen, SurpriseSlot, DriveRehearsal, PlanRehearsal, OnboardingRehearsal). A read outside
`#if DEBUG` would let a release build open on a plan preview that no planner produced, past onboarding's disclaimer.

A WHITELIST of whole lines, never a scan for bad spellings: every line under apps/ios/**/*.swift that is not a `//`
comment and names `"screen"`, `PlanRehearsalFixtures` or `OnboardingRehearsal` - or `forKey: launchArgumentKey` in a
file whose `launchArgumentKey` is `"screen"` - must be an APPROVED (file, line) site, as many times as approved; a site
marked DEBUG must sit inside an `#if DEBUG` arm (an `#else` arm is not); and PlanRehearsalFixtures.swift must be
wholly inside one `#if DEBUG`. `--prove-red` applies each mutation alone, in memory, and every one must be refused.
"""
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = "apps/ios"
SRC = "apps/ios/Packages/ScenicApp/Sources/"
FIXTURES = SRC + "FeaturePlanSheet/PlanRehearsalFixtures.swift"
TOKENS = ('"screen"', "PlanRehearsalFixtures", "OnboardingRehearsal")
KEY_DEF = 'static let launchArgumentKey = "screen"'
KEY_READ = "forKey: launchArgumentKey"

# (file, stripped line) -> (count, must be inside #if DEBUG)
APPROVED = {
    (SRC + "Entitlements/LaunchScreen.swift", KEY_DEF): (1, False),
    (SRC + "Entitlements/LaunchScreen.swift",
     "return UserDefaults.standard.string(forKey: launchArgumentKey).flatMap(LaunchScreen.init(rawValue:)) ?? .home"):
        (1, True),
    (SRC + "FeatureScenicHome/SurpriseSlot.swift", KEY_DEF): (1, False),
    (SRC + "FeatureScenicHome/SurpriseSlot.swift",
     "return UserDefaults.standard.string(forKey: launchArgumentKey) == launchValue"): (1, True),
    (SRC + "FeatureScenicHome/DriveRehearsal.swift",
     'guard UserDefaults.standard.string(forKey: "screen") == "drive" else { return nil }'): (2, True),
    (SRC + "FeatureScenicHome/OnboardingRehearsal.swift", "enum OnboardingRehearsal {"): (1, False),
    (SRC + "FeatureScenicHome/OnboardingRehearsal.swift",
     'if UserDefaults.standard.string(forKey: "screen") == "disclaimer" {'): (1, True),
    (SRC + "FeatureScenicHome/SafetyDisclaimer.swift", "@State private var onboarding = OnboardingRehearsal.atLaunch"):
        (1, False),
    (SRC + "FeaturePlanSheet/PlanRehearsal.swift",
     'return UserDefaults.standard.string(forKey: "screen").flatMap(PlanRehearsalFixtures.rehearsal(named:))'):
        (1, True),
    (FIXTURES, "enum PlanRehearsalFixtures {"): (1, True),
}


def debug_states(text):
    """(stripped line, inside an #if DEBUG arm) for every line; directives themselves are reported False."""
    stack, out = [], []
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("#if"):
            stack.append(line == "#if DEBUG")
            out.append((line, False))
            continue
        if line.startswith("#else") or line.startswith("#elseif"):
            if stack:
                stack[-1] = False
            out.append((line, False))
            continue
        if line.startswith("#endif"):
            if stack:
                stack.pop()
            out.append((line, False))
            continue
        out.append((line, any(stack)))
    return out


def check(files):
    """files: {relative path: text}. Returns the refusals, one line each; empty means green."""
    errs, seen = [], collections.Counter()
    for path in sorted(files):
        states = debug_states(files[path])
        reads_key = any(KEY_DEF in line for line, _ in states)
        for line, in_debug in states:
            if line.startswith("//"):
                continue
            if not (any(t in line for t in TOKENS) or (reads_key and KEY_READ in line)):
                continue
            seen[(path, line)] += 1
            approved = APPROVED.get((path, line))
            if approved is None:
                errs.append(f"P-SAFE-03 (rehearsal): `{line}` at {path} is not an approved -screen site")
            elif approved[1] and not in_debug:
                errs.append(f"P-SAFE-03 (rehearsal): `{line}` at {path} reads the -screen argument outside #if DEBUG")
    for (path, line), (count, _) in APPROVED.items():
        if seen[(path, line)] != count:
            errs.append(f"P-SAFE-03 (rehearsal): `{line}` at {path} occurs {seen[(path, line)]} time(s), approved {count}")
    fixtures = files.get(FIXTURES)
    if fixtures is None:
        errs.append(f"P-SAFE-03 (rehearsal): {FIXTURES} is gone")
    else:
        body = [(l, d) for l, d in debug_states(fixtures) if l]
        if not body or body[0][0] != "#if DEBUG" or body[-1][0] != "#endif" or \
                any(not d for l, d in body[1:-1] if not l.startswith("#")):
            errs.append(f"P-SAFE-03 (rehearsal): {FIXTURES} is not wholly inside one #if DEBUG - a release build carries it")
    return errs


def load():
    return {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted((ROOT / APP).rglob("*.swift"))}


def mutations(files):
    def edit(path, old, new, count=1):
        def apply(f):
            assert f[path].count(old) >= 1, (path, old)
            g = dict(f)
            g[path] = f[path].replace(old, new, count)
            return g
        return apply

    def add(path, text):
        def apply(f):
            g = dict(f)
            g[path] = text
            return g
        return apply

    shell = "apps/ios/ScenicDrive/ScenicDriveApp.swift"
    return [
        ("LaunchScreen's read outside DEBUG", edit(SRC + "Entitlements/LaunchScreen.swift", "#if DEBUG\n", "#if true\n")),
        ("SurpriseSlot's read outside DEBUG", edit(SRC + "FeatureScenicHome/SurpriseSlot.swift", "#if DEBUG\n", "")),
        ("DriveRehearsal's first read outside DEBUG",
         edit(SRC + "FeatureScenicHome/DriveRehearsal.swift", "#if DEBUG\n", "")),
        ("PlanRehearsal's read outside DEBUG", edit(SRC + "FeaturePlanSheet/PlanRehearsal.swift", "#if DEBUG\n", "")),
        ("PlanRehearsal's read moved to the #else arm", edit(SRC + "FeaturePlanSheet/PlanRehearsal.swift",
                                                           "#if DEBUG\n", "#if !DEBUG\n")),
        ("OnboardingRehearsal's read outside DEBUG",
         edit(SRC + "FeatureScenicHome/OnboardingRehearsal.swift", "#if DEBUG\n", "")),
        ("the fixtures compiled in release", edit(FIXTURES, "#if DEBUG\n", "")),
        ("the fixtures' #if DEBUG closed early", edit(FIXTURES, "enum PlanRehearsalFixtures {", "#endif\nenum PlanRehearsalFixtures {")),
        ("the shell reads -screen itself", edit(shell, "@main\n", "let rehearsal = UserDefaults.standard.string(forKey: \"screen\")\n@main\n")),
        ("a new feature file reads -screen", add(SRC + "FeaturePlanSheet/PlanTour.swift",
                                                 "let tour = UserDefaults.standard.string(forKey: \"screen\")\n")),
        ("the fixtures used from the shell", edit(shell, "@main\n", "let fixture = PlanRehearsalFixtures.preview\n@main\n")),
        ("T-0334's offer sample named outside DEBUG (a release plan-offered state)",
         edit(SRC + "FeaturePlanSheet/PlanRehearsal.swift", "public struct PlanRehearsal {\n",
              "public struct PlanRehearsal {\n    static let offered = PlanRehearsalFixtures.offer\n")),
    ]


def main(argv):
    files = load()
    if "--prove-red" in argv:
        bad = 0
        if check(files):
            print("PROVE-RED FAIL: the shipped tree is not green"); return 1
        rows = mutations(files)
        for name, apply in rows:
            errs = check(apply(files))
            print(f"[{'refused' if errs else 'GREEN'}] {name}: {errs[0] if errs else 'nothing refused'}")
            bad += not errs
        if bad:
            print(f"PROVE-RED FAIL: {bad}/{len(rows)} mutations green"); return 1
        print(f"PROVE-RED OK: {len(rows)}/{len(rows)} refused by name"); return 0
    errs = check(files)
    for e in errs:
        print(e)
    if errs:
        print(f"P-SAFE-03 (rehearsal) FAIL: {len(errs)} refusal(s)"); return 1
    print(f"P-SAFE-03 (rehearsal): {sum(c for c, _ in APPROVED.values())} approved -screen sites, every read inside "
          f"#if DEBUG, {FIXTURES.rsplit('/', 1)[-1]} wholly DEBUG-only")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
