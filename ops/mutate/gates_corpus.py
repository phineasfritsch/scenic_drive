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

# The tail of `decide`. Two invariant mutations insert a branch immediately above it.
RETURN_ALLOWED = "        return .allowed\n    }\n}"

# The line that drops every tag key no rule is written on. Every "refuse freeway geometry" mutation below
# REPLACES this line rather than inserting above RETURN_ALLOWED, because with the filter in place a branch
# keyed on `expressway`, `foot`, `lanes` or `maxspeed` is dead code - it would be an equivalent mutant, not a
# survivor. Deleting the filter and adding the branch is the edit an author actually makes once the branch
# they typed does nothing, so that is the edit the corpus models. `let tags = allTags` keeps the rest of the
# function compiling, which is exactly what such an author would do.
FILTER = "        let tags = allTags.filter { consideredTagKeys.contains($0.key) }"
UNFILTERED = "        let tags = allTags"

# The literal that IS the filter. Widening it is the other half of the same edit.
CONSIDERED_KEYS = ('        "surface", "highway", "tracktype", "smoothness", "access",\n'
                   '        "motor_vehicle", "barrier", "locked", "ford", "service",')

MUTATIONS = [
    # --- THE INVARIANT ------------------------------------------------------------------------------------
    # If only one mutation in this file is caught, it has to be one of these eleven.
    ("gate motorways, the invariant CLAUDE.md lists first", GATES, RETURN_ALLOWED,
     '        if tags["highway"] == "motorway" || tags["highway"] == "trunk" {\n'
     '            return .refused(.noAccess)\n'
     '        }\n' + RETURN_ALLOWED),

    ("gate motorway_link and trunk_link, the shape a 'tidy-up' actually takes", GATES, RETURN_ALLOWED,
     '        if tags["highway"]?.hasPrefix("motorway") == true\n'
     '            || tags["highway"]?.hasPrefix("trunk") == true {\n'
     '            return .refused(.noAccess)\n'
     '        }\n' + RETURN_ALLOWED),

    # Found by the first review of PR #82, which got both of these past the suite. They key on a SECOND tag,
    # which the two above do not. Re-anchored on FILTER by the second review: `oneway` and `motorroad` are not
    # in `consideredTagKeys`, so above RETURN_ALLOWED these no longer change behaviour.
    ("gate a one-way motorway_link, i.e. every freeway ramp there is", GATES, FILTER,
     UNFILTERED + '\n'
     '        if tags["highway"] == "motorway_link", tags["oneway"] == "yes" {\n'
     '            return .refused(.noAccess)\n'
     '        }'),

    ("gate motorroad=yes, which is how a trunk expressway is tagged", GATES, FILTER,
     UNFILTERED + '\n        if tags["motorroad"] == "yes" { return .refused(.noAccess) }'),

    # Found by the SECOND review of PR #82, all four with `swift test` green and the harness printing 28 of 28.
    # These are the ones `freewayTagsNeverGate`'s thirteen companions did not name, and they are why the
    # invariant is now pinned as a class in GatesInvariantTests instead of as a longer list of instances.
    ("delete the key filter and refuse expressway=yes", GATES, FILTER,
     UNFILTERED + '\n        if tags["expressway"] == "yes" { return .refused(.noAccess) }'),

    ("delete the key filter and be thorough about access tags, incl. foot and bicycle", GATES, FILTER,
     UNFILTERED + '\n'
     '        for key in ["access", "motor_vehicle", "foot", "bicycle"] {\n'
     '            if let v = tags[key], closedAccess.contains(v) { return .refused(.noAccess) }\n'
     '        }'),

    ("delete the key filter and refuse anything with five or more lanes", GATES, FILTER,
     UNFILTERED + '\n'
     '        if let l = tags["lanes"], let n = Int(l), n >= 5 { return .refused(.noAccess) }'),

    ("delete the key filter and refuse a maxspeed of 100 or more", GATES, FILTER,
     UNFILTERED + '\n'
     '        if let ms = tags["maxspeed"], let v = Int(ms), v >= 100 { return .refused(.noAccess) }'),

    # The other half of the same edit, and the only reason a branch keyed on a freeway tag is dead code: give
    # the branch its key back. This one is caught by a LITERAL PIN rather than by behaviour, and that is
    # stated rather than glossed - `theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn` is the named
    # test, and widening the set changes no verdict on its own.
    ("widen consideredTagKeys so a freeway branch would work again", GATES, CONSIDERED_KEYS,
     '        "surface", "highway", "tracktype", "smoothness", "access",\n'
     '        "motor_vehicle", "barrier", "locked", "ford", "service",\n'
     '        "expressway", "foot", "bicycle",'),

    # And the mutation that proves the filter is LOAD-BEARING rather than decorative: drop a key a rule really
    # reads and that rule stops firing. It is also what catches deletion of the filter itself - with `decide`
    # no longer filtering, this mutation changes nothing, goes MISSED, and the run exits 1.
    ("drop smoothness from consideredTagKeys, which kills the smoothness gate", GATES, CONSIDERED_KEYS,
     '        "surface", "highway", "tracktype", "access",\n'
     '        "motor_vehicle", "barrier", "locked", "ford", "service",'),

    # The enum arm of the invariant. Without this, `noMotorwayReasonExists` - the test whose NAME carries the
    # invariant - was never once demonstrated red by this harness, and CLAUDE.md says a check that has never
    # been seen red is untested. Anchored on `case serviceWay`, which is code, not on the doc comment above it.
    # Moved from GateDecision.swift to GateReason.swift when the two types were split one per file.
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
    ("try a locked barrier before access, so a private way blames the gate", GATES,
     '        if let access = tags["access"], closedAccess.contains(access) { return .refused(.noAccess) }',
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }\n'
     '        if let access = tags["access"], closedAccess.contains(access) { return .refused(.noAccess) }'),

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
# The name below used to read "reorder two independent rules that cannot both fire", which described
# something this entry does not do - nothing is reordered and no two rules are named. The review of PR #82
# called that out, and the genuine reorders it was standing in for are now real MUTATIONS above. What is
# left is what the code always was: spelling the same enum case two ways.
#
# NOT here, deliberately: "insert a branch on expressway= above RETURN_ALLOWED". It cannot change behaviour
# today, but only because `consideredTagKeys` does not list `expressway` - a reason that lives in `decide`'s
# first line rather than in the branch being mutated, and one that EXPIRES the moment somebody widens that
# set. Banking it here would buy an arm that one day fails for the right reason with the wrong message
# ("a test has an opinion about how the code is WRITTEN"). It is in neither list, and this comment is why.
EQUIVALENT = [
    ("spell a GateReason case fully qualified - the same case either way", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] == "yes" { return .refused(GateReason.ford) }'),
]

# Mutations this suite is KNOWN not to catch, asserted the other way round: each must still go MISSED, and a
# gap that closes FAILS the run so it gets promoted into MUTATIONS. Empty, and that is a claim rather than an
# omission - every mutation above is expected to be killed by a named test. The runner executes this arm when
# it is non-empty; before PR #82's review it did not, so the claim had no code behind it.
KNOWN_MISSED = []
