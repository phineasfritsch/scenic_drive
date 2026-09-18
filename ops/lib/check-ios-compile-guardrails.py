"""The guardrails on .github/workflows/ios-compile.yml, read as DATA (T-0157).

That workflow runs on a macOS runner. It is safe to have in the tree only while it is dispatch-only, read-only,
time-boxed and on the standard runner label: a `push:` trigger added in passing would put a macOS build on
every commit of every branch, next to the Linux CI the whole fleet depends on. Each guardrail is an
identifier in the parsed YAML, never a comment, and each refusal names the one that is gone.

    python ops/lib/check-ios-compile-guardrails.py [path]        exit 0 ok, 1 a guardrail is gone, 2 cannot tell
    python ops/lib/check-ios-compile-guardrails.py --prove-red   every guardrail seen red on a mutated copy
"""
import pathlib
import sys
import tempfile

try:
    import yaml
except ImportError:  # "I could not ask" is not "the answer is yes"
    print("IOS-COMPILE-GUARDRAILS REFUSING: PyYAML is not importable, so the workflow cannot be read as data")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/ios-compile.yml"
ALLOWED_RUNNERS = {"macos-15"}
MAX_TIMEOUT_MINUTES = 30
FORBIDDEN_IN_RUN = ("git push", "git commit", "gh pr merge", "gh release")

# One mutation per guardrail: (what it breaks, exact text in the shipped workflow, replacement). --prove-red
# applies each ALONE to a copy outside the tree. A mutation that does not apply exactly once is a hard
# failure - a proof over a no-op would pass for the wrong reason.
MUTATIONS = [
    ("a push trigger added", "on:\n  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n  push:\n    branches: [main]\n"),
    ("permissions widened", "permissions:\n  contents: read\n", "permissions:\n  contents: write\n"),
    ("the shell default dropped", "defaults:\n  run:\n    shell: bash\n", "defaults:\n  run:\n    shell: sh\n"),
    ("a larger runner", "    runs-on: macos-15\n", "    runs-on: macos-15-xlarge\n"),
    ("the timeout removed", "    timeout-minutes: 20\n", ""),
    ("derivedDataPath dropped", '            -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \\\n', ""),
    ("a push step", "          find apps/ios -name Package.resolved -print\n",
     "          find apps/ios -name Package.resolved -print\n          git push origin HEAD\n"),
]


def problems(doc):
    out = []
    # PyYAML reads the bare key `on` as the boolean True (YAML 1.1); accept either spelling of the same key.
    on = doc.get("on", doc.get(True))
    if not isinstance(on, dict) or set(on) != {"workflow_dispatch"}:
        out.append(f"on: must be exactly workflow_dispatch, found {sorted(map(str, on)) if isinstance(on, dict) else on!r}")
    if doc.get("permissions") != {"contents": "read"}:
        out.append(f"permissions: must be exactly contents: read, found {doc.get('permissions')!r}")
    if (doc.get("defaults") or {}).get("run", {}).get("shell") != "bash":
        out.append("defaults.run.shell: must be bash (pipefail), or a failed build piped into tee reports success")
    jobs = doc.get("jobs") or {}
    if not jobs:
        out.append("jobs: none defined - nothing to guard is not the same as guarded")
    for name, job in jobs.items():
        if job.get("runs-on") not in ALLOWED_RUNNERS:
            out.append(f"jobs.{name}.runs-on: must be one of {sorted(ALLOWED_RUNNERS)}, found {job.get('runs-on')!r}")
        t = job.get("timeout-minutes")
        if not isinstance(t, int) or not 0 < t <= MAX_TIMEOUT_MINUTES:
            out.append(f"jobs.{name}.timeout-minutes: must be an integer in 1..{MAX_TIMEOUT_MINUTES}, found {t!r}")
        steps = job.get("steps") or []
        if not any("xcodebuild" in str(s.get("run", "")) and "-derivedDataPath" in str(s.get("run", "")) for s in steps):
            out.append(f"jobs.{name}: no step runs xcodebuild with -derivedDataPath")
        for i, s in enumerate(steps):
            for bad in FORBIDDEN_IN_RUN:
                if bad in str(s.get("run", "")):
                    out.append(f"jobs.{name}.steps[{i}]: runs '{bad}' - this job never writes anywhere")
    return out


def check(path, quiet=False):
    """(exit code, lines). 0 ok, 1 a guardrail is gone, 2 cannot tell."""
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: cannot read {path.name}: {type(e).__name__}"]
    if not isinstance(doc, dict):
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: {path.name} is not a YAML mapping"]
    found = problems(doc)
    lines = [f"IOS-COMPILE-GUARDRAILS: {p}" for p in found]
    if found:
        return 1, lines + [f"IOS-COMPILE-GUARDRAILS FAIL: {len(found)} guardrail(s) gone in {path.name}"]
    return 0, [f"IOS-COMPILE-GUARDRAILS OK: {path.name} is dispatch-only, read-only, time-boxed, on {sorted(ALLOWED_RUNNERS)}"]


def prove_red():
    src = WORKFLOW.read_text(encoding="utf-8")
    unexpected = 0
    with tempfile.TemporaryDirectory() as d:
        for name, old, new in MUTATIONS:
            if src.count(old) != 1:
                print(f"PROVE-RED REFUSING: the mutation '{name}' does not apply exactly once - its anchor is stale")
                return 2
            p = pathlib.Path(d) / "ios-compile.yml"
            p.write_text(src.replace(old, new, 1), encoding="utf-8", newline="\n")
            rc, lines = check(p)
            unexpected += rc != 1
            print(f"[{'red' if rc == 1 else 'NOT RED'} rc={rc}] {name}: {lines[0] if lines else ''}")
        p = pathlib.Path(d) / "not-yaml.yml"
        p.write_text("on: [unclosed\n", encoding="utf-8")
        rc, lines = check(p)
        unexpected += rc != 2
        print(f"[{'refused' if rc == 2 else 'NOT REFUSED'} rc={rc}] unreadable YAML: {lines[0]}")
    rc, lines = check(WORKFLOW)
    unexpected += rc != 0
    print(f"[{'green' if rc == 0 else 'NOT GREEN'} rc={rc}] the shipped file: {lines[-1]}")
    print(f"PROVE-RED {'OK' if not unexpected else 'FAILED'}: {len(MUTATIONS)} guardrails mutated, {unexpected} unexpected result(s)")
    return 0 if not unexpected else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--prove-red":
        return prove_red()
    rc, lines = check(pathlib.Path(argv[1]) if len(argv) > 1 else WORKFLOW)
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
