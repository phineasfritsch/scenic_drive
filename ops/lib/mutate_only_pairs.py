"""T-0353 (rv1 B1): the in-process half of ops/lib/check-mutate-only.py - every id pair, both shared parsers.

The subprocess probes run each driver with ONE name range, so a range expansion keyed to a property that pair
lacks (mutant S: both halves share a stem before a numeric suffix, `window-89-window-91`) stays green. Here every
ordered pair (a, b) of every driver's listed ids, a == b included, whose `a-b` no id equals or contains, is handed
to both parsers the drivers share - mutate_only.select_only in all four (substring, split) modes and onlyIds.mjs
through one `node` harness - against that driver's ids, and every call must refuse: exit 64 with a
`REFUSING TO RUN: ` line. Every population goes to both parsers, so the class closes whichever driver uses which
parser and whatever order its ids are listed in. PAIR_FLOOR (the pair tokens measured 2026-10-10) keeps a drained
population from passing as `0 of 0`.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ops/mutate"))

import mutate_only  # noqa: E402

PAIR_FLOOR = 192168
MODES = ((False, True), (True, True), (False, False), (True, False))
REFUSED = "REFUSING TO RUN: "
SHOW = 3

NODE_HARNESS = """
import { readFileSync } from "node:fs";
import { onlyIds } from %s;
const jobs = JSON.parse(readFileSync(0, "utf8"));
const write = process.stdout.write.bind(process.stdout), exit = process.exit;
class Refused { constructor(code) { this.code = code; } }
const bad = [];
let n = 0;
for (const [name, ids, tokens] of jobs) {
  for (const t of tokens) {
    let said = "", why = null;
    process.stdout.write = (s) => { said += s; return true; };
    process.exit = (c) => { throw new Refused(c); };
    try {
      why = "selected " + JSON.stringify(onlyIds(["--only", t], ids));
    } catch (e) {
      if (!(e instanceof Refused)) why = "threw " + String(e);
      else if (e.code !== 64 || !said.split("\\n").some((l) => l.startsWith(%s))) why = "exit " + e.code;
    } finally {
      process.stdout.write = write;
      process.exit = exit;
    }
    n += 1;
    if (why !== null) bad.push([name, t, why]);
  }
}
write(JSON.stringify({ n, bad }) + "\\n");
"""


def pair_tokens(ids: list) -> list:
    """Every ordered `a-b` over the ids, a == b included, that no id equals or contains."""
    ids = list(dict.fromkeys(ids))
    joined = "\0".join(ids)
    return [t for t in ("%s-%s" % (a, b) for a in ids for b in ids) if t not in joined]


def py_verdict(token: str, ids: list, substring: bool, split: bool) -> str | None:
    """None when select_only refuses `--only token` with exit 64 and a REFUSING line; else what it did."""
    said = io.StringIO()
    try:
        with contextlib.redirect_stdout(said):
            got = mutate_only.select_only(["--only", token], ids, substring=substring, split=split)
    except SystemExit as e:
        ok = e.code == mutate_only.EXIT_ONLY_REFUSED and any(l.startswith(REFUSED) for l in said.getvalue().split("\n"))
        return None if ok else "exit %s" % e.code
    except Exception as e:  # noqa: BLE001 - a parser that throws did not refuse
        return "threw %r" % e
    return "selected %s" % json.dumps(sorted(got))


def node_misses(jobs: list) -> list:
    """[(driver, token, what onlyIds did)] for every token onlyIds did not refuse. SystemExit when the harness
    cannot run or did not see every token."""
    uri = json.dumps((ROOT / "services/api/test/mutate/onlyIds.mjs").as_uri())
    js = NODE_HARNESS % (uri, json.dumps(REFUSED))
    p = subprocess.run(["node", "--input-type=module", "-e", js], input=json.dumps(jobs), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    want = sum(len(t) for _, _, t in jobs)
    try:
        res = json.loads(p.stdout.strip().split("\n")[-1])
    except (ValueError, IndexError):
        res = None
    if p.returncode != 0 or not isinstance(res, dict) or res.get("n") != want:
        raise SystemExit("onlyIds pair harness: exit %d, %r (want n=%d): REFUSING"
                         % (p.returncode, (p.stdout + p.stderr).strip()[-300:], want))
    return [tuple(b) for b in res["bad"]]


def report(parser: str, misses: list) -> list:
    """At most SHOW lines per (parser, driver), then a count of the rest."""
    lines, per = [], {}
    for name, token, why in misses:
        per.setdefault(name, []).append((token, why))
    for name, hits in per.items():
        for token, why in hits[:SHOW]:
            lines.append(("%s %s --only %s: %s" % (parser, name, token, why))[:240])
        if len(hits) > SHOW:
            lines.append("%s %s: and %d more pair tokens not refused" % (parser, name, len(hits) - SHOW))
    return lines


def probe(populations: list) -> tuple:
    """(failure lines, pair tokens per parser) over [(driver, ids)]; each token goes to 5 parser calls."""
    jobs = [(name, list(ids), pair_tokens(ids)) for name, ids in populations if ids]
    bad = []
    for substring, split in MODES:
        misses = [(name, t, why) for name, ids, tokens in jobs for t in tokens
                  for why in [py_verdict(t, ids, substring, split)] if why is not None]
        bad += report("select_only(substring=%s, split=%s)" % (substring, split), misses)
    bad += report("onlyIds", node_misses(jobs))
    return bad, sum(len(t) for _, _, t in jobs), len(jobs)
