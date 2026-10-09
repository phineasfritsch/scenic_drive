import Foundation

/// Corridor speeds learned on the device (plan, ETA honesty): per H3-8 cell x hour of the week, an EWMA of the
/// observed speed ratio freeFlowSeconds / actualSeconds, clamped to [0.3, 1.0] per observation (T-0320 R2, R3).
/// A slot is learned at 5 samples; until every edge of a route is learned, its ETA is an estimate (P-SAFE-07, R7).
/// It never leaves the device: no Codable conformance, and no use outside this folder (P-PRIV-05, R9).
public struct LearnedCorridorSpeeds: TrafficProvider, Equatable {
    /// Samples at which a slot's ratio is used and the badge may go (CLAUDE.md: ">= 5 learned samples").
    public static let learnedSamples = 5
    /// The weight of a new observation; the first one seeds the ratio (R3).
    public static let alpha = 0.25
    /// The learned ratio's floor and ceiling (plan, acceptance: "learned ratio in [0.3, 1.0]").
    public static let floorRatio = 0.3
    public static let ceilingRatio = 1.0

    /// The zone the hour of the week is read in.
    public let timeZone: TimeZone
    /// Every slot taught so far.
    public private(set) var slots: [CorridorSlot: CorridorRatio] = [:]

    public init(timeZone: TimeZone) {
        self.timeZone = timeZone
    }

    /// The learner a previous launch kept (T-0343 R2): nil unless EVERY row has its hour in 0...167, its ratio in
    /// [0.3, 1.0] (NaN is in neither) and samples >= 1, and no two rows share a cell and an hour - a store that
    /// holds one bad row restores nothing, and the badge stays. The cell is not checked: no route has a stray one.
    public init?(timeZone: TimeZone, restoring rows: [CorridorSlotRow]) {
        self.timeZone = timeZone
        for row in rows {
            guard let hour = HourOfWeek(row.hour), row.ratio >= Self.floorRatio, row.ratio <= Self.ceilingRatio,
                  row.samples >= 1 else { return nil }
            let slot = CorridorSlot(cell: CorridorCell(index: row.cell), hour: hour)
            guard slots[slot] == nil else { return nil }
            slots[slot] = CorridorRatio(ratio: row.ratio, samples: row.samples)
        }
    }

    /// Every slot as a row, by cell then hour: what the store keeps, and what `init(timeZone:restoring:)` takes.
    public var rows: [CorridorSlotRow] {
        slots.map { slot, learned in
            CorridorSlotRow(cell: slot.cell.index, hour: slot.hour.value, ratio: learned.ratio, samples: learned.samples)
        }.sorted { ($0.cell, $0.hour) < ($1.cell, $1.hour) }
    }

    /// Teaches one driven edge. False, with nothing changed, when either time is NaN, infinite, zero or negative.
    @discardableResult
    public mutating func record(cell: CorridorCell, hourOfWeek: HourOfWeek, actualSeconds: Double,
                                freeFlowSeconds: Double) -> Bool {
        guard actualSeconds.isFinite, freeFlowSeconds.isFinite, actualSeconds > 0, freeFlowSeconds > 0 else {
            return false
        }
        let observed = min(Self.ceilingRatio, max(Self.floorRatio, freeFlowSeconds / actualSeconds))
        let slot = CorridorSlot(cell: cell, hour: hourOfWeek)
        if let prior = slots[slot] {
            let ratio = (1 - Self.alpha) * prior.ratio + Self.alpha * observed
            slots[slot] = CorridorRatio(ratio: ratio, samples: prior.samples + 1)
        } else {
            slots[slot] = CorridorRatio(ratio: observed, samples: 1)
        }
        return true
    }

    /// Each edge at the ratio of the slot it is entered in - departsAt plus the earlier edges' re-timed seconds
    /// (R6) - when that slot is learned, else at free flow; an estimate unless every edge was learned (R7).
    public func retime(_ edges: [CorridorEdge], departsAt: Date) -> RetimedRoute {
        var seconds: [Double] = []
        var elapsed = 0.0
        var everyEdgeLearned = !edges.isEmpty
        for edge in edges {
            let hour = HourOfWeek.of(departsAt.addingTimeInterval(elapsed), in: timeZone)
            var time = edge.freeFlowSeconds
            if let learned = slots[CorridorSlot(cell: edge.cell, hour: hour)], learned.samples >= Self.learnedSamples {
                time = edge.freeFlowSeconds / learned.ratio
            } else {
                everyEdgeLearned = false
            }
            seconds.append(time)
            elapsed += time
        }
        return RetimedRoute(edgeSeconds: seconds, isEstimate: !everyEdgeLearned)
    }
}
