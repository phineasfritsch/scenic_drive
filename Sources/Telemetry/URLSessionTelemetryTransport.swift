import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The production transport: one URLSession data task per post, the status read and the body ignored (R3).
public struct URLSessionTelemetryTransport: TelemetryTransport {
    private let session: URLSession

    public init(session: URLSession = .shared) {
        self.session = session
    }

    public func send(_ request: TelemetryRequest) async throws -> Int {
        var urlRequest = URLRequest(url: request.url)
        urlRequest.httpMethod = request.method
        urlRequest.httpBody = request.body
        for (name, value) in request.headers {
            urlRequest.setValue(value, forHTTPHeaderField: name)
        }
        let (_, response) = try await session.data(for: urlRequest)
        return (response as? HTTPURLResponse)?.statusCode ?? 0
    }
}
