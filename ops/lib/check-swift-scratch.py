#!/usr/bin/env python3
"""P-OPS-10 (T-0229): every swift build/test a pin runs takes its OWN --scratch-path, never the shared .build.

  check-swift-scratch.py              PINS.yaml assertions + run-named-tests.py's swift call; exit 0 green, 1 red
  check-swift-scratch.py --list       every swift word the scan sees, per pin
  check-swift-scratch.py --prove-red  every synthetic row must come out as its expected verdict; exit 0 only then

Two halves, both whitelists:
  1. Assertions, read by ops/lib/pins.py's own `load` (what ops/check-pins runs). Every word `swift`, any case, is
     counted. Only four shapes are excused: glued into an identifier (`SwiftUI`, `MySwift`), a file extension
     (`Package.swift`), a directory component (`Sources/swift/`) and a hyphenated name component
     (`check-swift-scratch.py`). So `swift-build`, `apple-swift`, `SWIFT`, `swift.exe`, a quoted
     `swift` and a swift that ends a path (`/usr/bin/swift`, `"$T/usr/bin/swift"`, `~/.swiftly/bin/swift`) are words
     (SwiftPM's executables are `swift` and `swift-<subcommand>`). Each must sit at a command position (start, after `&&`, `||`,
     `;`, `|`, `(`, `{`, `!`, then/do/else) and read exactly `swift test|build --scratch-path .build/pins-<own id,
     lowercased>`, with no second --scratch-path/--build-path later in the same command. Anything else is refused.
  2. ops/lib/run-named-tests.py, the one script a pin names that builds Swift (11 pins). The shipping function
     `swift_results` is called with only its subprocess and `which` replaced; the argv it would run must carry
     `test --scratch-path <dir under .build that is not .build>`, and SCENIC_SWIFT_SCRATCH=.build must be refused
     before any swift runs.
"""
import importlib.util
import os
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "ops" / "lib"
RUNNER = LIB / "run-named-tests.py"
SHARED = (ROOT / ".build").resolve()
WORD = re.compile(r"(?:(?<![A-Za-z0-9_./-])|(?<=/)(?!swift/)|(?<=-)(?!swift-))swift(?![A-Za-z0-9_])", re.IGNORECASE)
COMMAND_POSITION = re.compile(r"(^|&&|\|\||[;|({!]|\bthen|\bdo|\belse)\s*$")
SEGMENT_END = re.compile(r"&&|\|\||[;|)\n]")
LATER_PATH_FLAG = re.compile(r"--(scratch|build)-path\b")


def load_module(name, path, source=None):
    if source is None:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(source, str(path), "exec"), mod.__dict__)
    return mod


def approved(pid):
    return re.compile(r"swift (test|build) --scratch-path \.build/pins-" + re.escape(pid.lower()) + r"(?=$|[\s;&|)])")


def assertion_refusals(pins):
    """[str] - one line per swift word in an assertion that is not at an approved site."""
    out = []
    for p in pins:
        pid, text = str(p.get("id")), str(p.get("assertion") or "")
        ok_site = approved(pid)
        for m in WORD.finditer(text):
            i = m.start()
            snippet = text[i:i + 70]
            if not COMMAND_POSITION.search(text[:i]):
                out.append(f"{pid}: `{snippet}` - swift not at a command position (echo, quote, prefix or wrapper)")
                continue
            ok = ok_site.match(text, i)
            if not ok:
                out.append(f"{pid}: `{snippet}` - not `swift test|build --scratch-path .build/pins-{pid.lower()}`")
                continue
            end = SEGMENT_END.search(text, ok.end())
            rest = text[ok.end():end.start() if end else len(text)]
            if LATER_PATH_FLAG.search(rest):
                out.append(f"{pid}: `{snippet}` - a second --scratch-path/--build-path in the same command overrides it")
    return out


class _Stub:
    def __init__(self):
        self.calls = []

    def run(self, cmd, **_kw):
        self.calls.append(list(cmd))
        return types.SimpleNamespace(returncode=1, stdout="", stderr="")

    @staticmethod
    def which(_name):
        return "swift"


