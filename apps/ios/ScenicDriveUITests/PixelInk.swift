import UIKit

/// What an element's own screenshot shows: how much of it is NOT its one most common colour, and how light that
/// colour is (T-0180, rulings R5(c) and R6).
///
/// A view drawn over an element - a shape, a colour, a material - or the element at `.opacity(0)` carries no
/// accessibility element of its own, so neither `isHittable` nor a frame comparison can see it; what it leaves is a
/// field of one colour where the text was. Text on its ground leaves glyph and anti-aliasing pixels. The edge
/// `inset` is skipped so that a cover whose bounds land on a fractional pixel cannot pass on its blended border.
struct PixelInk {
    /// The share of the inset image's pixels whose RGBA differs from the dominant RGBA, 0...1.
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
        let red = Double((dominant.key >> 24) & 0xFF) / 255
        let green = Double((dominant.key >> 16) & 0xFF) / 255
        let blue = Double((dominant.key >> 8) & 0xFF) / 255
        self.init(fraction: Double(total - dominant.value) / Double(total),
                  luminance: 0.2126 * red + 0.7152 * green + 0.0722 * blue,
                  size: "\(width)x\(height)")
    }

    private init(fraction: Double, luminance: Double, size: String) {
        offDominantFraction = fraction
        dominantLuminance = luminance
        pixelSize = size
    }
}
