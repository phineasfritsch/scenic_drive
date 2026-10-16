import Foundation
import ScenicKit

/// Every `SearchOutcome` -> what the plan sheet shows (T-0362 R5, R8). A row is offered only when the Worker issued its
/// place id (R1): that id, never the row's coordinate, is what /plan is sent, so a row without one cannot be planned to.
public enum PlaceSearchCopy {
    public static let noMatch = "No address matched. Try a street and a city."
    public static let notPlannable = "Address search found places but can't plan to them right now."
    public static let refused = "That search can't be sent. Shorten it and try again."
    public static let invalid = "That search wasn't accepted. Edit it and try again."
    public static let unauthorized = "Your session has expired. Try the search again."
    public static let methodRefused = "Address search needs a newer version of the app."
    public static let quotaExhausted = "You've used today's address searches. Named places still work."
    public static let paused = "Search is paused right now. Named places still work."
    public static let failed = "Address search didn't answer. Try again in a moment."
    public static let unreadable = "Address search sent an answer this app can't read. Try again in a moment."
    public static let offline = "You're offline. Named places still work."

    public static func unexpected(_ status: Int) -> String {
        "Address search answered unexpectedly (HTTP \(status)). Try again in a moment."
    }

    public static func answer(_ outcome: SearchOutcome) -> PlaceSearchAnswer {
        switch outcome {
        case .results(let rows):
            guard !rows.isEmpty else { return .notice(noMatch) }
            let places = rows.compactMap { row in
                row.place.map { PlanPlace(id: $0, name: row.label, coordinate: row.coordinate) }
            }
            return places.isEmpty ? .notice(notPlannable) : .places(places)
        case .refusedOnDevice: return .notice(refused)
        case .invalidRequest: return .notice(invalid)
        case .unauthorized: return .notice(unauthorized)
        case .methodRefused: return .notice(methodRefused)
        case .quotaExhausted: return .notice(quotaExhausted)
        case .paused: return .notice(paused)
        case .unavailable: return .notice(PlaceSearchAnswer.unavailableNotice)
        case .failed: return .notice(failed)
        case .unreadable: return .notice(unreadable)
        case .unexpected(let status): return .notice(unexpected(status))
        case .offline: return .notice(offline)
        }
    }
}