def _call_runner(mod, env_value):
    stub = _Stub()
    mod.subprocess, mod.shutil = stub, stub
    saved = os.environ.pop("SCENIC_SWIFT_SCRATCH", None)
    if env_value is not None:
        os.environ["SCENIC_SWIFT_SCRATCH"] = env_value
    try:
        mod.swift_results("SuiteUnderT0229Probe")
        refused = False
    except mod.Refusal:
        refused = True
    finally:
        os.environ.pop("SCENIC_SWIFT_SCRATCH", None)
        if saved is not None:
            os.environ["SCENIC_SWIFT_SCRATCH"] = saved
    return refused, stub.calls


def runner_refusals(source=None):
    """[str] - what is wrong with the swift call run-named-tests.py's swift_results would make."""
    out = []
    try:
        mod = load_module("run_named_tests_t0229", RUNNER, source)
    except Exception as e:  # noqa: BLE001 - an unloadable runner is red, never green
        return [f"run-named-tests.py: does not load: {e!r}"]
    _, calls = _call_runner(mod, None)
    if len(calls) != 1:
        out.append(f"run-named-tests.py: swift_results made {len(calls)} swift calls with SCENIC_SWIFT_SCRATCH unset "
                   f"(expected exactly 1)")
    for cmd in calls:
        if cmd[1:3] != ["test", "--scratch-path"] or len(cmd) < 4:
            out.append(f"run-named-tests.py: `{' '.join(cmd[:6])}` - not `swift test --scratch-path <dir>`")
            continue
        scratch = (ROOT / cmd[3]).resolve()
        if scratch == SHARED or SHARED not in scratch.parents:
            out.append(f"run-named-tests.py: scratch path `{cmd[3]}` is the shared .build or outside it")
        if any(LATER_PATH_FLAG.fullmatch(a) for a in cmd[4:]):
            out.append(f"run-named-tests.py: a second --scratch-path/--build-path in `{' '.join(cmd)}`")
    for shared in (".build", "./.build/"):
        refused, calls = _call_runner(mod, shared)
        if not refused or calls:
            out.append(f"run-named-tests.py: SCENIC_SWIFT_SCRATCH={shared} was not refused before swift ran "
                       f"({len(calls)} call(s))")
    return out


OWN = "swift test --scratch-path .build/pins-p-x-01"
ASSERTION_ROWS = [
    # (name, assertion, expect_red)
    ("missing flag", "swift test --filter SolarFixtureTests", True),
    ("P-SAFE-05 as it stood before T-0229",
     "grep -q 'Naval Observatory' f && swift test --filter SolarFixtureTests 2>&1 | grep -E 'passed' >/dev/null", True),
    ("flag only in an echo", "echo --scratch-path .build/pins-p-x-01 && swift test --filter X", True),
    ("flag only in a comment", "swift test --filter X # --scratch-path .build/pins-p-x-01", True),
    ("flag on a different command", "grep --scratch-path .build/pins-p-x-01 f && swift test --filter X", True),
    ("second swift call missing it", OWN + " --filter A && swift build", True),
    ("second call missing it after a pipe", OWN + " | grep x; swift test --filter B", True),
    ("another pin's scratch", "swift test --scratch-path .build/pins-p-x-02 --filter X", True),
    ("shared .build spelled out", "swift test --scratch-path .build --filter X", True),
    ("flag value prefix of own id", "swift test --scratch-path .build/pins-p-x-0 --filter X", True),
    ("later flag overrides own", OWN + " --scratch-path .build --filter X", True),
    ("later --build-path overrides own", OWN + " --build-path .build", True),
    ("swift run", "swift run --scratch-path .build/pins-p-x-01 scenic", True),
    ("echo of a flagged command", "echo " + OWN, True),
    ("quoted bash -c", 'bash -c "' + OWN + '"', True),
    ("env-prefixed", "env A=1 " + OWN, True),
    ("swift-build executable", "swift-build --scratch-path .build/pins-p-x-01", True),
    ("swift-test after a pipe", "true | swift-test --scratch-path .build/pins-p-x-01", True),
    ("upper-case SWIFT", "SWIFT test --scratch-path .build/pins-p-x-01", True),
    ("flag before subcommand", "swift --scratch-path .build/pins-p-x-01 test", True),
    ("swift by absolute path", "/usr/bin/swift test --filter X", True),
    ("quoted toolchain path", '"$T/usr/bin/swift" build', True),
    ("swiftly path", "~/.swiftly/bin/swift test", True),
    ("relative path", "./swift test --filter X", True),
    ("swift.exe by path", "C:/t/bin/swift.exe test --filter X", True),
    ("swift-build by path", "/usr/bin/swift-build --filter X", True),
    ("own flag but by path", "/usr/bin/swift test --scratch-path .build/pins-p-x-01", True),
    ("xcrun wrapper", "xcrun swift test", True),
    ("env wrapper", "env swift test", True),
    ("swift ending a hyphenated token", "apple-swift test --filter X", True),
    ("control: one flagged call", OWN + " --filter X 2>&1 | grep -E 'passed' >/dev/null", False),
    ("control: two flagged calls", "swift build --scratch-path .build/pins-p-x-01 && " + OWN + " --filter X", False),
    ("control: in a subshell", "test $(" + OWN + " --filter X | wc -l) -ge 1", False),
    ("control: file names only", "grep -q 'iOS' Package.swift && test -f Tests/A/B.swift", False),
    ("control: swift as a directory", "test -f Sources/swift/x", False),
    ("control: .swift file", "grep Foo.swift", False),
    ("control: hyphenated name component", "python ops/lib/check-swift-scratch.py --list", False),
    ("control: SwiftUI in a grep alternation (P-SRC-01's shape)", "! grep -rE 'import (UIKit|SwiftUI|MapKit)' Sources/", False),
]

