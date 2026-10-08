import Foundation

/// The ONE header set of every plan-family request - POST /plan, /trip and /loop (T-0315 R1, R2): the JSON content
/// type, `x-scenic-device` (the install id, T-0260), and `x-scenic-account-token` (the purchase id the Worker's
/// accountTier reads, T-0272 R1) exactly when the device holds one. Both ids lowercased, the form the Worker's
/// DEVICE_ID and UUID patterns accept. Never `authorization`: a session JWT without `act` reads anon (T-0315 R1).
public enum IdentityHeaders {
    public static let deviceHeader = "x-scenic-device"
    public static let accountHeader = "x-scenic-account-token"

    public static func json(device: UUID, account: UUID?) -> [String: String] {
        var headers = ["content-type": "application/json", deviceHeader: device.uuidString.lowercased()]
        if let account { headers[accountHeader] = account.uuidString.lowercased() }
        return headers
    }
}
