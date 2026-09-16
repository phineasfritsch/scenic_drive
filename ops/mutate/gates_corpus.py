#!/usr/bin/env python3
"""The mutation corpus for the safety gates. The runner is ops/mutate/gates.py.

Split out of gates.py when the review of PR #82 added seven mutations and the single file went past the
300-line cap CLAUDE.md sets. The split is not only bookkeeping: `MIN_MUTATIONS` lives in the runner and is
checked against `len(MUTATIONS)` from here, so deleting a mutation "with a plausible reason" now has to
defeat two files instead of editing one number next to the list it guards.

Each entry is `(name, file, old, new)`. `old` must appear verbatim in the pristine file or the runner reports
SKIP and fails the run - a stale anchor is never silently a pass. **Anchor on code, never on a comment**
(CLAUDE.md): comments get stripped, and a mutation anchored on one dies quietly.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATES = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"
DECISION = ROOT / "Sources" / "ScenicKit" / "Gates" / "GateDecision.swift"
REASON = ROOT / "Sources" / "ScenicKit" / "Gates" / "GateReason.swift"
CONSIDERED = ROOT / "Sources" / "ScenicKit" / "Gates" / "ConsideredTags.swift"

# The tail of `verdict`, where every rule lives. Two invariant mutations insert a branch immediately above it.
RETURN_ALLOWED = "        return .allowed\n    }\n}"

# The body of the PUBLIC entry point - the one position in this package where a rule would still see the raw
# dictionary, because Swift gives a function no way to drop its own parameter. `verdict` is handed a
# `ConsideredTags` and cannot read an unconsidered key by any spelling, so the same branch inserted there
# would be an equivalent mutant, not a survivor. Every "refuse freeway geometry" mutation below therefore
# goes HERE, at the residual - which is where the fourth review of PR #82 put five survivors.
ENTRY = "        return verdict(ConsideredTags(tags))"

# The accessor that IS the narrowing, checked per read rather than once up front. Breaking it is one half of
# the edit that revives a dead branch; widening CONSIDERED_KEYS below is the other.
SUBSCRIPT = "        return Gates.consideredTagKeys.contains(key) ? raw[key] : nil"

# The literal the accessor consults.
CONSIDERED_KEYS = ('        "surface", "highway", "tracktype", "smoothness", "access",\n'
                   '        "motor_vehicle", "barrier", "locked", "ford", "service",')

# Rules reused as anchors by more than one mutation.
ACCESS_RULE = '        if let access = tags["access"], closedAccess.contains(access) { return .refused(.noAccess) }'
MOTOR_VEHICLE_RULE = '        if tags["motor_vehicle"] == "no" { return .refused(.noAccess) }'

MUTATIONS = [
    # --- THE INVARIANT ------------------------------------------------------------------------------------
    # If only one mutation in this file is caught, it has to be one of these seventeen.
    ("gate motorways, the invariant CLAUDE.md lists first", GATES, RETURN_ALLOWED,
     '        if tags["highway"] == "motorway" || tags["highway"] == "trunk" {\n'
     '            return .refused(.noAccess)\n'
     '        }\n' + RETURN_ALLOWED),

    ("gate motorway_link and trunk_link, the shape a 'tidy-up' actually takes", GATES, RETURN_ALLOWED,
     '        if tags["highway"]?.hasPrefix("motorway") == true\n'
     '            || tags["highway"]?.hasPrefix("trunk") == true {\n'
     '            return .refused(.noAccess)\n'
     '        }\n' + RETURN_ALLOWED),

    # Found by the first review of PR #82. They key on a SECOND tag, which the two above do not. Both keys
    # are outside `consideredTagKeys`, so in `verdict` these are now dead code; they live at ENTRY, the one
    # position where a raw read still bites.
    ("gate a one-way motorway_link from the entry point, i.e. every freeway ramp there is", GATES, ENTRY,
     '        if tags["highway"] == "motorway_link", tags["oneway"] == "yes" {\n'
     '            return .refused(.noAccess)\n'
     '        }\n' + ENTRY),

    ("gate motorroad=yes from the entry point, which is how a trunk expressway is tagged", GATES, ENTRY,
     '        if tags["motorroad"] == "yes" { return .refused(.noAccess) }\n' + ENTRY),

    # Found by the SECOND review of PR #82, all four with `swift test` green. Until the fourth review they
    # were anchored on the old `let tags = allTags.filter { ... }` line and named "delete the key filter
    # and ...", so the edit modelled was deleting that filter. Wrong model: the filter never had to be
    # deleted, because `allTags` stayed in scope. There is no filter line now, and these model what is live.
    ("refuse expressway=yes from the entry point", GATES, ENTRY,
     '        if tags["expressway"] == "yes" { return .refused(.noAccess) }\n' + ENTRY),

    ("be thorough about access tags from the entry point, incl. foot and bicycle", GATES, ENTRY,
     '        for key in ["access", "motor_vehicle", "foot", "bicycle"] {\n'
     '            if let v = tags[key], closedAccess.contains(v) { return .refused(.noAccess) }\n'
     '        }\n' + ENTRY),

    ("refuse anything with five or more lanes, from the entry point", GATES, ENTRY,
     '        if let l = tags["lanes"], let n = Int(l), n >= 5 { return .refused(.noAccess) }\n' + ENTRY),

    ("refuse a maxspeed of 100 or more, from the entry point", GATES, ENTRY,
     '        if let ms = tags["maxspeed"], let v = Int(ms), v >= 100 { return .refused(.noAccess) }\n'
     + ENTRY),

    # Found by the FOURTH review, which got all three past the shipped suite by reading the function's own
    # parameter instead of the narrowed local - one identifier's difference. `destination` is the text on a
    # freeway sign, on essentially every signed ramp, so confusing that KEY for the `access=destination`
    # VALUE excludes every ramp; `horse=no` is the third member of the motorway access triple.
    ("refuse a signed ramp, confusing the destination KEY for the access VALUE", GATES, ENTRY,
     '        if tags["destination"] != nil { return .refused(.noAccess) }\n' + ENTRY),

    ("refuse horse=no, the third member of the motorway access triple", GATES, ENTRY,
     '        if tags["horse"] == "no" { return .refused(.noAccess) }\n' + ENTRY),

    ("loop over horse and moped too, the thorough form of the same mistake", GATES, ENTRY,
     '        for key in ["access", "motor_vehicle", "horse", "moped"] {\n'
     '            if tags[key] == "no" { return .refused(.noAccess) }\n'
     '        }\n' + ENTRY),

    # The narrowing itself. Breaking this accessor is what a "why is this branch dead?" edit reaches for once
    # the branch above does nothing, and it is caught on its own - by the view test, not by a rule, because
    # no rule reads an unconsidered key today.
    ("stop ConsideredTags narrowing, so any key reads through to a rule again", CONSIDERED, SUBSCRIPT,
     "        return raw[key]"),

    # The other half of the same edit: give the branch its key back. Caught by a LITERAL PIN rather than by
    # behaviour, and that is stated rather than glossed - widening the set changes no verdict on its own.
    ("widen consideredTagKeys so a freeway branch would work again", GATES, CONSIDERED_KEYS,
     '        "surface", "highway", "tracktype", "smoothness", "access",\n'
     '        "motor_vehicle", "barrier", "locked", "ford", "service",\n'
     '        "expressway", "foot", "bicycle",'),

    # And the mutation that proves the key set is LOAD-BEARING rather than decorative: drop a key a rule
    # really reads and that rule stops firing, so behaviour tests object alongside the literal pin.
    ("drop smoothness from consideredTagKeys, which kills the smoothness gate", GATES, CONSIDERED_KEYS,
     '        "surface", "highway", "tracktype", "access",\n'
     '        "motor_vehicle", "barrier", "locked", "ford", "service",'),

    # RESIDUAL 1, which no type closes: a refusal keyed on a key that IS considered. `ConsideredTags` is
    # irrelevant to both by construction - `motor_vehicle` and `access` are read by rules on purpose, and
    # `motor_vehicle=designated` is how motorroad and expressway geometry is tagged. Only
    # `freewayValuesOfConsideredKeysAreAllowed` stands between these and the freeway network.
    ("refuse any motor_vehicle value but yes, which refuses motorroad geometry", GATES, MOTOR_VEHICLE_RULE,
     '        if let mv = tags["motor_vehicle"], mv != "yes" { return .refused(.noAccess) }'),

    ("refuse any access value but yes, tightening a considered key", GATES, ACCESS_RULE,
     '        if let access = tags["access"], access != "yes" { return .refused(.noAccess) }'),

    # The enum arm of the invariant. Without this, `noMotorwayReasonExists` - the test whose NAME used to
    # carry the invariant - was never once demonstrated red by this harness, and CLAUDE.md says a check that
    # has never been seen red is untested. Anchored on `case serviceWay`, which is code, not on the doc
    # comment above it. Moved from GateDecision.swift to GateReason.swift when the two types were split.
    ("add a GateReason case that could name a motorway refusal", REASON,
     "    case serviceWay",
     "    case serviceWay\n\n    case motorwayExcluded"),

    # --- absent is not negative ---------------------------------------------------------------------------
    ("refuse a way with NO surface tag, which would exclude most rural lanes", GATES,
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {',
     '        if !unpavedSurfaces.contains(tags["surface"] ?? "") == false || tags["surface"] == nil {'),

    ("refuse any way that has a surface tag at all", GATES,
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {',
     '        if tags["surface"] != nil {'),

    ("refuse every gate, locked or not", GATES,
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }',
     '        if tags["barrier"] == "gate" { return .refused(.lockedBarrier) }'),

    ("refuse a way tagged locked even with no barrier", GATES,
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }',
     '        if tags["locked"] == "yes" { return .refused(.lockedBarrier) }'),

    ("refuse every service way, not only driveways and parking aisles", GATES,
     '        if tags["highway"] == "service", let s = tags["service"], refusedServiceValues.contains(s) {',
     '        if tags["highway"] == "service" {'),

    ("refuse a driveway value even on a road that is not a service way", GATES,
     '        if tags["highway"] == "service", let s = tags["service"], refusedServiceValues.contains(s) {',
     '        if let s = tags["service"], refusedServiceValues.contains(s) {'),

    ("refuse ford = no as well as ford = yes", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] != nil { return .refused(.ford) }'),

    # --- the sets themselves ------------------------------------------------------------------------------
    ("drop compacted and fine_gravel from the unpaved set", GATES,
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",',
     '        "gravel", "dirt", "ground", "sand", "unpaved",'),

    ("call asphalt unpaved", GATES,
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",',
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel", "asphalt",'),

    # The widening direction, on values a "be thorough" edit actually reaches for. `asphalt` above was covered
    # by the four paved values the old allowed-side list happened to name; cobblestone and sett were not, and
    # a cobbled lane becoming a HARD SAFETY REFUSAL is the opposite of what a scenic router is for. Found by
    # the second review of PR #82.
    ("call cobblestone and sett unpaved, refusing a scenic cobbled lane", GATES,
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",',
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",\n'
     '        "cobblestone", "sett",'),

    ("let destination-only access through", GATES,
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]',
     '    public static let closedAccess: Set<String> = ["private", "no", "permit"]'),

    ("refuse permissive access", GATES,
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]',
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination",\n'
     '                                                   "permissive"]'),

    ("move the tracktype boundary, letting grade3 through", GATES,
     '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]',
     '    public static let refusedTracktypes: Set<String> = ["grade4", "grade5"]'),

    ("move the tracktype boundary the other way, refusing grade2", GATES,
     '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]',
     '    public static let refusedTracktypes: Set<String> = ["grade2", "grade3", "grade4", "grade5"]'),

    ("refuse intermediate smoothness, which the plan allows", GATES,
     '        "bad", "very_bad", "horrible", "very_horrible", "impassable",',
     '        "intermediate", "bad", "very_bad", "horrible", "very_horrible", "impassable",'),

    ("let a merely bad road through", GATES,
     '        "bad", "very_bad", "horrible", "very_horrible", "impassable",',
     '        "very_bad", "horrible", "very_horrible", "impassable",'),

    # `refusedServiceValues` was the one rule set with neither a member-by-member test nor a shrink mutation,
    # and the two members the old suite never named are exactly the two this drops. Added for PR #82.
    ("shrink refusedServiceValues to the two values the old suite named", GATES,
     '        "driveway", "parking_aisle", "drive-through", "emergency_access",',
     '        "driveway", "parking_aisle",'),

    # `highway = track` is an unconditional safety gate. Every old track test supplied either highway=track
    # with no tracktype or a tracktype on highway=residential, so this narrowing was invisible. Added for #82.
    ("narrow the track gate to spare a well-graded track", GATES,
     '        if tags["highway"] == "track" { return .refused(.track) }',
     '        if tags["highway"] == "track", tags["tracktype"] != "grade1" { return .refused(.track) }'),

    # --- the reason, which the autopsy reads --------------------------------------------------------------
    ("report an unpaved surface as a locked barrier", GATES,
     "            return .refused(.unpavedSurface)",
     "            return .refused(.lockedBarrier)"),

    ("report a ford as rough surface", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] == "yes" { return .refused(.tooRough) }'),

    # Rule ORDER is behaviour, because ops/route-autopsy reads whichever reason fires first. No test used to
    # supply a way that tripped two rules, so both reorders below were silent. Added for PR #82 - and note
    # that the EQUIVALENT arm's only member used to be NAMED "reorder two independent rules", while being a
    # spelling change; these are the real thing.
    ("try ford before surface, so a gravel ford blames the water", GATES,
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {\n'
     '            return .refused(.unpavedSurface)\n        }',
     '        if tags["ford"] == "yes" { return .refused(.ford) }\n'
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {\n'
     '            return .refused(.unpavedSurface)\n        }'),

    ("try access before highway=track, so a private track blames the gate", GATES,
     '        if tags["highway"] == "track" { return .refused(.track) }',
     '        if let a = tags["access"], closedAccess.contains(a) { return .refused(.noAccess) }\n'
     '        if tags["highway"] == "track" { return .refused(.track) }'),

    # The two reorders the five hand-picked pairs in `theFirstRuleToFireIsTheReasonReported` did not cover.
    # Found by the second review of PR #82; both are caught by the all-pairs property in GatesOrderTests.
    ("try a locked barrier before access, so a private way blames the gate", GATES, ACCESS_RULE,
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }\n'
     + ACCESS_RULE),

    ("try smoothness before highway=track, so a rough track blames the surface", GATES,
     '        if tags["highway"] == "track" { return .refused(.track) }',
     '        if let s = tags["smoothness"], refusedSmoothness.contains(s) { return .refused(.tooRough) }\n'
     '        if tags["highway"] == "track" { return .refused(.track) }'),

    ("a refusal reports itself as allowed", DECISION,
     "    public var isAllowed: Bool {\n        if case .allowed = self { return true }\n        return false",
     "    public var isAllowed: Bool {\n        return true"),

    ("an allowed way reports a reason anyway", DECISION,
     "    public var reason: GateReason? {\n        if case let .refused(r) = self { return r }\n"
     "        return nil",
     "    public var reason: GateReason? {\n        if case let .refused(r) = self { return r }\n"
     "        return .ford"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE.
#
# The first entry's name used to read "reorder two independent rules that cannot both fire", describing
# something it does not do. The review of PR #82 called that out; the real reorders are MUTATIONS above.
#
# The second is the tidy-up that would undo the fourth review's finding without changing a verdict: narrow
# once in the initialiser and let the subscript hand back whatever it stored. Identical for every input -
# which is the point. It is banked here because a test that caught it would have an opinion about how
# `ConsideredTags` is WRITTEN. What it costs is the thing this corpus cannot assert: it puts back a single
# deletable line, exactly the shape that let `allTags` survive four reviews.
#
# NOT here, deliberately: "insert a branch on expressway= above RETURN_ALLOWED". It cannot change behaviour
# today, but only because `consideredTagKeys` does not list `expressway` - a reason that EXPIRES the moment
# somebody widens that set. Banking it would buy an arm that one day fails for the right reason with the
# wrong message. It is in neither list, and this comment is why.
EQUIVALENT = [
    ("spell a GateReason case fully qualified - the same case either way", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] == "yes" { return .refused(GateReason.ford) }'),

    ("narrow in the initialiser instead of at each read - same answer for every key", CONSIDERED,
     "        self.raw = raw\n    }",
     "        self.raw = raw.filter { Gates.consideredTagKeys.contains($0.key) }\n    }"),
]

# Mutations this suite is KNOWN not to catch, asserted the other way round: each must still go MISSED, and a
# gap that closes FAILS the run so it gets promoted into MUTATIONS. Empty, and that is a claim rather than an
# omission - every mutation above is expected to be killed by a named test. The runner executes this arm when
# it is non-empty; before PR #82's review it did not, so the claim had no code behind it.
KNOWN_MISSED = []
