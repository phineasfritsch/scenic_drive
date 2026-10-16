"""T-0352 (P-PROC-06): every anchor of every Worker mutation driver occurs exactly once in today's source.

    python ops/lib/check-mutate-anchors.py

A driver under services/api/test/mutate/ refuses its whole run at the FIRST entry whose `find` text does not occur
exactly once in its file (`STALE <id>`). That refusal is correct, but nothing ran the drivers: on 2026-10-10 eight
of them (15 entries) had been refusing since 2026-10-06..09, so every mutant in those populations had silently stopped
being applied while P-PROC-06 still counted them. This check reads each driver's exported MUTATIONS and EQUIVALENT
(the same objects the driver mutates with, imported by node, never parsed from source text) and counts every `find`
in its `file` the way the driver does, naming EVERY stale entry rather than the first.

DRIVERS is a whitelist: the set of services/api/test/mutate/*Mutants.mjs must equal it exactly, so a new driver is a
refusal until it is listed here (and therefore checked), and a listed driver that disappears is a refusal too.
FLOOR is literal so a whitelist emptied by a bad merge is a refusal and not `0 drivers, 0 anchors`.
THE CWD ARM (T-0363). The anchor count above resolves `file` against services/api itself, so it cannot see a driver
whose OWN path resolution regressed to the cwd (`const API = process.cwd()`): such a driver works from services/api
and dies from anywhere else, and check-mutate-only's probes, though run from the repo root, are all refused by onlyIds
before any file is read. So every whitelisted driver is also run, as the shipping command line, from the REPO ROOT
with `--only=<its first MUTATIONS id>` and must print its `population mutations=` line - which every driver prints
only after its own STALE pass has read every anchored file through its own resolution and its `git status -- src`
has run - and the process tree is killed at that line, before the baseline: this check never runs vitest and never
mutates. A driver that does not reach the line in CWD_TIMEOUT_S is named with its last output; the tree's git status
(untracked included) must be identical before and after. Not seen by this arm: the vitest child's cwd and TESTS
paths, which only a run that reaches its baseline exercises.
Exit 0 every anchor occurs once and every driver reached its line; 1 a stale anchor or a driver that did not (each
named), or the tree changed; 2 this check could not run (whitelist, floor, node, git).
"""
from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
API = ROOT / "services/api"
MUTATE = API / "test/mutate"
DRIVERS = ("asn", "assert", "attest", "closures", "config", "crossing", "isochrone", "ledger", "loop", "plan", "quota",
           "region", "siwa", "telemetry", "tier", "trip", "vehicle")
FLOOR = 17
TABLES = ("MUTATIONS", "EQUIVALENT")
REACHED = "population mutations="
CWD_TIMEOUT_S = 90

LOADER = """
const out = {};
for (const [name, url] of JSON.parse(process.argv[1])) {
  const mod = await import(url);
  out[name] = {};
  for (const t of %s) {
    const rows = mod[t];
    out[name][t] = Array.isArray(rows) ? rows.map((x) => ({ id: x?.id, file: x?.file, find: x?.find })) : null;
  }
}
process.stdout.write(JSON.stringify(out));
""" % json.dumps(list(TABLES))


def refuse(msg: str) -> int:
    print("check-mutate-anchors: %s: REFUSING" % msg)
    return 2


def load(names: list) -> dict:
    pairs = [[n, (MUTATE / ("%sMutants.mjs" % n)).as_uri()] for n in names]
    p = subprocess.run(["node", "--input-type=module", "-e", LOADER, json.dumps(pairs)], cwd=API,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError("node could not import the drivers (exit %d): %s" % (p.returncode, p.stderr.strip()[-400:]))
    return json.loads(p.stdout)


def status() -> str:
    p = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, capture_output=True,
                       text=True)
    if p.returncode != 0:
        raise RuntimeError("git status failed (exit %d)" % p.returncode)
    return p.stdout


