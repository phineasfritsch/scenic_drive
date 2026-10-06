/**
 * The one location telemetry may carry: an H3 resolution-5 cell (P-PRIV-05, T-0265 R3), checked from its bit
 * layout as uber/h3 v4's isValidCell does at resolution 5 (T-0279 R4). Sources/Telemetry/H3Cell.swift writes the
 * cell; this module only recognises one - it never decodes a cell to a point.
 */

/** h3ToString's form of a resolution-5 cell: mode 1 and resolution 5 make the index 15 lowercase hex digits. */
const HEX15 = /^[0-9a-f]{15}$/;

/** The 122 base cells are 0...121; these twelve are pentagons, which have no digit-1 (k axis) child. */
export const MAX_BASE_CELL = 121;
export const PENTAGON_BASE_CELLS: readonly number[] = [4, 14, 24, 38, 49, 58, 63, 72, 83, 97, 107, 117];

/** The H3 digit of resolution `r` (1...15) of an index. */
function digit(index: bigint, r: number): number {
  return Number((index >> BigInt((15 - r) * 3)) & 7n);
}

/** True exactly when `cell` is the h3ToString form of a valid resolution-5 H3 cell. */
export function isResolution5Cell(cell: string): boolean {
  if (!HEX15.test(cell)) return false;
  const index = BigInt(`0x${cell}`);
  // Fifteen digits leave bits 60-63 zero, so the reserved bit 63 holds and the mode (bits 59-62) is bit 59 alone.
  if (((index >> 59n) & 15n) !== 1n) return false;
  if (((index >> 56n) & 7n) !== 0n) return false;
  if (((index >> 52n) & 15n) !== 5n) return false;
  const base = Number((index >> 45n) & 127n);
  if (base > MAX_BASE_CELL) return false;
  for (let r = 1; r <= 5; r++) if (digit(index, r) > 6) return false;
  for (let r = 6; r <= 15; r++) if (digit(index, r) !== 7) return false;
  if (PENTAGON_BASE_CELLS.includes(base)) {
    for (let r = 1; r <= 5; r++) {
      const d = digit(index, r);
      if (d === 0) continue;
      return d !== 1;
    }
  }
  return true;
}
