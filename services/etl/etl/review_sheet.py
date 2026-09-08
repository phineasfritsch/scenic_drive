"""The review sheet: a page of Street View links with the verdict captured next to each one.

A sheet you click through and forget is a nicer way to waste an afternoon, so every row carries a verdict
control and the run refuses rather than emitting an empty page.

Run through `ops/score-review`, which is the documented entry point.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl import streetview as sv  # noqa: E402

# Where the score earns its keep. The extremes are usually obviously right: a page of the highest and lowest
# scores mostly confirms what anyone would guess. The segments that decide whether the index is any good are
# the ones it placed in the MIDDLE, where a small weighting error changes the ranking.
REVIEW_BAND = (4.0, 6.0)


def select(segments: list[dict], top: int, bottom: int,
           band: tuple[float, float] | None) -> list[dict]:
    """Pick which segments to review, tagging each with why it was picked. Never silently truncates."""
    scored = [s for s in segments if isinstance(s.get("score"), (int, float))]
    out: list[dict] = []
    seen: set = set()

    def take(items, why):
        for s in items:
            k = s.get("id")
            if k in seen:
                continue
            seen.add(k)
            out.append({**s, "why": why})

    if band and scored:
        lo, hi = band
        take(sorted((s for s in scored if lo <= s["score"] <= hi), key=lambda s: s["score"]),
             f"band {lo:g}-{hi:g}")
    if top and scored:
        take(sorted(scored, key=lambda s: -s["score"])[:top], "top")
    if bottom and scored:
        take(sorted(scored, key=lambda s: s["score"])[:bottom], "bottom")
    if not scored:
        # No composite score exists yet (T-0029). Reviewing the TERMS is still worth doing - "does this look
        # like a road with 82% canopy" is answerable from a photograph - so fall back rather than emit
        # nothing and call it a clean review.
        take(segments, "unscored")
    return out


def _esc(x) -> str:
    return (str(x).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


CSS = (
    "body{font:15px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:24px;"
    "background:#faf9f5;color:#1c1a17}"
    "h1{font-size:20px;margin:0 0 4px}.sub{color:#6b6459;font-size:13px;margin:0 0 20px;max-width:80ch}"
    "table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #e0dace}"
    "th,td{padding:8px 10px;border-bottom:1px solid #ece7dc;text-align:left;font-size:13.5px;"
    "vertical-align:top}"
    "th{background:#f3efe6;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#6b6459}"
    "a{color:#1a5fb4}.t{font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px;color:#514b42}"
    "td.v{white-space:nowrap}label{margin-right:8px;font-size:12.5px}"
    "@media(prefers-color-scheme:dark){body{background:#15140f;color:#f2ede3}"
    "table{background:#1e1c17;border-color:#38342a}th{background:#252219;color:#9a9184}"
    "td{border-color:#2f2b22}a{color:#8fb0cc}.t,.sub{color:#cfc7b8}}"
)


def render(segments: list[dict], top: int = 0, bottom: int = 0,
           band: tuple[float, float] | None = REVIEW_BAND, title: str = "score review") -> str:
    """Render the sheet, or raise. An empty page must never read as a clean review.

    That refusal is the discipline: an afternoon that ends in "reviewed 0 segments, no problems" is this
    repository's signature defect in its most expensive form.
    """
    if not segments:
        raise ValueError("no segments to review - refusing to emit an empty sheet")
    rows = select(segments, top, bottom, band)
    if not rows:
        raise ValueError(
            f"{len(segments)} segment(s) given but none selected "
            f"(band={band}, top={top}, bottom={bottom}) - widen the selection rather than "
            f"reviewing an empty page")

    out = [
        "<!doctype html>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{_esc(title)}</title>", f"<style>{CSS}</style>",
        f"<h1>{_esc(title)}</h1>",
        f'<p class="sub">{len(rows)} of {len(segments)} segments &middot; '
        f"selection: band={band} top={top} bottom={bottom}. "
        "Each link opens Street View facing <em>along</em> the road at its length-midpoint. "
        "The question is not whether the road is nice &mdash; it is whether it looks like its score.</p>",
        "<table><tr><th>id</th><th>name</th><th>score</th><th>picked</th><th>terms</th>"
        "<th>view</th><th>verdict</th></tr>",
    ]
    for s in rows:
        pts = [(float(p[0]), float(p[1])) for p in (s.get("geometry") or [])]
        if pts:
            url = sv.look_along(pts, sv.midpoint_index(pts))
            link = f'<a href="{_esc(url)}" target="_blank" rel="noopener">look along</a>'
        else:
            link = '<span class="t">no geometry</span>'
        terms = " ".join(
            (f"{k}={v:.2f}" if isinstance(v, (int, float)) else f"{k}={v}")
            for k, v in (s.get("terms") or {}).items())
        sc = f'{s["score"]:.2f}' if isinstance(s.get("score"), (int, float)) else "&mdash;"
        rid = _esc(s.get("id", "?"))
        out.append(
            f'<tr><td class="t">{rid}</td><td>{_esc(s.get("name") or "")}</td>'
            f'<td class="v">{sc}</td><td class="t">{_esc(s["why"])}</td>'
            f'<td class="t">{_esc(terms)}</td><td>{link}</td><td class="v">'
            f'<label><input type="radio" name="v_{rid}" value="right"> right</label>'
            f'<label><input type="radio" name="v_{rid}" value="wrong"> wrong</label>'
            f'<label><input type="radio" name="v_{rid}" value="unsure"> ?</label></td></tr>')
    out.append("</table>")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a:
        print("usage: ops/score-review <segments.json> [--top N] [--bottom N] "
              "[--band LO-HI] [-o out.html]", file=sys.stderr)
        return 2
    src, top, bottom, band, out_path = a[0], 0, 0, REVIEW_BAND, None
    i = 1
    while i < len(a):
        k = a[i]
        try:
            if k == "--top":
                top = int(a[i + 1]); i += 2
            elif k == "--bottom":
                bottom = int(a[i + 1]); i += 2
            elif k == "--band":
                lo, hi = a[i + 1].split("-", 1)
                band = (float(lo), float(hi)); i += 2
            elif k in ("-o", "--out"):
                out_path = a[i + 1]; i += 2
            elif k == "--no-band":
                band = None; i += 1
            else:
                print(f"score-review: unknown argument {k!r}", file=sys.stderr)
                return 2
        except (IndexError, ValueError):
            print(f"score-review: {k} needs a valid value", file=sys.stderr)
            return 2
    try:
        data = json.loads(Path(src).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"score-review: cannot read {src}: {e}", file=sys.stderr)
        return 2
    segs = data.get("segments", []) if isinstance(data, dict) else data
    try:
        html = render(segs, top=top, bottom=bottom, band=band, title=f"score review - {src}")
    except ValueError as e:
        print(f"SCORE-REVIEW REFUSED: {e}", file=sys.stderr)
        return 2
    if out_path:
        Path(out_path).write_text(html, encoding="utf-8", newline="\n")
        print(f"wrote {out_path} ({len(segs)} segments in, {html.count('<tr>') - 1} rows out)")
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