def kill_tree(p: subprocess.Popen) -> None:
    if p.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def reaches_population(name: str, first: str) -> str | None:
    """None when the driver, run from the repo root with --only=<first>, printed its population line; else why not."""
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    p = subprocess.Popen(["node", str(MUTATE / ("%sMutants.mjs" % name)), "--only=%s" % first], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                         errors="replace", **group)
    timer = threading.Timer(CWD_TIMEOUT_S, kill_tree, [p])
    timer.start()
    lines, reached = [], False
    try:
        for raw in p.stdout:
            line = raw.rstrip("\r\n")
            lines.append(line)
            if line.startswith(REACHED):
                reached = True
                break
    finally:
        timer.cancel()
        kill_tree(p)
        p.wait(timeout=60)
        p.stdout.close()
    if reached:
        return None
    said = [l for l in lines if l.strip()]
    told = [l for l in said if "Error" in l or l.startswith(("STALE", "REFUSING"))]
    return "exit %s, %s" % (p.returncode, ((told or said or ["(no output)"])[0]).strip()[:160])


def cwd_arm(tables: dict) -> list:
    bad = []
    for name in DRIVERS:
        first = tables[name]["MUTATIONS"][0]["id"]
        why = reaches_population(name, first)
        if why is not None:
            bad.append("CWD %s: run from the repo root with --only=%s never printed its population line - %s"
                       % (name, first, why))
    return bad


def main() -> int:
    if len(DRIVERS) < FLOOR or len(set(DRIVERS)) != len(DRIVERS):
        return refuse("DRIVERS holds %d distinct of %d names (floor %d)" % (len(set(DRIVERS)), len(DRIVERS), FLOOR))
    present = sorted(f.name[: -len("Mutants.mjs")] for f in MUTATE.glob("*Mutants.mjs"))
    unlisted = sorted(set(present) - set(DRIVERS))
    missing = sorted(set(DRIVERS) - set(present))
    if unlisted or missing:
        return refuse("driver(s) not in the DRIVERS whitelist: %s; listed but not on disk: %s"
                      % (", ".join(unlisted) or "none", ", ".join(missing) or "none"))
    try:
        tables = load(list(DRIVERS))
    except (RuntimeError, ValueError) as e:
        return refuse(str(e))

    stale, anchors, cache = [], 0, {}
    for name in DRIVERS:
        got = tables.get(name, {})
        if not got.get("MUTATIONS"):
            return refuse("%sMutants.mjs exports no MUTATIONS rows" % name)
        for table in TABLES:
            rows = got.get(table)
            if rows is None:
                return refuse("%sMutants.mjs exports no %s array" % (name, table))
            for x in rows:
                if not all(isinstance(x.get(k), str) and x.get(k) for k in ("id", "file", "find")):
                    stale.append("%s %s: entry %r has no string id/file/find" % (name, table, x.get("id")))
                    continue
                anchors += 1
                path = (API / x["file"]).resolve()
                if path not in cache:
                    cache[path] = path.read_bytes().decode("utf-8") if path.is_file() else None
                text = cache[path]
                count = -1 if text is None else text.count(x["find"])
                if count != 1:
                    where = "is not a file" if text is None else "occurs %d times" % count
                    stale.append("STALE %s %s: anchor %s in %s" % (name, x["id"], where, x["file"]))
    for line in stale:
        print(line)
    print("check-mutate-anchors: %d drivers, %d anchors, %d stale" % (len(DRIVERS), anchors, len(stale)))
    try:
        before = status()
        lost = cwd_arm(tables)
        after = status()
    except (RuntimeError, OSError) as e:
        return refuse(str(e))
    for line in lost:
        print(line)
    if after != before:
        moved = sorted(set(after.splitlines()) ^ set(before.splitlines()))
        print("TREE CHANGED during the cwd arm: %s" % "; ".join(moved))
    print("check-mutate-anchors: cwd arm: %d drivers run from the repo root, %d reached their population line"
          % (len(DRIVERS), len(DRIVERS) - len(lost)))
    return 1 if stale or lost or after != before else 0


if __name__ == "__main__":
    sys.exit(main())
