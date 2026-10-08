import Foundation
import ScenicKit

/// The stored vehicle, for the shell (T-0309 R4). The shell imports features only, and Settings (Entitlements) has no
/// ScenicKit, so the shell reads the vehicle's name here and hands Settings a string.
public enum VehicleSetting {
    /// The stored vehicle's name; a standard car when nothing usable is stored.
    public static var name: String {
        VehicleProfile.stored(UserDefaults.standard.string(forKey: VehicleProfile.storageKey)).name
    }

    /// Whether onboarding has stored a vehicle on this device. The shell holds its launch corpus offer until it has,
    /// so the offer and the onboarding sheet are never raised together.
    public static var isChosen: Bool {
        UserDefaults.standard.string(forKey: VehicleProfile.storageKey) != nil
    }
}
