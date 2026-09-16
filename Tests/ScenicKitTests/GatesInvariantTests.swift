import Foundation
import Testing
@testable import ScenicKit

/// The motorway invariant, pinned as a **class** rather than as a list of instances.
///
/// `GatesTests` crosses the four freeway `highway` values with thirteen literal companion tag sets. That kills
/// every branch keyed on one of those thirteen keys, and the reviews of PR #82 then walked straight past it
/// eleven times - `expressway=yes`, a loop over `foot`/`bicycle`, `lanes >= 5`, `maxspeed >= 100`, then
/// `destination`, `horse`, a loop over `horse`/`moped`, `let tags = allTags` then `horse`,
/// `motor_vehicle != "yes"`, and then `sidewalk=no` and `int_ref` from the sixth review. Each one refuses
/// real freeway geometry and each left `swift test` green.
/// Enumerating more keys buys more rounds of the same review, so the three tests below pin the class.
///
///   * `theConsideredTagsViewCannotReadAnUnconsideredKey` pins the *mechanism*. `Gates.verdict` - where every
///     rule lives - is handed a `ConsideredTags`, and that type answers `nil` for any key outside
///     `Gates.consideredTagKeys`, at each read, with the raw dictionary private. A rule keyed on a freeway
///     tag is therefore dead code wherever it is typed, by an extra identifier or by a loop. This test is
///     what goes red if that accessor ever stops narrowing.
///   * `theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn` pins the literal the accessor consults.
///     Widening it is the one edit that revives such a branch, and it turns this test red by name.
///   * `irrelevantTagKeysCannotChangeADecision` pins the *behaviour* for sixteen bases against twenty-one
///     keys no rule uses. It is what covers the one position a type cannot reach: `Gates.decide` itself,
///     which still has the raw dictionary in scope because Swift gives a function no way to drop its own
///     parameter. `ops/mutate/gates_corpus.py` keeps eleven mutations in exactly that position. It is also
///     what caught the sixth review's reflection mutant, which the accessor did not stop.
///
/// **What is still not closed, stated rather than denied.**
///
///   1. A refusal keyed on a key that IS in `consideredTagKeys`, with a freeway-relevant value. The
///      accessor is irrelevant to it by construction. `freewayValuesOfConsideredKeysAreAllowed` below is the
///      only thing that closes it, and it closes it for the values it writes out and no others.
///   2. A refusal typed into `Gates.decide` on a key this suite's noise list does not name. The list is an
///      enumeration and that is its honest limit; it now names the keys all eleven refuted branches used.
///      The sixth review measured that limit at two keys - `sidewalk` and `int_ref` - and both are in the
///      list below now, which moves the boundary without closing the class.
@Suite("Gates invariant")
struct GatesInvariantTests {

    @Test("a tag view read of a key no rule is written on is nil, whatever the way carries")
    func theConsideredTagsViewCannotReadAnUnconsideredKey() {
        // A realistic signed freeway ramp, written out. Every key a refused branch has reached for in four
        // reviews of PR #82 is on it.
        let ramp = ConsideredTags([
            "highway": "motorway_link", "destination": "San Francisco", "oneway": "yes",
            "ref": "I 280", "expressway": "yes", "foot": "no", "bicycle": "no", "horse": "no",
            "moped": "no", "lanes": "5", "maxspeed": "105", "motorroad": "yes", "toll": "yes",
            "sidewalk": "no", "int_ref": "I 280",
            "surface": "asphalt", "motor_vehicle": "designated",
        ])

        // Reads that must answer nil - the key is not one any rule is written on. Expected side is the
        // literal `nil`, not `Gates.consideredTagKeys.contains(...)`, which would ask the thing under test.
        for key in ["destination", "oneway", "ref", "expressway", "foot", "bicycle", "horse",
                    "moped", "lanes", "maxspeed", "motorroad", "toll", "sidewalk", "int_ref"] {
            #expect(ramp[key] == nil, "\(key) is not a key any gate rule is written on and must read as nil")
        }

        // And the two keys on this way that ARE considered must read straight through, so the test cannot
        // pass by narrowing everything to nothing.
        #expect(ramp["highway"] == "motorway_link")
        #expect(ramp["surface"] == "asphalt")
        #expect(ramp["motor_vehicle"] == "designated")

        // An absent considered key is still nil, which is what "positive evidence only" rests on.
        #expect(ramp["ford"] == nil)
        #expect(ConsideredTags([:])["highway"] == nil)
    }

