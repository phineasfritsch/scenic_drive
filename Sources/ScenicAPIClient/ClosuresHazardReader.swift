import Foundation
import ScenicKit

/// The one reader of a 200 body's closures_hazard (T-0341 R3), shared by PlanResponse, TripResponse and LoopResponse.
///
/// It never throws: closures never refuse a route (services/api/src/closuresStore.ts), so nothing in this key can
/// fail the answer's decode. And it never reads a doubt as silence: the key absent is the Worker's fresh contract
/// and reads `.clear`; anything present that does not read exactly as the Worker writes it reads the safest TRUE
/// line - `unavailable`, closures could not be checked. `dropped` and `crosses` are added by the Worker only to say
/// so, so either key PRESENT, whatever its value, keeps its line.
public enum ClosuresHazardReader {
    enum Keys: String, CodingKey {
        case state, version, dropped, crosses
        case fetchedAt = "fetched_at"
    }

    /// The closures_hazard under `key` in `top`, read fail-closed.
    public static func read<Key: CodingKey>(_ top: KeyedDecodingContainer<Key>, forKey key: Key) -> ClosuresHazard {
        .clear
    }
}
