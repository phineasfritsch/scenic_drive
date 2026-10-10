"""The mutation population for T-0357: the app's /config client (Sources/ScenicAPIClient/ConfigClient.swift,
ConfigReader.swift, ConfigWire.swift, ConfigCache.swift, ConfiguredPlanner.swift) and the degrade model
(Sources/ScenicKit/Config/RemoteConfig.swift, ConfigDegrade.swift, AppBuild.swift), plus the lines this task added to
PlanSheet's gate, RetimingPlanner and ClientPlanner. Driver config.py, runner config_run.py (ledger's three-file shape).

  * THE CLIENT (1-5): the path, the method, a header, a body, a retry;
  * THE READER (6-15): the status, every half of the build's range, a field read as a constant, the kept encoding;
  * THE WIRE (16-17): each key's name;
  * THE CACHE (18-20): the fallback, the save, a refusal that writes;
  * THE PLANNER (21-23): our build dropped, the refresh skipped, the plan bypassed;
  * THE DEGRADE (24-31): the comparison, the unknown build, the precedence, the pause, each notice;
  * OUR BUILD (32-37): the digit class at both bounds and dropped, every half of the range;
  * THE DEFAULTS (38-40): the bundled build and pause, the Worker's maximum;
  * THE WIRING (41-44): the gate, setDegrade, RetimingPlanner's forward, ClientPlanner's answer.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

API = ROOT / "Sources" / "ScenicAPIClient"
KIT = ROOT / "Sources" / "ScenicKit"
CLIENT = API / "ConfigClient.swift"
READER = API / "ConfigReader.swift"
WIRE = API / "ConfigWire.swift"
CACHE = API / "ConfigCache.swift"
PLANNER = API / "ConfiguredPlanner.swift"
REMOTE = KIT / "Config" / "RemoteConfig.swift"
DEGRADE = KIT / "Config" / "ConfigDegrade.swift"
BUILD = KIT / "Config" / "AppBuild.swift"
SUBJECTS = (CLIENT, READER, WIRE, CACHE, PLANNER, REMOTE, DEGRADE, BUILD)
SHEET = KIT / "PlanSheet" / "PlanSheet.swift"
RETIMING = KIT / "Traffic" / "RetimingPlanner.swift"
CLIENTPLANNER = API / "ClientPlanner.swift"
MUTATED_FILES = SUBJECTS + (SHEET, RETIMING, CLIENTPLANNER)

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "ConfigClientTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "ConfigCacheTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "ConfiguredPlannerTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "Config" / "ConfigDegradeTests.swift")

REQ = "GET /config is exactly the base's /config with no headers and no body, sent once"
OFF = "No reply at all is no answer, after exactly one request"
INB = "Every in-bounds answer reads as exactly the config it carries"
REF = ("Every out-of-bounds, mistyped or missing field, non-object body and non-200 status refuses the whole "
       "answer")
BUNDLED = "The bundled defaults are exactly the Worker's answer with no KV record and no kill"
FALLBACK = "A refused answer or no reply is the last good answer, else the bundled defaults, and stores nothing"
KEEPS = "A good answer is the answer and is kept as the last good one"
PDEG = "The live planner's degrade is the degrade of the refreshed answer against our build"
PPLAN = "The live planner's plan is the client planner's, and the client planner itself never degrades"
MAP = "The degrade is exactly the table's row for every pause, minimum build and our build"
OURS = "Our build reads only a positive decimal integer within 1...2147483647"
NOTICE = "Each degrade's notice is its row: the typed planningPaused copy, the update line, none"
GATE = "Under a degrade the gate issues no ticket; clear, it issues one; clearing reopens it"
RETIME = "The retiming planner's degrade is its inner planner's"

RANGE = "(1...RemoteConfig.maxAppBuild).contains(wire.minAppBuild)"
DIGITS = "text.utf8.allSatisfy({ (48...57).contains($0) })"
BUILD_RANGE = "(1...RemoteConfig.maxAppBuild).contains(build)"
ORDER = ("if let appBuild, config.minAppBuild > appBuild { return .updateRequired }\n"
         "        return config.planningPaused ? .planningPaused : .clear")

MUTATIONS = [
    ("1 the path", CLIENT, 'appendingPathComponent("config")', 'appendingPathComponent("configs")', [REQ]),
    ("2 the method", CLIENT, 'method: "GET"', 'method: "POST"', [REQ]),
    ("3 a device header", CLIENT, "headers: [:],", 'headers: ["x-scenic-device": "1"],', [REQ]),
    ("4 a body", CLIENT, "body: Data())", 'body: Data("{}".utf8))', [REQ]),
    ("5 no reply retried once", CLIENT, "else { return nil }",
     "else { _ = try? await transport.send(request); return nil }", [OFF]),
    ("6 any 2xx read", READER, "guard reply.status == 200", "guard (200..<300).contains(reply.status)", [REF]),
    ("7 any status at or above 200 read", READER, "guard reply.status == 200", "guard reply.status >= 200", [REF]),
    ("8 build 0 admitted", READER, RANGE, RANGE.replace("(1...", "(0..."), [REF]),
    ("9 the upper bound dropped", READER, RANGE, RANGE.replace("RemoteConfig.maxAppBuild", "Int.max"), [REF]),
    ("10 the maximum refused", READER, RANGE, RANGE.replace("maxAppBuild)", "maxAppBuild - 1)"), [INB]),
    ("11 build 1 refused", READER, RANGE, RANGE.replace("(1...", "(2..."), [INB, BUNDLED]),
    ("12 the range check dropped", READER, ",\n              " + RANGE, "", [REF]),
    ("13 the pause read as false", READER, "planningPaused: wire.planningPaused)", "planningPaused: false)", [INB]),
    ("14 the build read as 1", READER, "RemoteConfig(minAppBuild: wire.minAppBuild,",
     "RemoteConfig(minAppBuild: 1,", [INB]),
    ("15 the kept pause written false", READER, "planningPaused: config.planningPaused)))",
     "planningPaused: false)))", [KEEPS]),
    ("16 the build's key", WIRE, 'case minAppBuild = "min_app_build"', 'case minAppBuild = "min_build"', [INB]),
    ("17 the pause's key", WIRE, 'case planningPaused = "planning_paused"', 'case planningPaused = "paused"',
     [INB]),
    ("18 a refusal is the bundled defaults", CACHE, "else { return kept }", "else { return RemoteConfig.bundled }",
     [FALLBACK]),
    ("19 a good answer not kept", CACHE, "storage.save(ConfigReader.encode(fresh))", "_ = fresh", [KEEPS]),
    ("20 a refusal writes the defaults", CACHE, "else { return kept }",
     "else { storage.save(ConfigReader.encode(RemoteConfig.bundled)); return kept }", [FALLBACK]),
    ("21 our build dropped", PLANNER, "appBuild: appBuild)", "appBuild: nil)", [PDEG]),
    ("22 the refresh skipped", PLANNER, "ConfigDegrade.of(await cache.refresh(),",
     "ConfigDegrade.of(RemoteConfig.bundled,", [PDEG]),
    ("23 the plan bypassed", PLANNER, "await planner.plan(ticket)", ".failure(.routingOffline)", [PPLAN]),
    ("24 equal builds prompt", DEGRADE, "config.minAppBuild > appBuild", "config.minAppBuild >= appBuild",
     [MAP, PDEG]),
    ("25 the comparison reversed", DEGRADE, "config.minAppBuild > appBuild", "config.minAppBuild < appBuild",
     [MAP]),
    ("26 an unknown build prompts", DEGRADE, "if let appBuild, config.minAppBuild > appBuild",
     "if config.minAppBuild > (appBuild ?? 0)", [MAP, PDEG]),
    ("27 the pause outranks the update", DEGRADE, ORDER,
     "if config.planningPaused { return .planningPaused }\n"
     "        if let appBuild, config.minAppBuild > appBuild { return .updateRequired }\n"
     "        return .clear", [MAP, PDEG]),
    ("28 the pause ignored", DEGRADE, "return config.planningPaused ? .planningPaused : .clear", "return .clear",
     [MAP]),
    ("29 the pause's notice another failure's", DEGRADE, "PlanFailureCopy.of(.planningPaused).line",
     "PlanFailureCopy.of(.routingOffline).line", [NOTICE]),
    ("30 the update's notice nil", DEGRADE, "case .updateRequired: return Self.updateLine",
     "case .updateRequired: return nil", [NOTICE]),
    ("31 clear given a notice", DEGRADE, "case .clear: return nil", "case .clear: return Self.updateLine", [NOTICE]),
    ("32 the digit class dropped", BUILD, DIGITS + ", ", "", [OURS]),
    ("33 the digit class refuses 0", BUILD, DIGITS, DIGITS.replace("48", "49"), [OURS]),
    ("34 the digit class refuses 9", BUILD, DIGITS, DIGITS.replace("57", "56"), [OURS]),
    ("35 build 0 admitted", BUILD, BUILD_RANGE, BUILD_RANGE.replace("(1...", "(0..."), [OURS]),
    ("36 the maximum refused", BUILD, BUILD_RANGE, BUILD_RANGE.replace("maxAppBuild)", "maxAppBuild - 1)"),
     [OURS]),
    ("37 the upper bound dropped", BUILD, BUILD_RANGE, "build >= 1", [OURS]),
    ("38 the bundled build 0", REMOTE, "RemoteConfig(minAppBuild: 1, planningPaused: false)",
     "RemoteConfig(minAppBuild: 0, planningPaused: false)", [BUNDLED]),
    ("39 the bundled defaults paused", REMOTE, "RemoteConfig(minAppBuild: 1, planningPaused: false)",
     "RemoteConfig(minAppBuild: 1, planningPaused: true)", [BUNDLED, FALLBACK]),
    ("40 the Worker's maximum one short", REMOTE, "maxAppBuild = 2_147_483_647", "maxAppBuild = 2_147_483_646",
     [INB, OURS]),
    ("41 the gate ignores the degrade", SHEET, "guard disclaimerAccepted, degrade == .clear, let start",
     "guard disclaimerAccepted, let start", [GATE]),
    ("42 setDegrade a no-op", SHEET, "self.degrade = degrade", "_ = degrade", [GATE]),
    ("43 the retiming planner never degrades", RETIMING, "await inner.degrade()", ".clear", [RETIME]),
    ("44 the client planner paused", CLIENTPLANNER, "func degrade() async -> ConfigDegrade { .clear }",
     "func degrade() async -> ConfigDegrade { .planningPaused }", [PPLAN]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 a good answer returned as the kept one", CACHE, "return fresh\n", "return kept\n",
     "the line before saved ConfigReader.encode(fresh), and kept is ConfigReader.decode of those bytes: an Int in "
     "1...maxAppBuild and a Bool round-trip exactly, so kept == fresh"),
    ("E2 the empty check dropped", BUILD, "!text.isEmpty, ", "",
     "Int(\"\") is nil, so an empty build is refused by the `let build = Int(text)` clause either way"),
    ("E3 the digit class admits a slash", BUILD, DIGITS, DIGITS.replace("48", "47"),
     "Int(String) parses an optional sign then decimal digits only, so a build holding '/' is nil there"),
    ("E4 the digit class admits a colon", BUILD, DIGITS, DIGITS.replace("57", "58"),
     "Int(String) parses an optional sign then decimal digits only, so a build holding ':' is nil there"),
]

MIN_MUTATIONS = 44
MIN_EQUIVALENT = 4
MIN_TEST_FILES = 4
