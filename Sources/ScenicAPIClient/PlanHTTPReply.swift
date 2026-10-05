import Foundation

/// What came back: the HTTP status and the body bytes, nothing else (the Worker's /plan carries its meaning in
/// these two; its headers are cache-control and content-type).
public struct PlanHTTPReply: Equatable, Sendable {
    public let status: Int
    public let body: Data

    public init(status: Int, body: Data) {
        self.status = status
        self.body = body
    }
}
