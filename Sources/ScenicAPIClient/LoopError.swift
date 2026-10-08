import Foundation
import ScenicKit

/// Every way a /loop call ends without a loop (T-0314 R2), one case per answer the table in LoopReplyReader tells
/// apart, and the ScenicKit failure the sheet shows for each.
public enum LoopError: Error, Equatable, Sendable {
    case quotaExhausted(resetsAt: Date)
    case planningPaused
    case routingOffline
    case noRoute
    case noCleanLoop
    case regionUnsupported
    case invalidRequest(detail: String)
    case refusedOnDevice(LoopRefusal)
    case unexpectedResponse(status: Int)

    public var failure: LoopFailure {
        switch self {
        case .quotaExhausted: return .quotaExhausted
        case .planningPaused: return .planningPaused
        case .routingOffline: return .routingOffline
        case .noRoute: return .noRoute
        case .noCleanLoop: return .noCleanLoop
        case .regionUnsupported: return .regionUnsupported
        case .invalidRequest: return .invalidRequest
        case .refusedOnDevice: return .refusedOnDevice
        case .unexpectedResponse: return .unexpectedResponse
        }
    }
}
