import Foundation
import ScenicKit

/// Every way a /trip call ends without an itinerary (T-0313 R3), one case per answer the table in TripReplyReader
/// tells apart, and the ScenicKit failure the sheet shows for each.
public enum TripError: Error, Equatable, Sendable {
    case quotaExhausted(resetsAt: Date)
    case planningPaused
    case routingOffline
    case noRoute
    case regionUnsupported
    case unknownPlace
    case tooFewDays
    case ceilingBreached
    /// 422 `nothing_pretty` (T-0337): the trip the Worker would ship is not pretty enough to show.
    case nothingPretty(TripNothingPretty)
    case planRefused(reason: String)
    case invalidRequest(detail: String)
    case refusedOnDevice(TripRefusal)
    case unexpectedResponse(status: Int)

    public var failure: TripFailure {
        switch self {
        case .quotaExhausted: return .quotaExhausted
        case .planningPaused: return .planningPaused
        case .routingOffline: return .routingOffline
        case .noRoute: return .noRoute
        case .regionUnsupported: return .regionUnsupported
        case .unknownPlace: return .unknownPlace
        case .tooFewDays: return .tooFewDays
        case .ceilingBreached: return .ceilingBreached
        case .nothingPretty: return .nothingPretty
        case .planRefused: return .planRefused
        case .invalidRequest: return .invalidRequest
        case .refusedOnDevice: return .refusedOnDevice
        case .unexpectedResponse: return .unexpectedResponse
        }
    }
}
