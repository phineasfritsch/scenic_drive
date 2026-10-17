"""P-SAFE-03 (T-0394 R6): the app reaches the Worker on ONE base URL, LiveBaseURL.url - the Info.plist value, or in a
DEBUG build the `-plan.base.url` launch argument - and no client reads a base URL any other way.

A WHITELIST of whole lines, never a scan for bad spellings: every line under apps/ios/**/*.swift that is not a `//`
comment and names the word `base`, `LiveBaseURL`, `APIBaseURL`, `plan.base.url`, `SCENIC_API_BASE_URL`,
`forInfoDictionaryKey`, `workers.dev` or `PlanHTTPRequest` must be an APPROVED (file, line) site, as many times as
approved. Every ScenicAPIClient and Telemetry client takes its URL as `base:`, so a client built on any other URL
names the word on an unapproved line. LiveBaseURL.swift's code lines are compared WHOLE to a typed list, the
override read must sit inside an `#if DEBUG` arm (an `#else` arm is not), and the release arm is `return nil`.
`--prove-red` applies each mutation alone, in memory, and every one must be refused.
"""
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = "apps/ios"
SRC = "apps/ios/Packages/ScenicApp/Sources/"
PA = SRC + "PlanAdapter/"
LIVE = PA + "LiveBaseURL.swift"
TOKEN = re.compile(r"\bbase\b|LiveBaseURL|APIBaseURL|plan\.base\.url|SCENIC_API_BASE_URL|forInfoDictionaryKey"
                   r"|workers\.dev|PlanHTTPRequest")
OVERRIDE_READ = "return UserDefaults.standard.string(forKey: APIBaseURL.overrideKey)"

# The whole of LiveBaseURL.swift's code, `//` lines and blank lines dropped, in order.
LIVE_BODY = [
    "import Foundation", "import ScenicAPIClient", "enum LiveBaseURL {",
    "static let url: URL? = APIBaseURL.resolve(bundled: bundled, override: debugOverride)",
    "private static var bundled: String? {", "Bundle.main.object(forInfoDictionaryKey: APIBaseURL.infoPlistKey) as? String",
    "}", "private static var debugOverride: String? {", "#if DEBUG", OVERRIDE_READ, "#else", "return nil", "#endif", "}",
    "}",
]

