import Foundation

/// One POST /telemetry exactly as the client hands it to its transport (T-0355 R2), so a test compares the whole
/// request - URL, method, headers and body bytes - by equality.
public struct TelemetryRequest: Equatable, Sendable {
    public let url: URL
    public let method: String
    public let headers: [String: String]
    public let body: Data

    public init(url: URL, method: String, headers: [String: String], body: Data) {
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body
    }
}
