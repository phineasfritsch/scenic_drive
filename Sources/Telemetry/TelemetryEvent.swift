import Foundation

/// The plan closed enum of fourteen telemetry events (plan :148, T-0265 R1), and the ONLY things the app may
/// report. Payloads are coarse by construction (P-PRIV-05, T-0265 R4): closed label enums, whole numbers
/// (minutes, counts, a corpus version), a whole percent, one Bool, and at most one H3 resolution-5 cell - no
/// coordinate, no Double, no time, no free-form String. A new case cannot ship quietly: the encoding table in
/// TelemetryEventEncodingTests switches over this enum with no `default`.
public enum TelemetryEvent: Equatable, Sendable {
    /// A plan was asked for: which surface, the extra-time budget in whole minutes, and the H3-5 cell of the
    /// origin - the one location telemetry ever carries (T-0265 R3).
    case planRequested(feature: PlanFeature, budgetMinutes: Int, origin: H3Cell)
    case planResult(PlanResultKind)
    case previewShown
    case handoffTapped(HandoffApp)
    case driveStarted
    case driveCompleted(CompletionPercent, deviations: Int)
    case driveAbandoned(CompletionPercent)
    case postDriveAnswer(prettier: Bool)
    case surpriseShown
    case surpriseNotThis(SurpriseNotThisReason)
    case surpriseTakeMeThere
    case surpriseArrived
    case corpusActivated(version: Int)
    case paywall(PaywallStep)

    /// Which of the fourteen this is.
    public var kind: TelemetryEventKind {
        switch self {
        case .planRequested: return .planRequested
        case .planResult: return .planResult
        case .previewShown: return .previewShown
        case .handoffTapped: return .handoffTapped
        case .driveStarted: return .driveStarted
        case .driveCompleted: return .driveCompleted
        case .driveAbandoned: return .driveAbandoned
        case .postDriveAnswer: return .postDriveAnswer
        case .surpriseShown: return .surpriseShown
        case .surpriseNotThis: return .surpriseNotThis
        case .surpriseTakeMeThere: return .surpriseTakeMeThere
        case .surpriseArrived: return .surpriseArrived
        case .corpusActivated: return .corpusActivated
        case .paywall: return .paywall
        }
    }

    /// The Workers Analytics Engine data point for this event, in T-0265 R2 fixed width: indexes = [name],
    /// blobs = [name, label, cell], doubles = [value1, value2].
    public var dataPoint: TelemetryDataPoint {
        var name = kind.rawValue
        var label = ""
        var cell = ""
        var value1 = 0.0
        var value2 = 0.0
        switch self {
        case let .planRequested(feature, budgetMinutes, origin):
            label = feature.rawValue
            cell = origin.hexString
            value1 = Double(budgetMinutes)
        case let .planResult(result):
            label = result.rawValue
        case let .handoffTapped(app):
            label = app.rawValue
        case let .driveCompleted(percent, deviations):
            value1 = Double(percent.value)
            value2 = Double(deviations)
        case let .driveAbandoned(percent):
            value1 = Double(percent.value)
        case let .postDriveAnswer(prettier):
            label = prettier ? "prettier" : "not_prettier"
        case let .surpriseNotThis(reason):
            label = reason.rawValue
        case let .corpusActivated(version):
            value1 = Double(version)
        case let .paywall(step):
            name = "paywall_" + step.rawValue
        case .previewShown, .driveStarted, .surpriseShown, .surpriseTakeMeThere, .surpriseArrived:
            break
        }
        return TelemetryDataPoint(indexes: [name], blobs: [name, label, cell], doubles: [value1, value2])
    }
}
