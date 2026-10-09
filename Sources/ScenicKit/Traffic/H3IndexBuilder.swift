import Foundation

/// `_faceIjkToH3` of uber/h3 v4.1.0 (src/h3lib/lib/h3Index.c) with the digit rotations it calls: walks a
/// face's ijk+ coordinate up to resolution 0 one aperture-7 step at a time, recording one digit per step, looks
/// the base cell up in H3BaseCells, and rotates the digits into that base cell's orientation - with the
/// pentagon rules, because twelve base cells have no digit-1 (k axis) child. Apache-2.0, see CorridorCell.swift (a copy of Telemetry's file of this name, T-0325 R1).
enum H3IndexBuilder {
    /// `H3_INIT`: mode, resolution and base cell zero, all fifteen digits 7 (unused).
    static let initial: UInt64 = 0x1FFF_FFFF_FFFF
    /// `H3_CELL_MODE` at `H3_MODE_OFFSET` 59, the resolution at 52, the base cell at 45.
    static let cellMode: UInt64 = 1 << 59
    /// `MAX_FACE_COORD`: a res-0 ijk+ component above 2 lies off the face table.
    static let maxFaceCoord = 2
    /// `K_AXES_DIGIT`: the digit a pentagon does not have.
    static let kAxesDigit = 1

    /// The 64-bit H3 index of the cell at `coord` on `face`, or nil when the coordinate leaves the face table.
    static func index(face: Int, coord: H3CoordIJK, resolution: Int) -> UInt64? {
        var ijk = coord
        // digits[r] is the digit at resolution r; digits[0] is unused, as in H3_GET_INDEX_DIGIT.
        var digits = [Int](repeating: 7, count: resolution + 1)
        var r = resolution - 1
        while r >= 0 {
            let last = ijk
            var center: H3CoordIJK
            if (r + 1) % 2 == 1 {
                ijk.upAp7()
                center = ijk
                center.downAp7()
            } else {
                ijk.upAp7r()
                center = ijk
                center.downAp7r()
            }
            digits[r + 1] = last.digit(from: center)
            r -= 1
        }
        guard ijk.i <= maxFaceCoord, ijk.j <= maxFaceCoord, ijk.k <= maxFaceCoord else { return nil }
        let (baseCell, rotations) = H3BaseCells.entry(face: face, coord: ijk)
        if H3BaseCells.isPentagon(baseCell) {
            if leadingNonZeroDigit(digits) == kAxesDigit {
                digits = H3BaseCells.isClockwiseOffset(baseCell, face: face)
                    ? digits.map(rotate60cw) : rotate60ccw(digits)
            }
            for _ in 0..<rotations {
                digits = rotatePentagon60ccw(digits)
            }
        } else {
            for _ in 0..<rotations {
                digits = rotate60ccw(digits)
            }
        }
        var h = initial | cellMode | UInt64(resolution) << 52 | UInt64(baseCell) << 45
        for res in stride(from: 1, through: resolution, by: 1) {
            let offset = UInt64((15 - res) * 3)
            h = (h & ~(UInt64(7) << offset)) | UInt64(digits[res]) << offset
        }
        return h
    }

    /// `_h3LeadingNonZeroDigit`.
    static func leadingNonZeroDigit(_ digits: [Int]) -> Int {
        digits.dropFirst().first { $0 != 0 } ?? 0
    }

    /// `_h3Rotate60ccw` over the digits.
    static func rotate60ccw(_ digits: [Int]) -> [Int] {
        [digits[0]] + digits.dropFirst().map(rotate60ccw)
    }

    /// `_h3RotatePent60ccw`: a 60-degree ccw rotation that, on reaching the first non-zero digit, rotates
    /// once more if that digit landed on the deleted k axis.
    static func rotatePentagon60ccw(_ digits: [Int]) -> [Int] {
        var out = digits
        var foundFirstNonZero = false
        for res in out.indices.dropFirst() {
            out[res] = rotate60ccw(out[res])
            if !foundFirstNonZero && out[res] != 0 {
                foundFirstNonZero = true
                if leadingNonZeroDigit(out) == kAxesDigit {
                    out = rotate60ccw(out)
                }
            }
        }
        return out
    }

    /// `_rotate60ccw` (coordijk.c) on one digit: k -> ik -> i -> ij -> j -> jk -> k; 0 stays 0.
    static func rotate60ccw(_ digit: Int) -> Int {
        switch digit {
        case 1: return 5
        case 5: return 4
        case 4: return 6
        case 6: return 2
        case 2: return 3
        case 3: return 1
        default: return digit
        }
    }

    /// `_rotate60cw` (coordijk.c) on one digit: k -> jk -> j -> ij -> i -> ik -> k; 0 stays 0.
    static func rotate60cw(_ digit: Int) -> Int {
        switch digit {
        case 1: return 3
        case 3: return 2
        case 2: return 6
        case 6: return 4
        case 4: return 5
        case 5: return 1
        default: return digit
        }
    }
}
