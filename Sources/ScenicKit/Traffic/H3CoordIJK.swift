import Foundation

/// ijk+ coordinates on one icosahedron face: uber/h3 v4.1.0's `CoordIJK` and the functions of
/// src/h3lib/lib/coordijk.c that `latLngToCell` runs - nothing else of that file is ported. Apache-2.0, see
/// CorridorCell.swift (a copy of Telemetry's file of this name, T-0325 R1). Each method names the C function it is, so the port can be read against the source.
struct H3CoordIJK: Equatable, Sendable {
    var i: Int
    var j: Int
    var k: Int

    /// sin(60 degrees), `M_SIN60` in constants.h.
    static let sin60 = 0.8660254037844386467637231707529361834714

    init(i: Int, j: Int, k: Int) {
        self.i = i
        self.j = j
        self.k = k
    }

    /// `_hex2dToCoordIJK`: the ijk+ coordinates of the hex containing a 2D hex-grid point.
    init(hex2dX x: Double, y: Double) {
        let a1 = abs(x)
        let a2 = abs(y)
        let x2 = a2 / Self.sin60
        let x1 = a1 + x2 / 2.0
        let m1 = Int(x1)
        let m2 = Int(x2)
        let r1 = x1 - Double(m1)
        let r2 = x2 - Double(m2)
        var i: Int
        var j: Int
        if r1 < 0.5 {
            if r1 < 1.0 / 3.0 {
                i = m1
                j = r2 < (1.0 + r1) / 2.0 ? m2 : m2 + 1
            } else {
                j = r2 < 1.0 - r1 ? m2 : m2 + 1
                i = (1.0 - r1) <= r2 && r2 < 2.0 * r1 ? m1 + 1 : m1
            }
        } else {
            if r1 < 2.0 / 3.0 {
                j = r2 < 1.0 - r1 ? m2 : m2 + 1
                i = (2.0 * r1 - 1.0) < r2 && r2 < 1.0 - r1 ? m1 : m1 + 1
            } else {
                i = m1 + 1
                j = r2 < r1 / 2.0 ? m2 : m2 + 1
            }
        }
        // Fold across the axes if necessary.
        if x < 0.0 {
            if j % 2 == 0 {
                let diff = i - j / 2
                i -= 2 * diff
            } else {
                let diff = i - (j + 1) / 2
                i -= 2 * diff + 1
            }
        }
        if y < 0.0 {
            i -= (2 * j + 1) / 2
            j = -j
        }
        self.init(i: i, j: j, k: 0)
        normalize()
    }

    /// `_ijkNormalize`: no negative component, and at least one component zero.
    mutating func normalize() {
        if i < 0 {
            j -= i
            k -= i
            i = 0
        }
        if j < 0 {
            i -= j
            k -= j
            j = 0
        }
        if k < 0 {
            i -= k
            j -= k
            k = 0
        }
        let low = Swift.min(i, j, k)
        if low > 0 {
            i -= low
            j -= low
            k -= low
        }
    }

    /// `_upAp7`: the parent of this cell in the counter-clockwise aperture-7 grid (Class III to Class II).
    mutating func upAp7() {
        let ci = i - k
        let cj = j - k
        i = Int((Double(3 * ci - cj) / 7.0).rounded())
        j = Int((Double(ci + 2 * cj) / 7.0).rounded())
        k = 0
        normalize()
    }

    /// `_upAp7r`: the parent of this cell in the clockwise aperture-7 grid (Class II to Class III).
    mutating func upAp7r() {
        let ci = i - k
        let cj = j - k
        i = Int((Double(2 * ci + cj) / 7.0).rounded())
        j = Int((Double(3 * cj - ci) / 7.0).rounded())
        k = 0
        normalize()
    }

    /// `_downAp7`: the center child, one finer, counter-clockwise aperture 7.
    mutating func downAp7() {
        let (a, b, c) = (i, j, k)
        i = 3 * a + b
        j = 3 * b + c
        k = a + 3 * c
        normalize()
    }

    /// `_downAp7r`: the center child, one finer, clockwise aperture 7.
    mutating func downAp7r() {
        let (a, b, c) = (i, j, k)
        i = 3 * a + c
        j = a + 3 * b
        k = b + 3 * c
        normalize()
    }

    /// `_unitIjkToDigit` over `_ijkSub`: the H3 digit (0...6) of the unit vector from `center` to `self`,
    /// or 7 (`INVALID_DIGIT`) when the difference is not a unit vector. `UNIT_VECS[d]` is (i, j, k) = the
    /// three bits of d, which is why the digit is read as 4i + 2j + k.
    func digit(from center: H3CoordIJK) -> Int {
        var diff = H3CoordIJK(i: i - center.i, j: j - center.j, k: k - center.k)
        diff.normalize()
        guard (0...1).contains(diff.i), (0...1).contains(diff.j), (0...1).contains(diff.k) else { return 7 }
        return 4 * diff.i + 2 * diff.j + diff.k
    }
}
