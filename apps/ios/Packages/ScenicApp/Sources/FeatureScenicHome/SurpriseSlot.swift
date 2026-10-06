import Foundation
import ScenicKit
import SwiftUI

/// The home's Surprise slot (T-0273 R4, R5). FeatureScenicHome never imports FeatureSurpriseMe: the shell hands the
/// home a builder, and the home hands that builder its GATED opener - `openSurprise`, which constructs a
/// GatedHandoffButton with the acknowledgement passed through - and the last handoff failure.
public enum SurpriseSlot {
    /// Builds the card from the home's gated opener and the last failure message.
    public typealias Builder = @MainActor (_ open: @escaping @MainActor (Coordinate) -> Void,
                                           _ failure: String?) -> AnyView

    static let launchArgumentKey = "screen"
    static let launchValue = "surprise"

    /// `-screen surprise` opens the card at launch, for ios-screenshot; a release build ignores it.
    static var atLaunch: Bool {
        #if DEBUG
        return UserDefaults.standard.string(forKey: launchArgumentKey) == launchValue
        #else
        return false
        #endif
    }
}
