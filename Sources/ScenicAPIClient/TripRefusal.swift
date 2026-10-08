/// Why the device refused to send a /trip request (T-0313 R1). Each is a request the Worker's whitelist would answer
/// 400, refused here with 0 requests.
public enum TripRefusal: Error, Equatable, Sendable {
    case originOutOfRange
    case originMoreThanTwoDecimals
    case daysOutOfRange
    case extraPercentOutOfRange
    case noInstallID
    case vehicleNotEnabled
}