GUARD = "guard let base = LiveBaseURL.url else { return nil }"
# (file, stripped line) -> count
APPROVED = {
    (SRC + "MapAdapter/ScenicStyleDocument.swift", "let base = caches ?? FileManager.default.temporaryDirectory"): 1,
    (SRC + "MapAdapter/ScenicStyleDocument.swift",
     'return base.appending(path: "ScenicDrive/Styles", directoryHint: .isDirectory)'): 1,
    (LIVE, "enum LiveBaseURL {"): 1,
    (LIVE, "static let url: URL? = APIBaseURL.resolve(bundled: bundled, override: debugOverride)"): 1,
    (LIVE, "Bundle.main.object(forInfoDictionaryKey: APIBaseURL.infoPlistKey) as? String"): 1,
    (LIVE, OVERRIDE_READ): 1,
    (PA + "LiveCorpus.swift",
     'let build = Int(Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "") ?? 0'): 1,
    (PA + "LivePlanner.swift", 'AppBuild.parse(Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String)'): 1,
    (PA + "LiveAccountDeletion.swift", "guard let base = LiveBaseURL.url, let store = LiveSession.store"): 1,
    (PA + "LiveAccountDeletion.swift",
     "let client = AccountClient(base: base, transport: URLSessionPlanTransport(), session: store)"): 1,
    (PA + "LiveLoopPlanner.swift", "guard let base = LiveBaseURL.url else { return UnreachableLoopPlanner() }"): 1,
    (PA + "LiveLoopPlanner.swift",
     "let client = ClientLoopPlanner(client: LoopClient(base: base, transport: URLSessionPlanTransport(),"): 1,
    (PA + "LiveLoopPlanner.swift", "return TelemetryLoopPlanner(inner: ConfiguredLoopPlanner(planner: client, cache: "
                                   "LivePlanner.cache(base), appBuild: LivePlanner.appBuild))"): 1,
    (PA + "LivePlanner.swift", "guard let base = LiveBaseURL.url else { return NoPlaceSearch() }"): 1,
    (PA + "LivePlanner.swift",
     "return ClientPlaceSearch(client: SearchClient(base: base, transport: URLSessionPlanTransport(),"): 1,
    (PA + "LivePlanner.swift", "guard let base = LiveBaseURL.url else { return UnreachablePlanner() }"): 1,
    (PA + "LivePlanner.swift", "let cache = Self.cache(base)"): 1,
    (PA + "LivePlanner.swift", "return TelemetryRoutePlanner(inner: ConfiguredPlanner(planner: ClientPlanner(client: "
                               "client(base)), cache: cache,"): 1,
    (PA + "LivePlanner.swift", "guard let base = LiveBaseURL.url else { return SurpriseGate.of(RemoteConfig.bundled) }"): 1,
    (PA + "LivePlanner.swift", "return SurpriseGate.of(cache(base).kept)"): 1,
    (PA + "LivePlanner.swift", "static func cache(_ base: URL) -> ConfigCache {"): 1,
    (PA + "LivePlanner.swift", "ConfigCache(client: ConfigClient(base: base, transport: URLSessionPlanTransport()), "
                               "storage: DefaultsConfigStorage())"): 1,
    (PA + "LivePlanner.swift", "guard let base = LiveBaseURL.url, let continuation = preview.continuation else { "
                               "return RerouteUnavailable() }"): 1,
    (PA + "LivePlanner.swift", "return PlanRerouter(client: client(base), place: continuation.place, budgetMinutes: "
                               "continuation.budgetMinutes)"): 1,
    (PA + "LivePlanner.swift", "private static func client(_ base: URL) -> PlanClient {"): 1,
    (PA + "LivePlanner.swift",
     "PlanClient(base: base, transport: URLSessionPlanTransport(), installID: StoredInstallID(),"): 1,
    (PA + "LiveSession.swift", GUARD): 1,
    (PA + "LiveSession.swift",
     "return SessionStore(client: AttestClient(base: base, transport: URLSessionPlanTransport(),"): 1,
    (PA + "LiveSurpriseLedger.swift", GUARD): 1,
    (PA + "LiveSurpriseLedger.swift",
     "return LedgerSurpriseSource(client: LedgerClient(base: base, transport: URLSessionPlanTransport(),"): 1,
    (PA + "LiveTelemetry.swift", GUARD): 1,
    (PA + "LiveTelemetry.swift", "return TelemetryClient(base: base, device: { StoredInstallID().installID() },"): 1,
    (PA + "LiveTripPlanner.swift", "guard let base = LiveBaseURL.url else { return UnreachableTripPlanner() }"): 1,
    (PA + "LiveTripPlanner.swift",
     "let client = ClientTripPlanner(client: TripClient(base: base, transport: URLSessionPlanTransport(),"): 1,
    (PA + "LiveTripPlanner.swift", "return TelemetryTripPlanner(inner: ConfiguredTripPlanner(planner: client, cache: "
                                   "LivePlanner.cache(base), appBuild: LivePlanner.appBuild))"): 1,
    (PA + "LiveWaitlist.swift", GUARD): 1,
    (PA + "LiveWaitlist.swift",
     "return WaitlistClient(base: base, transport: URLSessionPlanTransport(), installID: StoredInstallID(),"): 1,
}


def debug_states(text):
    """(stripped line, inside an #if DEBUG arm) for every line; directives themselves are reported False."""
    stack, out = [], []
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("#if"):
            stack.append(line == "#if DEBUG")
            out.append((line, False))
        elif line.startswith("#else") or line.startswith("#elseif"):
            if stack:
                stack[-1] = False
            out.append((line, False))
        elif line.startswith("#endif"):
            if stack:
                stack.pop()
            out.append((line, False))
        else:
            out.append((line, any(stack)))
    return out


