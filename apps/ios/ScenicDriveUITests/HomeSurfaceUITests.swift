import XCTest

/// The runtime half of P-SAFE-03's persistent line and P-ATTR-01's credit (T-0180, acceptance 3): `home.conditions`
/// and the map credit pill `attribution.footer` are on screen, hittable and not covered (`UncoveredCheck`) at BOTH
/// home sheet detents, in BOTH themes - what a source whitelist cannot prove (T-0237 rv1/rv2: a detent-gated
/// summary, an opacity on the conditions line, an overlay over the credit).
///
/// One test per detent and theme, so a red names the combination. The theme is `XCUIDevice.shared.appearance`
/// (ruling R6) and is SEEN to take: the conditions line's dominant colour - the sheet's ground - is light in light
/// and dark in dark. The detent is SEEN to take as well: `home.route` exists at medium and not at collapsed.
final class HomeSurfaceUITests: XCTestCase {
    @MainActor
    func testConditionsAndCreditUncoveredCollapsedLight() {
        assertSurface(detent: "collapsed", appearance: .light)
    }

    @MainActor
    func testConditionsAndCreditUncoveredCollapsedDark() {
        assertSurface(detent: "collapsed", appearance: .dark)
    }

    @MainActor
    func testConditionsAndCreditUncoveredMediumLight() {
        assertSurface(detent: "medium", appearance: .light)
    }

    @MainActor
    func testConditionsAndCreditUncoveredMediumDark() {
        assertSurface(detent: "medium", appearance: .dark)
    }

    @MainActor
    private func assertSurface(detent: String, appearance: XCUIDevice.Appearance,
                               file: StaticString = #filePath, line: UInt = #line) {
        continueAfterFailure = true
        XCUIDevice.shared.appearance = appearance
        let dark = appearance == .dark
        let context = "\(detent) detent, \(dark ? "dark" : "light")"
        let app = HomeLaunch.launch(detent: detent)

        let route = HomeLaunch.element(app, "home.route")
        if detent == "medium" {
            XCTAssertTrue(route.waitForExistence(timeout: 20), "the medium detent did not take (\(context))",
                          file: file, line: line)
        } else {
            XCTAssertTrue(HomeLaunch.element(app, "home.title").waitForExistence(timeout: 20),
                          "the sheet never appeared (\(context))", file: file, line: line)
            XCTAssertFalse(route.exists, "the collapsed detent shows the details (\(context))", file: file, line: line)
        }

        let check = UncoveredCheck(app: app)
        let conditions = check.assertUncovered("home.conditions", ancestors: ["home.sheet"], context: context,
                                               file: file, line: line)
        check.assertUncovered("attribution.footer", ancestors: [], context: context, file: file, line: line)

        if let conditions {
            if dark {
                XCTAssertLessThan(conditions.dominantLuminance, 0.5,
                                  "the dark appearance did not take: the sheet's ground has luminance "
                                      + "\(conditions.dominantLuminance) (\(context))", file: file, line: line)
            } else {
                XCTAssertGreaterThan(conditions.dominantLuminance, 0.5,
                                     "the light appearance did not take: the sheet's ground has luminance "
                                         + "\(conditions.dominantLuminance) (\(context))", file: file, line: line)
            }
        }
    }
}
