import SwiftUI
import UIKit

/// The plan's semantic colour tokens, both appearances, as the single source of truth for colour.
///
/// The plan specifies these as an Asset Catalog with semantic names only. They are code here because
/// this package is authored without Xcode: an `.xcassets` bundle is a directory of JSON files that no
/// tool in this repository can validate, so a typo in it would be invisible until a device build,
/// while a typo here is a compile error in the first Xcode Cloud run. The catalog can replace this
/// type later without any call site changing.
///
/// Every value below is the plan's table verbatim (light / dark):
///
///     bg           #FFF7ED  #0F172A   ground
///     surface      #FFFFFF  #192134   cards/sheets
///     fg           #0F172A  #F8FAFC   body
///     fgMuted      #64748B  #94A3B8   secondary
///     primary      #EA580C  #FB923C   buttons
///     onPrimary    #FFFFFF  #0F172A
///     route        #2563EB  #3B82F6   route line 6 pt, 2 pt casing
///     scenic       #15803D  #4ADE80   episode highlights
///     hazard       #B45309  #FBBF24   hazard strip
///     destructive  #DC2626  #F87171
///     border       #FCEAE1  rgba(255,255,255,0.08)
///
/// - Important: **`primary` is never body text on `bg`.** It is a button fill and an accent, nothing
///   else. `#EA580C` on `#FFF7ED` is roughly 3.6:1, which passes for a 44 pt control and fails WCAG AA
///   for body copy; the dark pair `#FB923C` on `#0F172A` fails in the other direction for anything
///   small. Body text is `fg`, secondary text is `fgMuted`, and text on a `primary` fill is
///   `onPrimary`. A screen that reaches for `primary` to make a sentence look important is the one
///   this note exists to stop.
public enum DesignTokens {
    /// Ground. The lowest surface on any screen.
    public static let bg = dynamic(light: 0xFFF7ED, dark: 0x0F172A)

    /// Cards and sheets, one step above `bg`.
    public static let surface = dynamic(light: 0xFFFFFF, dark: 0x192134)

    /// Body text.
    public static let fg = dynamic(light: 0x0F172A, dark: 0xF8FAFC)

    /// Secondary text: captions, footnotes, attribution.
    public static let fgMuted = dynamic(light: 0x64748B, dark: 0x94A3B8)

    /// Button fills and accents. See the type note: never body text on `bg`.
    public static let primary = dynamic(light: 0xEA580C, dark: 0xFB923C)

    /// Text and symbols drawn on top of a `primary` fill.
    public static let onPrimary = dynamic(light: 0xFFFFFF, dark: 0x0F172A)

    /// The route line: 6 pt stroke over a 2 pt casing.
    public static let route = dynamic(light: 0x2563EB, dark: 0x3B82F6)

    /// Scenic episode highlights along the route.
    public static let scenic = dynamic(light: 0x15803D, dark: 0x4ADE80)

    /// The hazard strip. Warning, not error - `destructive` is the error colour.
    public static let hazard = dynamic(light: 0xB45309, dark: 0xFBBF24)

    /// Destructive actions: delete account, discard a plan.
    public static let destructive = dynamic(light: 0xDC2626, dark: 0xF87171)

    /// Hairlines and separators.
    ///
    /// The only token whose dark value is not a hex triple. The plan writes it `rgba(255,255,255,0.08)`
    /// - a translucent white that picks up whatever sits behind it, which is the point of a hairline on
    /// a dark surface. Flattening it to an opaque approximation would look right on `bg` and wrong on
    /// every card, so the alpha is kept.
    public static let border = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(white: 1.0, alpha: 0.08)
            : DesignTokens.srgb(0xFCEAE1)
    })

    // MARK: - Construction

    /// One token from its light and dark hex triples.
    ///
    /// A `UIColor` dynamic provider rather than two separate colours chosen at read time: the provider
    /// is re-resolved by UIKit whenever the trait collection changes, so a token captured once in a
    /// stored property still flips when the user switches appearance mid-session. Reading
    /// `colorScheme` at the call site instead would freeze whatever was current when the view was
    /// built.
    private static func dynamic(light: UInt32, dark: UInt32) -> Color {
        Color(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark ? srgb(dark) : srgb(light)
        })
    }

    /// `0xRRGGBB` as an sRGB colour.
    ///
    /// Explicitly sRGB, not `displayP3`: the plan's table is web hex, and the same digits read as P3
    /// are a visibly more saturated colour - `#EA580C` most of all.
    private static func srgb(_ hex: UInt32, alpha: CGFloat = 1) -> UIColor {
        UIColor(red: CGFloat((hex >> 16) & 0xFF) / 255.0,
                green: CGFloat((hex >> 8) & 0xFF) / 255.0,
                blue: CGFloat(hex & 0xFF) / 255.0,
                alpha: alpha)
    }
}
