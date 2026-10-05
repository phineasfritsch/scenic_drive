import UIKit

/// What an element's own screenshot shows: how much of it is NOT its one most common colour, and how light that
/// colour is (T-0180, rulings R5(c) and R6).
///
/// A view drawn over an element - a shape, a colour, a material - or the element at `.opacity(0)` carries no
/// accessibility element of its own, so neither `isHittable` nor a frame comparison can see it; what it leaves is a
/// field of one colour where the text was. Text on its ground leaves glyph and anti-aliasing pixels. The edge
/// `inset` is skipped so that a cover whose bounds land on a fractional pixel cannot pass on its blended border.
///
/// A pixel counts as ink only when some channel differs from the dominant colour by MORE than `tolerance` levels:
/// the screenshot is converted to 8-bit sRGB and a flat field comes back with conversion noise of a level or two.
/// Exact equality read that noise as ink - mutant m3's opaque red overlay over the credit passed (run 37298802427)
/// and m2's invisible conditions line scored 0.0096 against a 0.01 floor (run 37298568886) - ruling R15.
struct PixelInk {
    /// Channel levels (of 255) a pixel must differ from the dominant colour by to count as ink.
    static let tolerance = 48

    /// The share of the inset image's pixels that are ink (see `tolerance`), 0...1.
    let offDominantFraction: Double

    /// The relative luminance (Rec. 709) of the dominant colour, 0...1, or -1 when the image could not be read.
    let dominantLuminance: Double

    /// The image's size in pixels, for the failure message.
    let pixelSize: String

    init(image: UIImage, inset: Int = 3) {
        guard let cg = image.cgImage else {
            self.init(fraction: 0, luminance: -1, size: "unreadable")
            return
        }
        let width = cg.width
        let height = cg.height
        var bytes = [UInt8](repeating: 0, count: width * height * 4)
        let drawn: Bool = bytes.withUnsafeMutableBytes { buffer in
            guard let context = CGContext(data: buffer.baseAddress, width: width, height: height,
                                          bitsPerComponent: 8, bytesPerRow: width * 4,
                                          space: CGColorSpaceCreateDeviceRGB(),
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
                return false
            }
            context.draw(cg, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard drawn, width > 2 * inset, height > 2 * inset else {
            self.init(fraction: 0, luminance: -1, size: "\(width)x\(height)")
            return
        }
        var counts: [UInt32: Int] = [:]
        for y in inset..<(height - inset) {
            for x in inset..<(width - inset) {
                let i = (y * width + x) * 4
                let rgba = UInt32(bytes[i]) << 24 | UInt32(bytes[i + 1]) << 16 | UInt32(bytes[i + 2]) << 8 | UInt32(bytes[i + 3])
                counts[rgba, default: 0] += 1
            }
        }
        let total = (width - 2 * inset) * (height - 2 * inset)
        let dominant = counts.max { $0.value < $1.value } ?? (key: 0, value: total)
        let channels = [Int((dominant.key >> 24) & 0xFF), Int((dominant.key >> 16) & 0xFF), Int((dominant.key >> 8) & 0xFF)]
        var ink = 0
        for (rgba, count) in counts {
            let far = [Int((rgba >> 24) & 0xFF), Int((rgba >> 16) & 0xFF), Int((rgba >> 8) & 0xFF)]
                .enumerated().contains { abs($0.element - channels[$0.offset]) > Self.tolerance }
            if far {
                ink += count
            }
        }
        let red = Double(channels[0]) / 255
        let green = Double(channels[1]) / 255
        let blue = Double(channels[2]) / 255
        self.init(fraction: Double(ink) / Double(total),
                  luminance: 0.2126 * red + 0.7152 * green + 0.0722 * blue,
                  size: "\(width)x\(height)")
    }

    private init(fraction: Double, luminance: Double, size: String) {
        offDominantFraction = fraction
        dominantLuminance = luminance
        pixelSize = size
    }
}
