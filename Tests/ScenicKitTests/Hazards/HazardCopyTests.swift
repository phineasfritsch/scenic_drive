import Foundation
import ScenicKit
import Testing

/// T-0339 A1-A5: the hazard strip's words, compared WHOLE against the ruled copy (the task Log's R3), written out
/// here independently of HazardCopy's own table. Every unknown variant is a function of the kind it rides on.
@Suite("HazardCopyTests")
struct HazardCopyTests {
    static let access = "Restricted access on part of this route - check the signs before you drive it"
    static let surface = "Road surface we cannot name on part of this route - check it suits your car"
    static let generic = "Something on part of this route needs a closer look - check the road before you drive it"
    static let suits = "on part of this route - check it suits your car"
    static let through = "on part of this route - you may not be allowed through"

    /// R3, the 19 rows of M1: what the Worker's hazardsOf can send, and what each one says.
    static let ruled: [String: [String: String]] = [
        "surface": [
            "paving_stones": "Paving stones on part of this route - expect a slower, rougher ride",
            "cobblestone": "Cobblestones on part of this route - expect a slower, rougher ride",
            "unpaved": "Unpaved road \(suits)",
            "compacted": "Packed dirt \(suits)",
            "fine_gravel": "Fine gravel \(suits)",
            "gravel": "Gravel \(suits)",
            "ground": "Dirt road \(suits)",
            "dirt": "Dirt road \(suits)",
            "grass": "Grass track on part of this route - most cars should not drive it",
            "sand": "Sand on part of this route - cars can get stuck",
            "wood": "Wooden road surface on part of this route - slippery when wet",
            "other": "Unusual road surface \(suits)",
        ],
        "road_access": [
            "destination": "Local traffic only \(through)",
            "customers": "Customers only \(through)",
            "delivery": "Deliveries only \(through)",
            "agricultural": "Farm vehicles only \(through)",
            "forestry": "Forestry vehicles only \(through)",
            "private": "Private road on this route - you may not have permission to drive it",
            "no": "No entry for cars on part of this route - do not drive it",
        ],
    ]

    static func run(_ kind: String, _ value: String) -> PlanHazardRun {
        PlanHazardRun(kind: kind, value: value, fromIndex: 0, toIndex: 1)
    }

    @Test("every Worker hazard row reads its ruled line, whole")
    func everyRow() {
        #expect(HazardCopy.runLines == Self.ruled)
        #expect(Self.ruled.values.map(\.count).reduce(0, +) == 19)
        for (kind, rows) in Self.ruled {
            for (value, line) in rows {
                #expect(HazardCopy.line(for: Self.run(kind, value)) == line, "\(kind)/\(value)")
                #expect(HazardCopy.isKnown(Self.run(kind, value)), "\(kind)/\(value)")
            }
        }
    }

    /// The values each kind is probed with: an unlisted value, empty, each kind's row value upper-cased and
    /// space-padded, and each kind's whitelisted value (which the Worker never sends, and which is not a row).
    static func nearMisses() -> [String] {
        ["xyzzy", "", "GRAVEL", " gravel", "gravel ", "DESTINATION", " destination", "Destination", "asphalt", "yes"]
    }

    /// What a run that is not an exact row must read: a function of its kind only.
    static func expectedFallback(kind: String) -> String {
        switch kind {
        case "surface": return surface
        case "road_access": return access
        default: return generic
        }
    }

