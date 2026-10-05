#!/usr/bin/env python3
"""Run the EXISTING tests that prove one pin, by NAME, and refuse unless every named test ran and passed.

  run-named-tests.py <PIN-ID>        e.g. run-named-tests.py P-COST-01

The names live in ops/lib/named-tests.json under the pin id:
  {"P-X": {"vitest": {"test/a.test.ts": ["describe > it", ...]},
           "swift": {"filter": "SuiteA|SuiteB", "tests": ["ScenicKitTests.SuiteA/fn()", ...]}}}

Vitest (services/api): `npx vitest run <files> --reporter=json --outputFile=<tmp>`; a test is named
`<file> :: <describe> > ... > <it>` from the report's ancestorTitles + title.
Swift (root package): `swift test --scratch-path $SCENIC_SWIFT_SCRATCH (default .build) --filter <filter>
--xunit-output <tmp>/x.xml`; a test is named `<classname>/<name>` from x-swift-testing.xml and x.xml - for Swift
Testing that is Module.Suite/function(), the identifier, never the display string.

The reporters' exit status is not trusted in either direction; only the parsed report decides. Every named test
must appear at least once and every occurrence must have passed. Red BY NAME: MISSING, SKIPPED, FAILED. Red
without a name: an unknown pin, a pin naming zero tests, a report that is missing or unparsable.
Prints `NAMED <pin> passed=N/M` and exits 0 only when N == M > 0.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "ops" / "lib" / "named-tests.json"
API = ROOT / "services" / "api"
PASSED = "passed"


class Refusal(Exception):
    """A failure that has no test name to hang on: the run proves nothing."""


def vitest_results(files):
    """{name: [status, ...]} for every test the vitest JSON report carries for these files."""
    npx = shutil.which("npx")
    if npx is None:
        raise Refusal("npx is not on PATH - the Worker tests cannot run here")
    if not (API / "node_modules").is_dir():
        raise Refusal("services/api/node_modules is missing - run `npm ci` in services/api")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "vitest.json"
        cmd = [npx, "vitest", "run", *files, "--reporter=json", f"--outputFile={out}"]
        p = subprocess.run(cmd, cwd=API, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if not out.is_file():
            raise Refusal(f"vitest wrote no JSON report (exit {p.returncode}): {(p.stdout + p.stderr)[-600:]}")
        try:
            report = json.loads(out.read_text(encoding="utf-8"))
        except ValueError as e:
            raise Refusal(f"vitest JSON report is unparsable: {e}")
    results = {}
    for suite in report.get("testResults") or []:
        path = Path(str(suite.get("name", ""))).as_posix()
        rel = next((f for f in files if path.endswith("/" + f) or path == f), None)
        if rel is None:
            continue
        for a in suite.get("assertionResults") or []:
            name = rel + " :: " + " > ".join([*(a.get("ancestorTitles") or []), str(a.get("title"))])
            results.setdefault(name, []).append(str(a.get("status")))
    return results


def junit_status(case):
    for child in case:
        if child.tag in ("failure", "error"):
            return "failed"
        if child.tag == "skipped":
            return "skipped"
    return PASSED


def swift_results(filt):
    """{Module.Suite/function(): [status, ...]} from swift test's xunit reports."""
    swift = shutil.which("swift")
    if swift is None:
        raise Refusal("swift is not on PATH - the engine tests cannot run here")
    scratch = os.environ.get("SCENIC_SWIFT_SCRATCH") or ".build"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "x.xml"
        cmd = [swift, "test", "--scratch-path", scratch, "--filter", filt, "--xunit-output", str(base)]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        reports = [r for r in (base, Path(tmp) / "x-swift-testing.xml") if r.is_file()]
        if not reports:
            raise Refusal(f"swift test wrote no xunit report (exit {p.returncode}): {(p.stdout + p.stderr)[-600:]}")
        results = {}
        for r in reports:
            try:
                root = ET.parse(r).getroot()
            except ET.ParseError as e:
                raise Refusal(f"{r.name} is unparsable: {e}")
            for case in root.iter("testcase"):
                name = f"{case.get('classname')}/{case.get('name')}"
                results.setdefault(name, []).append(junit_status(case))
    return results


def verdicts(required, results):
    """[(name, verdict)] - verdict is PASSED or the reason this name is red."""
    out = []
    for name in required:
        statuses = results.get(name)
        if not statuses:
            out.append((name, "MISSING - no test of this name ran"))
        elif any(s in ("skipped", "pending", "todo", "disabled") for s in statuses):
            out.append((name, f"SKIPPED - {statuses}"))
        elif any(s != PASSED for s in statuses):
            out.append((name, f"FAILED - {statuses}"))
        else:
            out.append((name, PASSED))
    return out


def run_pin(pin):
    try:
        table = json.loads(TABLE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refusal(f"{TABLE.relative_to(ROOT).as_posix()} unreadable: {e}")
    spec = table.get(pin)
    if not isinstance(spec, dict) or not spec:
        raise Refusal(f"{pin} has no entry in {TABLE.name}")
    unknown = set(spec) - {"vitest", "swift"}
    if unknown:
        raise Refusal(f"{pin}: unknown runner(s) {sorted(unknown)}")
    rows = []
    vit = spec.get("vitest") or {}
    if vit:
        required = [f"{f} :: {n}" for f, names in vit.items() for n in names]
        if not required:
            raise Refusal(f"{pin}: vitest names no test")
        rows += verdicts(required, vitest_results(list(vit)))
    sw = spec.get("swift") or {}
    if sw:
        if not sw.get("filter") or not sw.get("tests"):
            raise Refusal(f"{pin}: swift needs a filter and at least one test")
        rows += verdicts(list(sw["tests"]), swift_results(sw["filter"]))
    if not rows:
        raise Refusal(f"{pin} names zero tests - a vacuous green is refused")
    return rows


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[2])
        return 2
    pin = argv[0]
    try:
        rows = run_pin(pin)
    except Refusal as e:
        print(f"NAMED {pin} REFUSED: {e}")
        return 1
    good = sum(1 for _, v in rows if v == PASSED)
    for name, v in rows:
        if v != PASSED:
            print(f"  RED {name}: {v}")
    print(f"NAMED {pin} passed={good}/{len(rows)}")
    return 0 if good == len(rows) and rows else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