def check(files):
    """files: {relative path: text}. Returns the refusals, one line each; empty means green."""
    errs, seen = [], collections.Counter()
    for path in sorted(files):
        for line, in_debug in debug_states(files[path]):
            if line.startswith("//") or not TOKEN.search(line):
                continue
            seen[(path, line)] += 1
            if (path, line) not in APPROVED:
                errs.append(f"P-SAFE-03 (base URL): `{line}` at {path} is not an approved base URL site")
            elif line == OVERRIDE_READ and not in_debug:
                errs.append(f"P-SAFE-03 (base URL): `{line}` at {path} reads the launch argument outside #if DEBUG")
    for (path, line), count in APPROVED.items():
        if seen[(path, line)] != count:
            errs.append(f"P-SAFE-03 (base URL): `{line}` at {path} occurs {seen[(path, line)]} time(s), approved {count}")
    live = files.get(LIVE)
    body = [l for l in (r.strip() for r in live.split("\n")) if l and not l.startswith("//")] if live is not None else None
    if body != LIVE_BODY:
        errs.append(f"P-SAFE-03 (base URL): {LIVE} is not the approved resolver call (gone or changed)")
    return errs


def load():
    return {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted((ROOT / APP).rglob("*.swift"))}


def mutations(files):
    def edit(path, old, new):
        def apply(f):
            assert f[path].count(old) >= 1, (path, old)
            g = dict(f)
            g[path] = f[path].replace(old, new, 1)
            return g
        return apply

    def add(path, text):
        def apply(f):
            g = dict(f)
            g[path] = text
            return g
        return apply

    shell = "apps/ios/ScenicDrive/ScenicDriveApp.swift"
    old_guard = ('guard let text = UserDefaults.standard.string(forKey: "plan.base.url"), let base = URL(string: text),\n'
                 '              base.scheme == "https" else { return nil }')
    return [
        ("the override read outside DEBUG", edit(LIVE, "#if DEBUG\n", "#if true\n")),
        ("the override read moved to the #else arm", edit(LIVE, "#if DEBUG\n", "#if !DEBUG\n")),
        ("the release arm reads the environment", edit(LIVE, "return nil\n",
                                                       'return ProcessInfo.processInfo.environment["BASE"]\n')),
        ("the old UserDefaults reader restored in LiveWaitlist", edit(PA + "LiveWaitlist.swift", GUARD, old_guard)),
        ("telemetry on a literal URL", edit(PA + "LiveTelemetry.swift", "TelemetryClient(base: base,",
                                            'TelemetryClient(base: URL(string: "https://example.com")!,')),
        ("the ledger on the pilot literal", edit(PA + "LiveSurpriseLedger.swift", GUARD,
                                                 'let base = URL(string: "https://scenic-api.phineas-fritsch.workers.dev")!')),
        ("a second resolve beside LiveBaseURL", edit(PA + "LiveSession.swift", GUARD,
                                                     "guard let base = APIBaseURL.resolve(bundled: nil, override: "
                                                     "ProcessInfo.processInfo.arguments.last) else { return nil }")),
        ("the shell reads the Info.plist key", edit(shell, "@main\n",
                                                    'let api = Bundle.main.object(forInfoDictionaryKey: '
                                                    '"SCENIC_API_BASE_URL")\n@main\n')),
        ("a new file builds a client on its own URL", add(PA + "LiveShadow.swift",
                                                          "let shadow = WaitlistClient(base: URL(string: \"https://x.dev\")!,\n")),
        ("a raw request outside every client", add(PA + "LivePing.swift",
                                                    'let ping = PlanHTTPRequest(url: URL(string: "https://x.dev/plan")!,\n')),
        ("LiveBaseURL.swift deleted", lambda f: {k: v for k, v in f.items() if k != LIVE}),
        ("the reroute sender drops LiveBaseURL", edit(PA + "LivePlanner.swift", "guard let base = LiveBaseURL.url, let continuation",
                                                     "guard let base = URL(string: preview.title), let continuation")),
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
        print(f"P-SAFE-03 (base URL) FAIL: {len(errs)} refusal(s)"); return 1
    print(f"P-SAFE-03 (base URL): {sum(APPROVED.values())} approved base URL sites, LiveBaseURL.swift as approved, "
          f"the -plan.base.url read inside #if DEBUG")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