    @Test("an unlisted value or kind reads a safe line, never the raw key")
    func unknownIsSafe() {
        let kinds = ["surface", "road_access", "toll_road", "ford", "", "Surface", "road_access "]
        var probed: [PlanHazardRun] = []
        for kind in kinds {
            var values = Self.nearMisses()
            // A row value of the OTHER kind, and every row value under an unknown kind: right value, wrong kind.
            for (other, rows) in Self.ruled where other != kind { values += rows.keys.sorted() }
            for value in values {
                #expect(Self.ruled[kind]?[value] == nil, "the probe \(kind)/\(value) is a row, not a near miss")
                probed.append(Self.run(kind, value))
            }
        }
        var unknown: [PlanHazardRun] = []
        for run in probed {
            let line = HazardCopy.line(for: run)
            #expect(line == Self.expectedFallback(kind: run.kind), "\(run.kind)/\(run.value) -> \(line)")
            #expect(!line.contains(":") && !line.contains("_"), "\(run.kind)/\(run.value) -> \(line)")
            let value = run.value.trimmingCharacters(in: .whitespaces).lowercased()
            let words = line.lowercased().split { !$0.isLetter }.map(String.init)
            if !value.isEmpty {
                #expect(!words.contains(value), "\(run.kind)/\(run.value) -> \(line)")
                #expect(!line.lowercased().contains(value) || !value.contains("_"), "\(run.kind)/\(run.value)")
            }
            if !HazardCopy.isKnown(run) { unknown.append(run) }
        }
        // Every probe is logged as unknown - none of them is a row.
        #expect(unknown == probed)
        // 7 kinds x 10 near misses, plus the other kind's rows: 7 + 12 for the two known kinds, 19 for each unknown.
        #expect(probed.count == 7 * 10 + 7 + 12 + 5 * 19)
        // The meta-test: the fallback differs by kind, so no expected line ignores the kind it rides on.
        #expect(Set(kinds.map { Self.expectedFallback(kind: $0) }).count == 3)
    }

    static func utc(_ text: String) -> Date { ISO8601DateFormatter().date(from: text)! }

