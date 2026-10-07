import Foundation
import ScenicKit
import SwiftUI

/// The planned line as an outline, fitted to its frame with longitude scaled by the cosine of the mean latitude.
/// Not a map: no tiles, so no second basemap surface (T-0294 R6).
struct PlanRouteShape: Shape {
    let route: [Coordinate]

    func path(in rect: CGRect) -> Path {
        var path = Path()
        guard let first = route.first else { return path }
        let box = rect.insetBy(dx: 8, dy: 8)
        let lats = route.map(\.latitude)
        let lons = route.map(\.longitude)
        let minLat = lats.min() ?? 0, maxLat = lats.max() ?? 0
        let minLon = lons.min() ?? 0, maxLon = lons.max() ?? 0
        let shrink = cos((minLat + maxLat) / 2 * .pi / 180)
        let width = max((maxLon - minLon) * shrink, 1e-9)
        let height = max(maxLat - minLat, 1e-9)
        let scale = min(box.width / width, box.height / height)
        let left = box.midX - width * scale / 2
        let top = box.midY - height * scale / 2
        func point(_ c: Coordinate) -> CGPoint {
            CGPoint(x: left + (c.longitude - minLon) * shrink * scale, y: top + (maxLat - c.latitude) * scale)
        }
        path.move(to: point(first))
        for c in route.dropFirst() {
            path.addLine(to: point(c))
        }
        return path
    }
}
