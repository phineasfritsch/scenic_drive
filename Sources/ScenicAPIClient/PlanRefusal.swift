/// Why the client refused to SEND a plan request - the device-side half of the Worker's whitelist (T-0251 R3).
///
/// A refused request makes zero transport calls. The server never receives more than one coordinate per user
/// action and never more than 2 decimal places; the client holds that before the bytes exist.
public enum PlanRefusal: Error, Equatable, Sendable {
    /// Latitude outside [-90, 90], longitude outside [-180, 180], or either not finite.
    case originOutOfRange
    /// Latitude or longitude is not already at 2 decimal places. The client does not round: the caller does.
    case originMoreThanTwoDecimals
    /// The extra-time budget is outside the Worker's 0...180 minutes.
    case budgetOutOfRange
    /// The client was built with no `InstallIDProvider`, so the request would lack `x-scenic-device` and land in the
    /// Worker's shared `device:unidentified` quota bucket (T-0260 R3).
    case noInstallID
    /// The vehicle profile is not one the app can plan for yet (`VehicleProfile.isEnabled` is false); the Worker
    /// refuses every such value too (T-0311 R3, R6).
    case vehicleNotEnabled
    /// T-0319 R9: a reroute's token is not the Worker's PLAN_TOKEN spelling (lowercase 8-4-4-4-12 hex).
    case rerouteTokenMalformed
    /// T-0319 R9: a reroute's first remaining pin is outside the Worker's 0...9.
    case firstPinOutOfRange
}
