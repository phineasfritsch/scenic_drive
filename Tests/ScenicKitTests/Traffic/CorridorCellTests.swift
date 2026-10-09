import Foundation
import Testing
@testable import ScenicKit

/// T-0325 R1: the corridor cell a point is in, from ScenicKit's copy of Telemetry's uber/h3 port, against uber/h3
/// itself - every row of CorridorCellReference (h3-py 4.1.2) compared by exact equality at 8 and at 5.
@Suite("corridor cells are uber/h3 resolution 8 (T-0325)") struct CorridorCellTests {
    @Test("every reference point's cell equals h3-py's latlng_to_cell at resolution 8, and at 5 as Telemetry's")
    func everyReferenceRow() {
        #expect(CorridorCell.resolution == 8)
        #expect(CorridorCellReference.rows.count == 249)
        for row in CorridorCellReference.rows {
            let cell = CorridorCell.containing(latitudeDegrees: row.latitude, longitudeDegrees: row.longitude)
            #expect(cell == CorridorCell(index: row.res8), "res 8 at \(row.latitude), \(row.longitude)")
            let five = CorridorCell.containing(latitudeDegrees: row.latitude, longitudeDegrees: row.longitude,
                                               resolution: 5)
            #expect(five == CorridorCell(index: row.res5), "res 5 at \(row.latitude), \(row.longitude)")
        }
    }

    /// Each bound exactly (a cell, equal to h3-py's) and one ulp outside it (nil), NaN and the infinities nil.
    @Test("latitude -90 and 90 and longitude -180 and 180 are cells; one ulp outside, NaN and infinities are nil")
    func rangeBounds() {
        let north = CorridorCell(index: 0x0880_3262_33bf_ffff)
        let south = CorridorCell(index: 0x088f_2938_0e1f_ffff)
        let east = CorridorCell(index: 0x0887_eb57_221f_ffff)
        let rows: [(Double, Double, CorridorCell?)] = [
            (90, 0, north), (-90, 0, south), (0, 180, east), (0, -180, east),
            (90.0.nextUp, 0, nil), ((-90.0).nextDown, 0, nil), (0, 180.0.nextUp, nil), (0, (-180.0).nextDown, nil),
            (.nan, 0, nil), (0, .nan, nil), (.infinity, 0, nil), (-.infinity, 0, nil), (0, .infinity, nil),
            (0, -.infinity, nil),
        ]
        for (latitude, longitude, expected) in rows {
            #expect(CorridorCell.containing(latitudeDegrees: latitude, longitudeDegrees: longitude) == expected,
                    "\(latitude), \(longitude)")
        }
        // The bound rows' cells are the reference table's own (h3-py), not retyped here.
        let table = Dictionary(CorridorCellReference.rows.map { ("\($0.latitude),\($0.longitude)", $0.res8) },
                               uniquingKeysWith: { first, _ in first })
        #expect(table["90.0,0.0"] == north.index)
        #expect(table["-90.0,0.0"] == south.index)
        #expect(table["0.0,180.0"] == east.index)
        #expect(table["0.0,-180.0"] == east.index)
    }
}
