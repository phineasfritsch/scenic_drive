import Foundation

/// T-0394 (R2-R4): the ONE rule for the Worker base URL every app client is built on. PlanAdapter's `LiveBaseURL.url`
/// is its only caller (ops/lib/check-base-url-sites.py): the bundled value is the app's Info.plist string under
/// `infoPlistKey`, and the override the `-plan.base.url` launch argument, which the app reads only in a DEBUG build.
///
/// A present override is the whole answer - a valid one wins, an invalid one (`off`, empty, http) means no base and
/// never a silent fall-back to the bundled server. Absent, the bundled value. nil is routingOffline: nothing is sent.
public enum APIBaseURL {
    public static let infoPlistKey = "SCENIC_API_BASE_URL"
    public static let overrideKey = "plan.base.url"

    public static func resolve(bundled: String?, override: String?) -> URL? {
        if let override { return parse(override) }
        return parse(bundled)
    }

    /// Exactly `https`, a non-empty host, no user, password, query or fragment, no whitespace (a typo is refused, not
    /// repaired); trailing slashes are dropped so every client's `appendingPathComponent` composes the same URL.
    static func parse(_ text: String?) -> URL? {
        guard var text, !text.contains(where: { $0.isWhitespace }) else { return nil }
        while text.hasSuffix("/") { text.removeLast() }
        guard let parts = URLComponents(string: text), parts.scheme == "https",
              let host = parts.host, !host.isEmpty, parts.user == nil, parts.password == nil,
              parts.query == nil, parts.fragment == nil, let url = parts.url
        else { return nil }
        return url
    }
}
