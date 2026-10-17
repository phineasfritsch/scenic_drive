import Foundation
import ScenicAPIClient

/// T-0394 R2: the app's ONE Worker base URL, resolved once per launch by ScenicAPIClient's APIBaseURL from the
/// Info.plist value the app ships and, in a DEBUG build only, the `-plan.base.url` launch argument (`off` forces
/// offline). Every live client reads `url` and nothing else (ops/lib/check-base-url-sites.py); nil is routingOffline.
enum LiveBaseURL {
    static let url: URL? = APIBaseURL.resolve(bundled: bundled, override: debugOverride)

    private static var bundled: String? {
        Bundle.main.object(forInfoDictionaryKey: APIBaseURL.infoPlistKey) as? String
    }

    private static var debugOverride: String? {
        #if DEBUG
        return UserDefaults.standard.string(forKey: APIBaseURL.overrideKey)
        #else
        return nil
        #endif
    }
}
