import Foundation

/// One HTTP request as the client builds it, before any transport sees it (T-0251 R4).
///
/// Our own value rather than `URLRequest`: its Sendable and Equatable conformances differ between Darwin and
/// swift-corelibs-foundation, and the tests compare the WHOLE request - url, method, headers and body bytes -
/// by exact equality to a typed literal, which needs an Equatable that means the same thing on every host.
public struct PlanHTTPRequest: Equatable, Sendable {
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
