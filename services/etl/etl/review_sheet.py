"""The review sheet: a page of Street View links with a verdict control beside each one.

The run refuses rather than emitting an empty or a truncated page - a sheet that reports "reviewed 0
segments, no problems", or renders one row out of four hundred, is the expensive form of this repository's
signature defect.

WHAT IT DOES NOT DO, AND THE PAGE SAYS SO. The verdict controls are radios and nothing reads them: no form,
no script, no file. Click thirty and close the tab and thirty verdicts are gone, which is the failure the
brief wanted this tool to end. Recording them - and seeding the rows from term disagreements - is [[T-0117]].
Until that lands the sheet prints `NOT_RECORDED_NOTICE` at the top, because a page that looks like it is
capturing an afternoon of judgements and is not is worse than one that admits it.

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

# Printed on every sheet for as long as the radios go nowhere. The controls look exactly like controls that
# save, and a reviewer who believes them loses the whole afternoon at the moment they close the tab. Deleted
# by whoever closes [[T-0117]]; `test_the_sheet_does_not_pretend_to_record_the_verdict` allows either the
# notice or a real recording mechanism, and fails only if the page starts lying.
NOT_RECORDED_NOTICE = (
    "Verdicts on this page are <strong>not recorded anywhere</strong>: nothing here writes them to a file, "
    "so closing the tab loses them. Writing them out for the score tuning is T-0117. Until then the radios "
    "are a place to keep your eye, and the answers have to be written down somewhere else.")


def _position_key(i: int, s: dict) -> object:
    """Which segment this is, for deduplication - its POSITION in the input, never its `id`.

    `id` was the first draft's key and it collapsed corpora, because nothing establishes that `id` is
    unique per SEGMENT. Six pieces of one OSM way all keyed `w/12` deduplicated to one row; five segments
    with no `id` field shared `k = None` and also deduplicated to one - a corpus reviewed one row deep,
    exit 0, no refusal. Position is unique by construction, and a segment picked by two criteria at once
    (band and top, say) is the only duplication the loop in `select` exists to remove.

    A function rather than an expression, and it still takes the segment it ignores, so that the test can
    put the shipped key back and watch the truncation guard below fire on it.
    """
    return i


def select(segments: list[dict], top: int, bottom: int,
           band: tuple[float, float] | None) -> list[dict]:
    """Pick which segments to review, tagging each with why it was picked. Never silently truncates.

    That last sentence is enforced below rather than asserted here: the rows kept are counted against the
    segments the criteria matched, and a shortfall raises. A 400-segment corpus that renders one row is
    "reviewed 0 segments, no problems" one row up, and it is the shape a review sheet fails in.
    """
    scored = [(i, s) for i, s in enumerate(segments) if isinstance(s.get("score"), (int, float))]
    picks: list[tuple[str, list[tuple[int, dict]]]] = []
    if band and scored:
        lo, hi = band
        picks.append((f"band {lo:g}-{hi:g}",
                      sorted(((i, s) for i, s in scored if lo <= s["score"] <= hi),
                             key=lambda t: t[1]["score"])))
    if top and scored:
        picks.append(("top", sorted(scored, key=lambda t: -t[1]["score"])[:top]))
    if bottom and scored:
        picks.append(("bottom", sorted(scored, key=lambda t: t[1]["score"])[:bottom]))
    if not scored:
        # No composite score exists yet (T-0029). Reviewing the TERMS is still worth doing - "does this look
        # like a road with 82% canopy" is answerable from a photograph - so fall back rather than emit
        # nothing and call it a clean review.
        picks.append(("unscored", list(enumerate(segments))))

    out: list[dict] = []
    seen: set = set()
    for why, items in picks:
        for i, s in items:
            k = _position_key(i, s)
            if k in seen:
                continue
            seen.add(k)
            out.append({**s, "why": why})
    # The floor is the population the criteria MATCHED, recomputed from the input - not "at least one row".
    matched = {i for _, items in picks for i, _ in items}
    if len(out) != len(matched):
        raise ValueError(
            f"selection matched {len(matched)} segment(s) but kept {len(out)} - refusing to hand over a "
            f"truncated sheet, because the dropped ones would read as reviewed and never be looked at")
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
    ".warn{border-left:3px solid #c25b28;padding-left:10px;color:#8a4520}"
    "td.v{white-space:nowrap}label{margin-right:8px;font-size:12.5px}"
    "@media(prefers-color-scheme:dark){body{background:#15140f;color:#f2ede3}"
    "table{background:#1e1c17;border-color:#38342a}th{background:#252219;color:#9a9184}"
    "td{border-color:#2f2b22}a{color:#8fb0cc}.t,.sub{color:#cfc7b8}"
    ".warn{color:#e8a878;border-left-color:#c25b28}}"
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
        f'<p class="sub warn">{NOT_RECORDED_NOTICE}</p>',
        "<table><tr><th>id</th><th>name</th><th>score</th><th>picked</th><th>terms</th>"
        "<th>view</th><th>verdict</th></tr>",
    ]
    for n, s in enumerate(rows):
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
        # The radio GROUP is named after the row, not after `id`. A browser groups radios by name, so six
        # pieces of one way - or six segments with no id, all rendering "?" - would otherwise share one
        # group, and answering row 6 would silently un-answer row 1. Same collapse as the dedup key above,
        # one layer down.
        out.append(
            f'<tr><td class="t">{rid}</td><td>{_esc(s.get("name") or "")}</td>'
            f'<td class="v">{sc}</td><td class="t">{_esc(s["why"])}</td>'
            f'<td class="t">{_esc(terms)}</td><td>{link}</td><td class="v">'
            f'<label><input type="radio" name="v_{n}" value="right"> right</label>'
            f'<label><input type="radio" name="v_{n}" value="wrong"> wrong</label>'
            f'<label><input type="radio" name="v_{n}" value="unsure"> ?</label></td></tr>')
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
