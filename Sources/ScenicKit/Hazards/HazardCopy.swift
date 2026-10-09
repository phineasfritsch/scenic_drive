import Foundation

/// T-0339 A6 RED STUB: the shipped '<kind>: <value>' rendering, so the named tests fail before the table lands.
public enum HazardCopy {
    public static let runLines: [String: [String: String]] = [:]
    public static let surfaceFallback = ""
    public static let accessFallback = ""
    public static let genericLine = ""
    public static let noneFlagged = "Nothing unpaved or restricted is flagged on this route."

    public static func isKnown(_ run: PlanHazardRun) -> Bool { true }

    public static func line(for run: PlanHazardRun) -> String { "\(run.kind): \(run.value)" }

    public static func lines(for preview: PlanPreview) -> [String] { preview.hazards.map { line(for: $0) } }

    public static func line(for flag: HazardFlag, timeZone: TimeZone) -> String { "\(flag)" }
}