    @Test("every hazard flag reads its ruled line, whole")
    func everyFlag() {
        let until = Self.utc("2026-10-09T18:00:00Z")
        let utc = TimeZone(identifier: "UTC")!
        let closed = "Road closed on this route until Oct 9, 6:00 PM"
        let open = "Road closed on this route, no reopening time given"
        let rows: [(HazardFlag, String)] = [
            (.closure(source: "Caltrans", until: until), "\(closed) - reported by Caltrans"),
            (.closure(source: "", until: until), "\(closed) - source not named"),
            (.closure(source: "  ", until: until), "\(closed) - source not named"),
            (.closure(source: "511 SF Bay", until: nil), "\(open) - reported by 511 SF Bay"),
            (.closure(source: "", until: nil), "\(open) - source not named"),
            (.closure(source: " \t", until: nil), "\(open) - source not named"),
            (.ford, "Ford on this route - the road crosses water; do not drive in if it is deep or flowing"),
            (.gate, "Gate on this route - it may be closed or locked"),
            (.noCell(minutes: 1), "No phone signal for about 1 min on this route - tell someone your plans"),
            (.noCell(minutes: 95), "No phone signal for about 95 min on this route - tell someone your plans"),
            (.twilightArrival(at: Self.utc("2026-10-09T19:42:00Z")),
             "You arrive after dusk, around 7:42 PM - expect to drive part of this in the dark"),
            (.twilightArrival(at: Self.utc("2026-10-09T09:05:00Z")),
             "You arrive after dusk, around 9:05 AM - expect to drive part of this in the dark"),
            (.surfaceUnknown(km: 2.04), "Road surface not recorded for 2.0 km of this route - it may be unpaved"),
            (.surfaceUnknown(km: 13.0), "Road surface not recorded for 13.0 km of this route - it may be unpaved"),
            (.unrecognised("hazard=landslide"), Self.generic),
            (.unrecognised("road_access"), Self.generic),
        ]
        for (flag, line) in rows {
            #expect(HazardCopy.line(for: flag, timeZone: utc) == line, "\(flag)")
        }
        // The time zone is the caller's: the same closure an hour east reads an hour later.
        let east = TimeZone(secondsFromGMT: 3600)!
        #expect(HazardCopy.line(for: .closure(source: "Caltrans", until: until), timeZone: east)
                    == "Road closed on this route until Oct 9, 7:00 PM - reported by Caltrans")
    }

    @Test("the strip keeps one line per hazard, in order")
    func oneLinePerHazard() {
        let rehearsal = [PlanHazardRun(kind: "road_access", value: "destination", fromIndex: 2, toIndex: 3)]
        let mix = [Self.run("surface", "gravel"), Self.run("road_access", "xyzzy"), Self.run("toll_road", "yes"),
                   Self.run("surface", "gravel")]
        let cases: [([PlanHazardRun], [String])] = [
            ([], []),
            (rehearsal, ["Local traffic only \(Self.through)"]),
            (mix, ["Gravel \(Self.suits)", Self.access, Self.generic, "Gravel \(Self.suits)"]),
        ]
        for (runs, lines) in cases {
            let preview = PlanPreview(route: [], etaSeconds: 600, fastestEtaSeconds: 500, etaIsEstimate: true,
                                      hazards: runs)
            #expect(HazardCopy.lines(for: preview) == lines)
            #expect(HazardCopy.lines(for: preview).count == runs.count)
        }
    }

    /// T-0341 R2, written out: X crosses, S stale, U unavailable, D dropped.
    static let closureX = "This route crosses a reported road closure - expect the road to be blocked and check before you drive"
    static let closureS = "Road closure reports may be out of date for this route - check for closures before you drive"
    static let closureU = "Road closures could not be checked for this route - check for closures before you drive"
    static let closureD =
        "Not every reported road closure near this route was checked - check for closures before you drive"

    @Test("every closure condition reads its ruled lines, whole, on every route card")
    func closureLines() {
        let (x, s, u, d) = (Self.closureX, Self.closureS, Self.closureU, Self.closureD)
        let rows: [(ClosuresState, Bool, Bool, [String])] = [
            (.fresh, false, false, []), (.fresh, true, false, [d]), (.fresh, false, true, [x]),
            (.fresh, true, true, [x, d]),
            (.stale, false, false, [s]), (.stale, true, false, [s, d]), (.stale, false, true, [x, s]),
            (.stale, true, true, [x, s, d]),
            (.unavailable, false, false, [u]), (.unavailable, true, false, [u, d]),
            (.unavailable, false, true, [x, u]), (.unavailable, true, true, [x, u, d]),
        ]
        let gravel = Self.run("surface", "gravel")
        for (state, dropped, crosses, want) in rows {
            let closures = ClosuresHazard(state: state, dropped: dropped, crosses: crosses)
            let label = "\(state) dropped=\(dropped) crosses=\(crosses)"
            #expect(HazardCopy.closureLines(for: closures) == want, "\(label)")
            let plan = PlanPreview(route: [], etaSeconds: 600, fastestEtaSeconds: 500, etaIsEstimate: true,
                                   hazards: [gravel, gravel], closures: closures)
            #expect(HazardCopy.lines(for: plan) == want + ["Gravel \(Self.suits)", "Gravel \(Self.suits)"], "\(label)")
            let trip = TripItinerary(isFull: true, etaSeconds: 600, fastestEtaSeconds: 500, etaIsEstimate: true,
                                     days: [], closures: closures)
            #expect(HazardCopy.lines(for: trip) == want, "\(label)")
            let loop = LoopPreview(path: [], waypoints: [], durationSeconds: 600, distanceMeters: 1_000,
                                   retraceFraction: 0, etaIsEstimate: true, closures: closures)
            #expect(HazardCopy.lines(for: loop) == want, "\(label)")
        }
        #expect(ClosuresHazard.clear == ClosuresHazard(state: .fresh, dropped: false, crosses: false))
        for line in [x, s, u, d] { #expect(!line.contains("_") && !line.contains(":"), "\(line)") }
    }

    @Test("no copy line is empty, and none spells a wire key")
    func noWireKey() {
        let lines = HazardCopy.runLines.values.flatMap(\.values)
            + [HazardCopy.surfaceFallback, HazardCopy.accessFallback, HazardCopy.genericLine, HazardCopy.noneFlagged]
        #expect(lines.count == 23)
        for line in lines {
            #expect(!line.isEmpty && !line.contains("_") && !line.contains(":"), "\(line)")
        }
        #expect(HazardCopy.surfaceFallback == Self.surface)
        #expect(HazardCopy.accessFallback == Self.access)
        #expect(HazardCopy.genericLine == Self.generic)
        #expect(HazardCopy.noneFlagged == "Nothing unpaved or restricted is flagged on this route.")
    }
}
