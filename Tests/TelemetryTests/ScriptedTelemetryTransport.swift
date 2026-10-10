import Foundation
@testable import Telemetry

/// A recording transport for TelemetryClientTests: each call's outcome is scripted (default 200), and with
/// `holdFirst` the first post is held in flight until `release()`.
actor ScriptedTelemetryTransport: TelemetryTransport {
    enum Outcome: Sendable, CustomStringConvertible {
        case status(Int)
        case fails

        var description: String {
            switch self {
            case let .status(code): return "status \(code)"
            case .fails: return "throws"
            }
        }
    }

    struct Refused: Error {}

    private(set) var requests: [TelemetryRequest] = []
    private var outcomes: [Outcome]
    private let holdFirst: Bool
    private var gate: CheckedContinuation<Void, Never>?
    private(set) var isHolding = false

    init(outcomes: [Outcome] = [], holdFirst: Bool = false) {
        self.outcomes = outcomes
        self.holdFirst = holdFirst
    }

    func send(_ request: TelemetryRequest) async throws -> Int {
        requests.append(request)
        if holdFirst && requests.count == 1 {
            await withCheckedContinuation { continuation in
                gate = continuation
                isHolding = true
            }
        }
        let outcome = outcomes.isEmpty ? .status(200) : outcomes.removeFirst()
        switch outcome {
        case let .status(code): return code
        case .fails: throw Refused()
        }
    }

    func release() {
        gate?.resume()
        gate = nil
    }
}
