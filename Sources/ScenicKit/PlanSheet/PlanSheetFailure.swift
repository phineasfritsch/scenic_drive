/// Why a plan did not reach the preview, as the plan sheet sees it (T-0294 R1): ScenicAPIClient's `PlanError`, one
/// case for one case and in the same order, without payloads. ScenicKit sits below ScenicAPIClient and cannot name
/// `PlanError`; `PlanError.failure` there is the exhaustive mapping, and no copy line reads a payload (R5).
public enum PlanSheetFailure: String, CaseIterable, Equatable, Sendable {
    case quotaExhausted
    case planningPaused
    case routingOffline
    case noRoute
    case regionUnsupported
    case attestUnsupported
    case offlineDuringDrive
    case noScenicAlternative
    /// T-0332: the route the server would ship scores below RouteScore's honest-failure threshold.
    case nothingPretty
    case unknownPlace
    case planRefused
    case invalidRequest
    case refusedOnDevice
    case unexpectedResponse
}
