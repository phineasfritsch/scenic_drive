/// Why the device refused to send a /loop request (T-0314 R1). Each is a request the Worker's whitelist would answer
/// 400, refused here with 0 requests.
public enum LoopRefusal: Error, Equatable, Sendable {
    case startOutOfRange
    case startMoreThanTwoDecimals
    case minutesOutOfRange
    case noInstallID
    case vehicleNotEnabled
}
