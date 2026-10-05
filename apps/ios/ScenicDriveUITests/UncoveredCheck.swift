import XCTest

/// "On screen, hittable and not covered by another element" as three limbs, every one required (T-0180, ruling R5).
///
/// (a) the element exists, `isHittable` (XCTest's accessibility hit test at its hit point), and its frame is
///     non-empty and inside the window;
/// (b) in ONE snapshot of the whole tree, no element carrying an identifier in the app's own namespaces intersects it
///     by more than 1 pt square - except the element's own subtree and the ancestors WHITELISTED by the caller
///     (`home.sheet` around `home.conditions`); everything this app draws in front of the map is identified there;
/// (c) its own screenshot is not one flat colour (`PixelInk`): a shape or colour drawn over it, or `.opacity(0)`,
///     has no accessibility element, so (a) and (b) are blind to it and only the pixels show it.
@MainActor
struct UncoveredCheck {
    /// The identifier namespaces the app draws in front of the map. MapLibre's own views are behind them by the
    /// screen's ZStack order and carry none of these prefixes.
    static let namespaces = ["home.", "attribution."]

    /// At least this share of the element's pixels must differ from its dominant colour.
    static let minimumInk = 0.01

    let app: XCUIApplication

    /// Assert (a), (b) and (c) for `id`; returns the element's `PixelInk` for the caller's theme check, or nil when
    /// the element never appeared.
    @discardableResult
    func assertUncovered(_ id: String, ancestors: Set<String>, context: String,
                         file: StaticString = #filePath, line: UInt = #line) -> PixelInk? {
        let element = HomeLaunch.element(app, id)
        guard element.waitForExistence(timeout: 15) else {
            XCTFail("\(id) does not exist (\(context))", file: file, line: line)
            return nil
        }
        let frame = element.frame
        let window = app.windows.firstMatch.frame
        XCTAssertTrue(element.isHittable, "\(id) is not hittable (\(context)), frame \(frame)", file: file, line: line)
        XCTAssertFalse(frame.isEmpty, "\(id) has an empty frame (\(context))", file: file, line: line)
        XCTAssertTrue(window.insetBy(dx: -0.5, dy: -0.5).contains(frame),
                      "\(id) frame \(frame) is not inside the window \(window) (\(context))", file: file, line: line)

        let covering = coveringElements(of: id, frame: frame, ancestors: ancestors)
        XCTAssertEqual(covering, [], "\(id) at \(frame) is covered by identified elements (\(context))",
                       file: file, line: line)

        let ink = PixelInk(image: element.screenshot().image)
        XCTAssertGreaterThanOrEqual(ink.offDominantFraction, Self.minimumInk,
                                    "\(id) renders as one flat colour - covered, or not drawn (\(context)): "
                                        + "\(ink.offDominantFraction) of \(ink.pixelSize) off the dominant colour",
                                    file: file, line: line)
        return ink
    }

    /// Every identified element in the app's namespaces, outside `id`'s subtree and the whitelisted ancestors,
    /// whose frame overlaps `frame` by more than 1 pt square - read from one snapshot.
    private func coveringElements(of id: String, frame: CGRect, ancestors: Set<String>) -> [String] {
        guard let root = try? app.snapshot() else {
            return ["the accessibility snapshot failed"]
        }
        var found: [String] = []
        walk(root, insideTarget: false, id: id, frame: frame, ancestors: ancestors, into: &found)
        return found
    }

    private func walk(_ node: XCUIElementSnapshot, insideTarget: Bool, id: String, frame: CGRect,
                      ancestors: Set<String>, into found: inout [String]) {
        let identifier = node.identifier
        let inside = insideTarget || identifier == id
        if !inside, !ancestors.contains(identifier),
           Self.namespaces.contains(where: { identifier.hasPrefix($0) }) {
            let overlap = node.frame.intersection(frame)
            if !overlap.isNull, overlap.width * overlap.height > 1 {
                found.append("\(identifier) at \(node.frame)")
            }
        }
        for child in node.children {
            walk(child, insideTarget: inside, id: id, frame: frame, ancestors: ancestors, into: &found)
        }
    }
}
