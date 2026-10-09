import Foundation

/// What the drive says, and when (T-0329 R2/R3): the voice half of the minimal surface (P-SAFE-09), decided here so
/// it is tested on Linux. NavAdapter calls `utterances(after:)` after every input it forwards and speaks each string
/// it gets back, unchanged, through Ferrostar's own spoken-instruction observer; it decides nothing.
///
/// Calm and sparse: nothing at the start; a mode change says one line or nothing (the closed 3x3 table in
/// `transition(from:to:)`); each leg end of the current line gets one approach line within 400 m along the line, and
/// the destination one arrival line within 30 m - each once, and only while guiding. A taken reroute is a new line.
public struct DriveVoice: Sendable, Equatable {
    /// Along-line metres to a leg's end at or below which its approach line is said; exactly 400 m speaks.
    public static let approachMeters = 400.0
    /// Along-line metres to the destination at or below which the arrival line is said; exactly 30 m speaks.
    public static let arrivalMeters = 30.0

    public static let nextStopLine = "Your next scenic stop is coming up."
    public static let destinationLine = "Your destination is coming up."
    public static let arrivalLine = "You have arrived. Take your time."

    private var mode: DriveMode
    private var line: DriveLine
    private var approached: Set<Int> = []
    private var arrived = false

    public init(session: DriveSession) {
        mode = session.mode
        line = session.line
    }

    /// The line a mode change says, or nil. Exhaustive over every (from, to) pair, with no default.
    public static func transition(from old: DriveMode, to new: DriveMode) -> String? {
        switch (old, new) {
        case (.guiding, .guiding), (.rerouting, .rerouting), (.rejoining, .rejoining): return nil
        case (.guiding, .rerouting): return "You left the route. Finding a new way."
        case (.guiding, .rejoining): return "You left the route and are offline. Head back to it."
        case (.rerouting, .guiding): return "Here is a new way."
        case (.rerouting, .rejoining): return "No new way for now. Head back to your route."
        case (.rejoining, .guiding): return "You are back on your route."
        case (.rejoining, .rerouting): return nil
        }
    }

    /// The line for a leg end `meters` away along the line, or nil. The last leg's end is the destination.
    public static func cue(metersToLegEnd meters: Double, lastLeg: Bool) -> String? {
        if lastLeg, meters <= arrivalMeters { return arrivalLine }
        guard meters <= approachMeters else { return nil }
        return lastLeg ? destinationLine : nextStopLine
    }

    /// Everything to say after the session's latest input, in order: the mode change's line, then the leg's.
    public mutating func utterances(after session: DriveSession) -> [String] {
        var said: [String] = []
        if let change = Self.transition(from: mode, to: session.mode) { said.append(change) }
        mode = session.mode
        if session.line != line {
            line = session.line
            approached = []
            arrived = false
        }
        guard session.mode == .guiding, !arrived, let end = session.legEnd,
              let cue = Self.cue(metersToLegEnd: end.meters, lastLeg: end.vertex == session.line.segmentCount)
        else { return said }
        if cue == Self.arrivalLine {
            arrived = true
            said.append(cue)
        } else if approached.insert(end.vertex).inserted {
            said.append(cue)
        }
        return said
    }
}
