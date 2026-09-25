"""Draw the Scenic Drive app icon. The SOURCE OF TRUTH for the PNG is this file, not the PNG.

    python ops/lib/make-app-icon.py
    python ops/lib/make-app-icon.py --out PATH --size N      # the check's mutation table hands a 512

Re-running it on the committed tree must leave `git status --short` empty: the output is a pure function of
the literals below. Nothing here reads a clock, an environment variable, a directory listing or an RNG;
Pillow writes no tIME and no text chunk unless handed a `pnginfo`, and none is; `optimize=False` with a
pinned `compress_level` stops Pillow's optimiser choosing a filter set. The drawing is supersampled 4x and
reduced once with LANCZOS, which is a pure function of the pixels above it.

THE SUBJECT (T-0234 ruling R2): a Los Angeles canyon road climbing toward layered ridges under a warm late
sky - the Santa Monica Mountains read, since that is what this product plans drives through. Flat shapes,
full bleed, no rounding (iOS masks the superellipse itself), RGB with NO alpha channel (App Store Connect
rejects an icon that carries one), no text, no photograph, and deliberately no Apple trade dress: no pin, no
beige map field, no chevron, no compass, no road sign.

EVERY COLOUR IS A DesignTokens VALUE, quoted from
apps/ios/Packages/ScenicApp/Sources/DesignSystem/DesignTokens.swift with its token and its column. No third
colour is invented; see TOKENS below.
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image, ImageDraw

# --- the palette: token -> (column, hex) exactly as DesignTokens.swift declares it -------------------
TOKENS = {
    "sky": ("bg", "light", (0xFF, 0xF7, 0xED)),  # #FFF7ED  the warm ground the app paints
    "sun": ("primary", "light", (0xEA, 0x58, 0x0C)),  # #EA580C
    "ridge_far": ("fgMuted", "dark", (0x94, 0xA3, 0xB8)),  # #94A3B8  haze on the far range
    "ridge_mid": ("hazard", "light", (0xB4, 0x53, 0x09)),  # #B45309  the sunlit slope
    "ridge_near": ("scenic", "light", (0x15, 0x80, 0x3D)),  # #15803D  the green hill the road climbs
    "road": ("surface", "light", (0xFF, 0xFF, 0xFF)),  # #FFFFFF
    "road_casing": ("route", "light", (0x25, 0x63, 0xEB)),  # #2563EB  the app's own route line
}

DEFAULT_OUT = "apps/ios/ScenicDrive/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
DEFAULT_SIZE = 1024
SUPERSAMPLE = 4
COMPRESS_LEVEL = 9

# Geometry is written as fractions of the square, so the same literals draw any size. The three ridges never
# cross: far max 0.50 < mid min 0.52, mid max 0.63 < near min 0.665, which is what makes the layering read.
RIDGE_FAR = [(0.00, 0.50), (0.14, 0.44), (0.30, 0.49), (0.46, 0.40), (0.62, 0.47), (0.80, 0.42), (1.00, 0.48)]
RIDGE_MID = [(0.00, 0.62), (0.18, 0.55), (0.34, 0.61), (0.52, 0.52), (0.70, 0.60), (0.86, 0.56), (1.00, 0.63)]
RIDGE_NEAR = [(0.00, 0.78), (0.20, 0.72), (0.40, 0.69), (0.55, 0.665), (0.72, 0.70), (0.88, 0.74), (1.00, 0.79)]

SUN_CENTRE = (0.34, 0.30)
SUN_RADIUS = 0.125

# One quadratic bend, from the bottom edge to just under the saddle in RIDGE_NEAR at x = 0.55. The road ends
# at 0.710, 46 of 1024 pixels below the 0.665 crest, so the casing cannot poke through the silhouette, and
ROAD_P0 = (0.34, 1.14)
ROAD_P1 = (0.72, 0.90)
ROAD_P2 = (0.545, 0.710)
# it starts at y = 1.14, off the bottom edge, so its square start cap never notches the corner.
ROAD_STEPS = 240
# Half-widths and the casing in 1024-pixel units: 230 px of road where the ribbon starts, 46 px where it crests
# (5.4 px at 40 pt @3x), 18 px of casing per side (2.1 px) - a visible dark edge, not a dissolving detail.
ROAD_HALF_NEAR_PX = 115.0
ROAD_HALF_FAR_PX = 23.0
ROAD_CASING_PX = 18.0
PX_BASIS = 1024.0


def _quad(t: float) -> tuple[float, float]:
    """The road's centreline at t, as a quadratic Bezier over ROAD_P0/P1/P2."""
    u = 1.0 - t
    x = u * u * ROAD_P0[0] + 2 * u * t * ROAD_P1[0] + t * t * ROAD_P2[0]
    y = u * u * ROAD_P0[1] + 2 * u * t * ROAD_P1[1] + t * t * ROAD_P2[1]
    return x, y


