import Foundation

/// Turns what the router reported about a route into the flags a driver reads.
///
/// Two decisions carry this type, and both are safety decisions rather than formatting ones.
///
/// **Thresholds exist so the strip stays worth reading.** Every advisory flag has a floor, because a strip
/// that fires on every rural lane trains the driver to ignore it - and the day it has something real to say,
/// they will. The floors are the plan's numbers where the plan gives one.
///
/// **Nothing is dropped.** Anything the derivation cannot classify becomes `.unrecognised` and sorts above
/// the advisory flags. A hazard strip that quietly omits a ford is worse than no strip, because the driver
/// has learned to trust it.
public enum HazardStrip {
    /// Below this the route barely touches unsurveyed road and saying so costs more attention than it is
    /// worth. The plan's number: *"shown only if the route spends >2 km on such edges."*
    public static let surfaceUnknownMinimumKm = 2.0

    /// Below this, "no signal" is a dead spot rather than a stretch of being out of contact.
    ///
    /// **Not from the plan.** The plan specifies the `no_cell` join and the flag, and leaves the threshold
    /// open. Five minutes is chosen here to mean "long enough that a breakdown matters", and it is named
    /// rather than inlined so tuning it is a one-line change with a test that moves. It must not be mistaken
    /// for a value handed down.
    public static let noCellMinimumMinutes = 5

    /// What the router and the corpus said about the route, in the terms this type consumes.
    ///
    /// A plain value rather than a protocol: the derivation is arithmetic and ordering, and it should be
    /// testable against exact inputs without a router, a graph or a container anywhere near it.
    public struct RouteFacts: Equatable, Sendable {
        public var surfaceUnknownKm: Double
        public var noCellMinutes: Int
        public var hasFord: Bool
        public var hasGate: Bool
        public var closures: [(source: String, until: Date?)]
        public var arrival: Date?
        public var civilTwilight: Date?
        /// Tags the router reported that this version has no case for. Carried, never discarded.
        public var unclassified: [String]

        public init(surfaceUnknownKm: Double = 0,
                    noCellMinutes: Int = 0,
                    hasFord: Bool = false,
                    hasGate: Bool = false,
                    closures: [(source: String, until: Date?)] = [],
                    arrival: Date? = nil,
                    civilTwilight: Date? = nil,
                    unclassified: [String] = []) {
            self.surfaceUnknownKm = surfaceUnknownKm
            self.noCellMinutes = noCellMinutes
            self.hasFord = hasFord
            self.hasGate = hasGate
            self.closures = closures
            self.arrival = arrival
            self.civilTwilight = civilTwilight
            self.unclassified = unclassified
        }

        public static func == (a: RouteFacts, b: RouteFacts) -> Bool {
            a.surfaceUnknownKm == b.surfaceUnknownKm && a.noCellMinutes == b.noCellMinutes
                && a.hasFord == b.hasFord && a.hasGate == b.hasGate && a.arrival == b.arrival
                && a.civilTwilight == b.civilTwilight && a.unclassified == b.unclassified
                && a.closures.map(\.source) == b.closures.map(\.source)
                && a.closures.map(\.until) == b.closures.map(\.until)
        }
    }

    /// The flags for a route, ordered by consequence.
    ///
    /// A route with nothing wrong returns an EMPTY array, never a reassuring flag. "No hazards found" and
    /// "we did not look" are different claims, and only the caller knows which it has - so this type does
    /// not put words to either.
    public static func flags(for facts: RouteFacts) -> [HazardFlag] {
        var out: [HazardFlag] = []

        for c in facts.closures where !c.source.isEmpty {
            out.append(.closure(source: c.source, until: c.until))
        }
        if facts.hasFord { out.append(.ford) }
        if facts.hasGate { out.append(.gate) }

        // Sorted so the strip is stable regardless of the order the router reported them, and deduplicated
        // because the same unknown tag on forty edges is one thing to tell the driver, not forty.
        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {
            out.append(.unrecognised(tag))
        }

        if facts.noCellMinutes >= noCellMinimumMinutes {
            out.append(.noCell(minutes: facts.noCellMinutes))
        }
        if let arrival = facts.arrival, let twilight = facts.civilTwilight, arrival > twilight {
            out.append(.twilightArrival(at: arrival))
        }
        if facts.surfaceUnknownKm > surfaceUnknownMinimumKm {
            out.append(.surfaceUnknown(km: facts.surfaceUnknownKm))
        }

        // A STABLE sort: within one severity the order the flags were built in is preserved, so two
        // closures from different sources keep the order the feed gave them rather than being reshuffled
        // by an unstable comparison on equal keys.
        return out.enumerated()
            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }
            .map(\.element)
    }
}
