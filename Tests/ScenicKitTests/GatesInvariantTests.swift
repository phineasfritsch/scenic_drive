import Foundation
import Testing
@testable import ScenicKit

/// The motorway invariant, pinned as a **class** rather than as a list of instances.
///
/// `GatesTests` crosses the four freeway `highway` values with thirteen literal companion tag sets. That kills
/// every branch keyed on one of those thirteen keys, and the second review of PR #82 then walked straight past
/// it four more times - `expressway=yes`, a loop over `foot`/`bicycle`, `lanes >= 5`, `maxspeed >= 100`. Each
/// one refuses real freeway geometry (`foot=no` and `bicycle=no` are on essentially every motorway in OSM) and
/// each left `swift test` green and `ops/mutate/gates.py` printing "28 of 28". Enumerating four more keys would
/// have bought four more rounds of the same review.
///
/// The two tests below are the class instead of the instances:
///
///   * `theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn` pins `Gates.consideredTagKeys` as a
///     written-out literal. `Gates.decide` drops every other key before a rule runs, so a branch keyed on a
///     key that is not in that set is dead code. Adding the key is the visible half of the edit, and it turns
///     this test red by name.
///   * `irrelevantTagKeysCannotChangeADecision` is the other half: it pins the *behaviour* for sixteen bases
///     against sixteen keys no rule uses, which is what catches an edit that deletes the filter and adds the
///     branch in one go - the shape `ops/mutate/gates_corpus.py` now carries four of.
///
/// **What is still not closed, stated rather than denied.** A refusal keyed on a key that IS in
/// `consideredTagKeys`, with a freeway-relevant value no test supplies. For a freeway that is `highway`, and
/// `freewayTagsNeverGate` covers it across 52 ways. And deleting the filter while keying on a key neither the
/// noise list nor the companion list names would still be invisible **to this suite** - deleting the filter
/// alone leaves every test here green, which was measured and not assumed. What objects to that deletion is
/// `ops/mutate/gates.py`: six mutations are anchored on the filter line and report `SKIP ... anchor not found
/// - harness is stale`, exit 1.
@Suite("Gates invariant")
struct GatesInvariantTests {

    @Test("the gate set considers only the tag keys its own rules are written on")
    func theGateSetConsidersOnlyTheTagKeysItsOwnRulesAreWrittenOn() {
        // Written out as the complete expected set, in a literal - not as a count, and not filtered out of
        // anything `Gates` exposes. Ten keys, one per rule in `decide`, and every OSM key a freeway carries is
        // deliberately absent. Widening this is how a motorway refusal gets its tag back; that is exactly why
        // it is pinned here, by name, rather than left to a comment.
        #expect(Gates.consideredTagKeys == Set([
            "surface", "highway", "tracktype", "smoothness", "access",
            "motor_vehicle", "barrier", "locked", "ford", "service",
        ]))
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

        // Keys no rule in `Gates.decide` reads. `foot=no` and `bicycle=no` are on essentially every motorway
        // in OSM, which is what makes "be thorough about access tags" the most dangerous refactor in this
        // file. `vehicle` is deliberately NOT here: it is a genuine access restriction the plan's gate list
        // does not name, and pinning it as inert would pin a gap I was not asked to close.
        let noise: [(String, String)] = [
            ("expressway", "yes"), ("foot", "no"), ("bicycle", "no"),
            ("lanes", "6"), ("maxspeed", "120"), ("toll", "yes"),
            ("hgv", "designated"), ("lit", "no"), ("oneway", "yes"),
            ("motorroad", "yes"), ("junction", "roundabout"), ("ref", "I 280"),
            ("bridge", "yes"), ("tunnel", "yes"), ("layer", "1"),
            ("name", "Junipero Serra Freeway"),
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
            // And all sixteen at once, which is closer to a real OSM way than any single one.
            var loaded = base
            for (key, value) in noise { loaded[key] = value }
            #expect(Gates.decide(loaded) == expected,
                    "every irrelevant key at once must not change the verdict for \(base.keys.sorted())")
        }
    }
}