RUNNER_ROWS = [
    # (name, old, new) applied to run-named-tests.py's source; the result must be red
    ("runner: --scratch-path pair dropped", '"--scratch-path", scratch, ', ""),
    ("runner: default back to .build", 'SWIFT_SCRATCH = ".build/pins-named-tests"', 'SWIFT_SCRATCH = ".build"'),
    ("runner: env .build accepted", 'if (ROOT / scratch).resolve() == (ROOT / ".build").resolve():', "if False:"),
    ("runner: scratch outside .build", 'SWIFT_SCRATCH = ".build/pins-named-tests"', 'SWIFT_SCRATCH = "pins-named-tests"'),
]


def prove_red():
    bad = 0
    for name, assertion, expect_red in ASSERTION_ROWS:
        got = assertion_refusals([{"id": "P-X-01", "assertion": assertion}])
        verdict = "RED" if got else "GREEN"
        good = bool(got) == expect_red
        bad += not good
        print(f"  {'ok  ' if good else 'FAIL'} {verdict:5} {name}{': ' + got[0] if got else ''}")
    source = RUNNER.read_text(encoding="utf-8")
    for name, old, new in RUNNER_ROWS:
        if source.count(old) != 1:
            bad += 1
            print(f"  FAIL REFUSED {name}: anchor occurs {source.count(old)} times in run-named-tests.py")
            continue
        got = runner_refusals(source.replace(old, new))
        bad += not got
        print(f"  {'ok  ' if got else 'FAIL'} {'RED' if got else 'GREEN':5} {name}{': ' + got[0] if got else ''}")
    got = runner_refusals(source)
    bad += bool(got)
    print(f"  {'ok  ' if not got else 'FAIL'} {'RED' if got else 'GREEN':5} control: run-named-tests.py as shipped")
    rows = len(ASSERTION_ROWS) + len(RUNNER_ROWS) + 1
    print(f"SWIFT-SCRATCH prove-red rows={rows} wrong={bad}")
    return 1 if bad else 0


def main(argv):
    pins_mod = load_module("pins_t0229", LIB / "pins.py")
    pins = pins_mod.load(pins_mod.PINS)
    if len(pins) < 40:
        print(f"SWIFT-SCRATCH REFUSED: only {len(pins)} pins loaded from PINS.yaml - a truncated read is not green")
        return 1
    if "--prove-red" in argv:
        return prove_red()
    if "--list" in argv:
        for p in pins:
            text = str(p.get("assertion") or "")
            for m in WORD.finditer(text):
                print(f"{p.get('id')}: {text[m.start():m.start() + 80]}")
        return 0
    problems = assertion_refusals(pins) + runner_refusals()
    calls = sum(len(WORD.findall(str(p.get("assertion") or ""))) for p in pins)
    for line in problems:
        print(f"  RED {line}")
    print(f"SWIFT-SCRATCH pins={len(pins)} swift_words={calls} refused={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