    @Test("the gate set considers only the tag keys its own rules are written on")
    func theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn() {
        // Written out as the complete expected set, in a literal - not as a count, and not filtered out of
        // anything `Gates` exposes. Ten keys, one per rule in `verdict`, and every OSM key a freeway carries
        // is deliberately absent. Widening this is how a motorway refusal gets its tag back; that is exactly
        // why it is pinned here, by name, rather than left to a comment.
        #expect(Gates.consideredTagKeys == Set([
            "surface", "highway", "tracktype", "smoothness", "access",
            "motor_vehicle", "barrier", "locked", "ford", "service",
        ]))
    }

    @Test("a freeway is allowed on every value of a considered key that real freeway geometry carries")
    func freewayValuesOfConsideredKeysAreAllowed() {
        // Residual 1, and the ONLY thing that closes it. `ConsideredTags` cannot help here: these keys are
        // read by rules on purpose, so a "be thorough" branch on one of them fires. The fourth review of
        // PR #82 got `if let mv = tags["motor_vehicle"], mv != "yes" { return .refused(.noAccess) }` past
        // the whole suite; `motor_vehicle=designated` is how motorroad and expressway geometry is tagged,
        // and refusing it refuses the freeway network again by a different door.
        //
        // Every pair below is a written-out literal and every expectation is the literal `.allowed`.
        // Nothing is read back from `Gates.closedAccess` and friends, which would assert a set against
        // itself.
        let freeways = ["motorway", "motorway_link", "trunk", "trunk_link"]
        let carried: [(String, String)] = [
            ("motor_vehicle", "yes"), ("motor_vehicle", "designated"), ("motor_vehicle", "permissive"),
            ("access", "yes"), ("access", "permissive"), ("access", "designated"),
            ("surface", "asphalt"), ("surface", "paved"), ("surface", "concrete"),
            ("smoothness", "excellent"), ("smoothness", "good"), ("smoothness", "intermediate"),
        ]

        for highway in freeways {
            for (key, value) in carried {
                #expect(Gates.decide(["highway": highway, key: value]) == .allowed,
                        "\(highway) carrying \(key)=\(value) is penalised, never excluded")
            }
            // One way carrying a plausible set of them at once.
            #expect(Gates.decide([
                "highway": highway, "motor_vehicle": "designated", "access": "yes",
                "surface": "asphalt", "smoothness": "excellent",
            ]) == .allowed)
        }
    }

    @Test("a tag key no safety rule is written on cannot change any decision")
    func irrelevantTagKeysCannotChangeADecision() {
        // Every expectation below is a written-out literal `.allowed` or `.refused(<case>)`. Nothing is read
        // back from `Gates`, and in particular this does NOT assert `decide(base + noise) == decide(base)`,
        // which would hold just as well for a rule set that refused both.
        let bases: [(tags: [String: String], expected: GateDecision)] = [
            (["highway": "motorway"], .allowed),
            (["highway": "motorway_link"], .allowed),
            (["highway": "trunk"], .allowed),
            (["highway": "trunk_link"], .allowed),
            (["highway": "residential"], .allowed),
            (["highway": "unclassified", "surface": "asphalt"], .allowed),
            ([:], .allowed),
            (["surface": "gravel"], .refused(.unpavedSurface)),
            (["highway": "track"], .refused(.track)),
            (["tracktype": "grade4"], .refused(.track)),
            (["smoothness": "bad"], .refused(.tooRough)),
            (["access": "private"], .refused(.noAccess)),
            (["motor_vehicle": "no"], .refused(.noAccess)),
            (["barrier": "gate", "locked": "yes"], .refused(.lockedBarrier)),
            (["ford": "yes"], .refused(.ford)),
            (["highway": "service", "service": "driveway"], .refused(.serviceWay)),
        ]

        // Keys no rule in `Gates.verdict` reads. `foot=no`, `bicycle=no` and `horse=no` are the standard
        // access triple on essentially every motorway in OSM, which is what makes "be thorough about access
        // tags" the most dangerous refactor in this file; `moped=no` is the fourth member a wider loop
        // reaches for. `destination` is the text on a freeway sign - `destination=San Francisco` is on
        // essentially every signed ramp - and has nothing to do with the `access=destination` VALUE the
        // gates do refuse; a branch confusing the two hard-excludes every on-ramp and off-ramp, which is
        // how the freeway shoulder in the middle of a long scenic drive becomes unreachable.
        //
        // `sidewalk` and `int_ref` are here because the SIXTH review got a refusal past this list on each
        // of them, with exit 0 and a control red: `sidewalk=no` is on essentially every motorway and
        // `int_ref=I 280` on every numbered freeway and ramp. Adding them moves the boundary of an
        // enumeration; it does not turn the enumeration into a proof, and nothing here claims it does.
        //
        // `vehicle` is deliberately NOT here: it is a genuine access restriction the plan's gate list does
        // not name, and pinning it as inert would pin a gap I was not asked to close.
        let noise: [(String, String)] = [
            ("expressway", "yes"), ("foot", "no"), ("bicycle", "no"),
            ("horse", "no"), ("moped", "no"), ("destination", "San Francisco"),
            ("lanes", "6"), ("maxspeed", "120"), ("toll", "yes"),
            ("hgv", "designated"), ("lit", "no"), ("oneway", "yes"),
            ("motorroad", "yes"), ("junction", "roundabout"), ("ref", "I 280"),
            ("bridge", "yes"), ("tunnel", "yes"), ("layer", "1"),
            ("name", "Junipero Serra Freeway"), ("sidewalk", "no"), ("int_ref", "I 280"),
        ]

        for (base, expected) in bases {
            #expect(Gates.decide(base) == expected, "the base itself must decide as written")
            // One key at a time, so a failure names the key that moved the verdict.
            for (key, value) in noise {
                var tags = base
                tags[key] = value
                #expect(Gates.decide(tags) == expected,
                        "adding \(key)=\(value) must not change the verdict for \(base.keys.sorted())")
            }
            // And all twenty-one at once, which is closer to a real OSM way than any single one.
            var loaded = base
            for (key, value) in noise { loaded[key] = value }
            #expect(Gates.decide(loaded) == expected,
                    "every irrelevant key at once must not change the verdict for \(base.keys.sorted())")
        }
    }
}
