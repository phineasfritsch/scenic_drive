/// Our own build number, as /config's min_app_build is compared against it (T-0357 R5): CFBundleVersion read as a
/// positive decimal integer within 1...RemoteConfig.maxAppBuild, ASCII digits only; anything else is unknown (nil).
public enum AppBuild {
    public static func parse(_ text: String?) -> Int? {
        guard let text, !text.isEmpty, text.utf8.allSatisfy({ (48...57).contains($0) }), let build = Int(text),
              (1...RemoteConfig.maxAppBuild).contains(build) else { return nil }
        return build
    }
}