def _ribbon(half_near: float, half_far: float) -> list[tuple[float, float]]:
    """The road as one closed polygon: the left offset forward, the right offset back."""
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i in range(ROAD_STEPS + 1):
        t = i / float(ROAD_STEPS)
        x, y = _quad(t)
        # Tangent by a fixed central difference - a literal step, so the same numbers every run.
        ax, ay = _quad(max(0.0, t - 0.002))
        bx, by = _quad(min(1.0, t + 0.002))
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        half = half_near + (half_far - half_near) * t
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left + right[::-1]


def _ridge(crest: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """A crest line closed down the two sides to the bottom edge."""
    return crest + [(1.0, 1.2), (0.0, 1.2)]


def draw(side: int) -> Image.Image:
    """The whole drawing at `side` pixels, painted back to front."""
    img = Image.new("RGB", (side, side), TOKENS["sky"][2])
    pen = ImageDraw.Draw(img)

    def scale(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(x * side, y * side) for x, y in points]

    cx, cy = SUN_CENTRE[0] * side, SUN_CENTRE[1] * side
    r = SUN_RADIUS * side
    pen.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TOKENS["sun"][2])

    pen.polygon(scale(_ridge(RIDGE_FAR)), fill=TOKENS["ridge_far"][2])
    pen.polygon(scale(_ridge(RIDGE_MID)), fill=TOKENS["ridge_mid"][2])
    pen.polygon(scale(_ridge(RIDGE_NEAR)), fill=TOKENS["ridge_near"][2])

    casing = ROAD_CASING_PX / PX_BASIS
    pen.polygon(
        scale(_ribbon(ROAD_HALF_NEAR_PX / PX_BASIS + casing, ROAD_HALF_FAR_PX / PX_BASIS + casing)),
        fill=TOKENS["road_casing"][2],
    )
    pen.polygon(
        scale(_ribbon(ROAD_HALF_NEAR_PX / PX_BASIS, ROAD_HALF_FAR_PX / PX_BASIS)),
        fill=TOKENS["road"][2],
    )
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description="Draw the Scenic Drive app icon deterministically.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="where to write the PNG (default: %s)" % DEFAULT_OUT)
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE, help="edge in pixels (default: 1024)")
    args = ap.parse_args()

    if args.size < 8:
        print("make-app-icon: --size %d is not a drawable icon" % args.size)
        return 2

    big = draw(args.size * SUPERSAMPLE)
    img = big.resize((args.size, args.size), Image.LANCZOS)
    parent = os.path.dirname(args.out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # RGB, so the PNG's IHDR colour type is 2: no alpha channel, which App Store Connect rejects.
    img.save(args.out, format="PNG", optimize=False, compress_level=COMPRESS_LEVEL)
    print("make-app-icon: wrote %s at %dx%d (RGB, compress_level=%d)"
          % (args.out, args.size, args.size, COMPRESS_LEVEL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
