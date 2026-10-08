import Foundation

/// The ONE header set of every plan-family request - POST /plan, /trip and /loop (T-0315 R1, R2): the JSON content
/// type, `x-scenic-device` (the install id, T-0260), and `x-scenic-account-token` (the purchase id the Worker's
/// accountTier reads, T-0272 R1) exactly when the device holds one. Both ids lowercased, the form the Worker's
/// DEVICE_ID and UUID patterns accept. T-0322 R4: `authorization: Bearer` exactly when the caller holds a session
/// whose act is that same purchase (PlanSessionProvider); the account header rides beside it for the whole migration
/// window, since a Worker without SESSION_JWT_SECRET reads only the header.
public enum IdentityHeaders {
    public static let deviceHeader = "x-scenic-device"
    public static let accountHeader = "x-scenic-account-token"
    public static let authorizationHeader = "authorization"

    public static func json(device: UUID, account: UUID?, bearer: String?) -> [String: String] {
        var headers = ["content-type": "application/json", deviceHeader: device.uuidString.lowercased()]
        if let account { headers[accountHeader] = account.uuidString.lowercased() }
        if let bearer { headers[authorizationHeader] = "Bearer " + bearer }
        return headers
    }
}
