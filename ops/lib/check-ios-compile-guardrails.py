"""The guardrails on .github/workflows/ios-compile.yml, read as DATA (T-0157).

That workflow runs on a macOS runner. It is safe to have in the tree only while it is dispatch-only, read-only,
time-boxed and on the standard runner label: a `push:` trigger added in passing would put a macOS build on
every commit of every branch, next to the Linux CI the whole fleet depends on. Each guardrail is an
identifier in the parsed YAML, never a comment, and each refusal names the one that is gone.

GitHub Actions lets a JOB, a STEP and the RUN BODY itself override what the workflow level says: a job-level
`permissions:` REPLACES the workflow-level block, a step-level `shell:` replaces `defaults.run.shell`,
`continue-on-error: true` turns a failed build green, and `set +o pipefail` inside the script undoes the
shell's initial state. Round 1 of the review passed the first three through a check that read only the top
level; round 2 passed the fourth through a check that read every YAML level and not the script. Hunting bad
substrings in a script is an arms race, so the run bodies are not scanned: each is compared BY EQUALITY to
the literal below. Changing what this job runs means changing this file, deliberately, under review.

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
ALLOWED_USES = {"actions/checkout@v4", "actions/upload-artifact@v4"}
MAX_TIMEOUT_MINUTES = 30

# The ONLY scripts this job may run, keyed by step name. Equality, not a scan.
EXPECTED_RUN = {
    "toolchain": "\n".join([
        "xcodebuild -version",
        "swift --version",
        "ls /Applications | grep -i '^Xcode' || true",
    ]) + "\n",
    "build for the iOS Simulator": "\n".join([
        'mkdir -p "$GITHUB_WORKSPACE/DerivedData"',
        "xcodebuild \\",
        "  -project apps/ios/ScenicDrive.xcodeproj \\",
        "  -scheme ScenicDrive \\",
        "  -destination 'generic/platform=iOS Simulator' \\",
        '  -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \\',
        "  CODE_SIGNING_ALLOWED=NO \\",
        '  build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"',
    ]) + "\n",
    "what the build wrote into the tree": "\n".join([
        "git status --porcelain --untracked-files=all",
        "find apps/ios -name Package.resolved -print",
    ]) + "\n",
}
BUILD_STEP = "build for the iOS Simulator"


def triggers(on):
    """`on:` may be a string, a list or a mapping; all three are the same set of event names."""
    if isinstance(on, str):
        return {on}
    if isinstance(on, (list, tuple)):
        return {str(x) for x in on}
    if isinstance(on, dict):
        return {str(k) for k in on}
    return {repr(on)}


def runner(value):
    """`runs-on:` may be a string or a one-element list; anything else (a matrix, a group) is not the pinned label."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0]
    return None


def problems(doc, raw):
    out = []
    # PyYAML reads the bare key `on` as the boolean True (YAML 1.1); accept either spelling of the same key.
    found = triggers(doc.get("on", doc.get(True)))
    if found != {"workflow_dispatch"}:
        out.append(f"on: must be exactly workflow_dispatch, found {sorted(found)}")
    if doc.get("permissions") != {"contents": "read"}:
        out.append(f"permissions: must be exactly contents: read, found {doc.get('permissions')!r}")
    if (doc.get("defaults") or {}).get("run", {}).get("shell") != "bash":
        out.append("defaults.run.shell: must be bash (pipefail), or a failed build piped into tee reports success")
    if "env" in doc:
        out.append("env: a workflow-level environment is a way to hand a token to a script - remove it")
    if "secrets." in raw:
        out.append("secrets.: this job references no secret; a personal token would be outside the read-only GITHUB_TOKEN")
    jobs = doc.get("jobs") or {}
    if not jobs:
        out.append("jobs: none defined - nothing to guard is not the same as guarded")
    for name, job in jobs.items():
        for key, why in (("permissions", "a job-level block REPLACES the workflow-level one"),
                         ("defaults", "a job-level default can replace the bash shell"),
                         ("strategy", "a matrix multiplies the runner and can change its label"),
                         ("env", "a job-level environment is a way to hand a token to a script")):
            if key in job:
                out.append(f"jobs.{name}.{key}: {why} - remove it (found {job[key]!r})")
        if job.get("continue-on-error"):
            out.append(f"jobs.{name}.continue-on-error: a failed build must fail the job")
        if runner(job.get("runs-on")) not in ALLOWED_RUNNERS:
            out.append(f"jobs.{name}.runs-on: must be one of {sorted(ALLOWED_RUNNERS)}, found {job.get('runs-on')!r}")
        t = job.get("timeout-minutes")
        if isinstance(t, bool) or not isinstance(t, int) or not 0 < t <= MAX_TIMEOUT_MINUTES:
            out.append(f"jobs.{name}.timeout-minutes: must be an integer in 1..{MAX_TIMEOUT_MINUTES}, found {t!r}")
        steps = job.get("steps") or []
        if [s.get("name") for s in steps if "run" in s].count(BUILD_STEP) != 1:
            out.append(f"jobs.{name}: must have exactly one step named '{BUILD_STEP}'")
        for i, s in enumerate(steps):
            where = f"jobs.{name}.steps[{i}]"
            if "shell" in s and s["shell"] != "bash":
                out.append(f"{where}.shell: {s['shell']!r} replaces the pipefail default - a failed build piped into tee would pass")
            if s.get("continue-on-error"):
                out.append(f"{where}.continue-on-error: a failed step must fail the job")
            if "env" in s:
                out.append(f"{where}.env: a step-level environment is a way to hand a token to a script - remove it")
            if "uses" in s and s["uses"] not in ALLOWED_USES:
                out.append(f"{where}.uses: {s['uses']!r} is not in the allowlist {sorted(ALLOWED_USES)}")
            if "run" in s:
                want = EXPECTED_RUN.get(s.get("name"))
                if want is None:
                    out.append(f"{where}: a run step named {s.get('name')!r} is not one of the pinned scripts {sorted(EXPECTED_RUN)}")
                elif s["run"] != want:
                    out.append(f"{where}.run: the script of '{s.get('name')}' differs from the text pinned in this check (compared by equality)")
    return out


def check(path):
    """(exit code, lines). 0 ok, 1 a guardrail is gone, 2 cannot tell."""
    try:
        raw = path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw)
    except Exception as e:
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: cannot read {path.name}: {type(e).__name__}"]
    if not isinstance(doc, dict):
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: {path.name} is not a YAML mapping"]
    try:
        found = problems(doc, raw)
    except Exception as e:  # a shape this check did not expect is "cannot tell", never a verdict
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: {path.name} has a shape this check cannot judge: {type(e).__name__}"]
    lines = [f"IOS-COMPILE-GUARDRAILS: {p}" for p in found]
    if found:
        return 1, lines + [f"IOS-COMPILE-GUARDRAILS FAIL: {len(found)} guardrail(s) gone in {path.name}"]
    return 0, [f"IOS-COMPILE-GUARDRAILS OK: {path.name} is dispatch-only, read-only, time-boxed, on {sorted(ALLOWED_RUNNERS)}, and runs only its {len(EXPECTED_RUN)} pinned scripts"]


# One mutation per guardrail AND per level it can be overridden at: (what it breaks, exact text in the shipped
# workflow, replacement). --prove-red applies each ALONE to a copy outside the tree. A mutation that does not
# apply exactly once is a hard failure - a proof over a no-op would pass for the wrong reason.
JOB = "  simulator-build:\n    runs-on: macos-15\n"
BUILD = "      - name: build for the iOS Simulator\n        run: |\n"
MKDIR = '          mkdir -p "$GITHUB_WORKSPACE/DerivedData"\n'
TEE = 'build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"\n'
MUTATIONS = [
    ("a push trigger added", "on:\n  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n  push:\n    branches: [main]\n"),
    ("on: as a list that includes push", "on:\n  workflow_dispatch:\n", "on: [workflow_dispatch, push]\n"),
    ("workflow_call beside workflow_dispatch", "on:\n  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n  workflow_call:\n"),
    ("workflow-level permissions widened", "permissions:\n  contents: read\n", "permissions:\n  contents: write\n"),
    ("JOB-level permissions: write-all", JOB, "  simulator-build:\n    permissions: write-all\n    runs-on: macos-15\n"),
    ("the shell default dropped", "defaults:\n  run:\n    shell: bash\n", "defaults:\n  run:\n    shell: sh\n"),
    ("STEP-level shell: sh on the build step", BUILD, "      - name: build for the iOS Simulator\n        shell: sh\n        run: |\n"),
    ("RUN-BODY: set +o pipefail above the build", MKDIR, "          set +o pipefail\n" + MKDIR),
    ("RUN-BODY: || true after the build pipeline", TEE, TEE.rstrip("\n") + " || true\n"),
    ("continue-on-error on the build step", BUILD, "      - name: build for the iOS Simulator\n        continue-on-error: true\n        run: |\n"),
    ("continue-on-error on the job", JOB, "  simulator-build:\n    continue-on-error: true\n    runs-on: macos-15\n"),
    ("a token handed to the build step", BUILD, "      - name: build for the iOS Simulator\n        env:\n          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n        run: |\n"),
    ("a matrix on the job", JOB, "  simulator-build:\n    strategy:\n      matrix:\n        os: [macos-15, macos-15-xlarge]\n    runs-on: macos-15\n"),
    ("a larger runner", "    runs-on: macos-15\n", "    runs-on: macos-15-xlarge\n"),
    ("the timeout removed", "    timeout-minutes: 20\n", ""),
    ("the timeout as a boolean", "    timeout-minutes: 20\n", "    timeout-minutes: true\n"),
    ("derivedDataPath dropped", '            -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \\\n', ""),
    ("a push step", "          find apps/ios -name Package.resolved -print\n",
     "          find apps/ios -name Package.resolved -print\n          git push origin HEAD\n"),
    ("an unpinned run step", "      - name: toolchain\n", "      - name: anything else\n        run: echo hi\n      - name: toolchain\n"),
    ("a third-party action", "      - uses: actions/checkout@v4\n", "      - uses: actions/checkout@v4\n      - uses: someone/else@v1\n"),
]
# Legitimate spellings that must stay GREEN - a check that refuses them teaches people to stop running it.
STILL_GREEN = [
    ("on: as a bare string", "on:\n  workflow_dispatch:\n", "on: workflow_dispatch\n"),
    ("runs-on as a one-element list", "    runs-on: macos-15\n", "    runs-on: [macos-15]\n"),
]


def prove_red():
    src = WORKFLOW.read_text(encoding="utf-8")
    unexpected = 0
    with tempfile.TemporaryDirectory() as d:
        for want, label, table in ((1, "red", MUTATIONS), (0, "green", STILL_GREEN)):
            for name, old, new in table:
                if src.count(old) != 1:
                    print(f"PROVE-RED REFUSING: the mutation '{name}' does not apply exactly once - its anchor is stale")
                    return 2
                p = pathlib.Path(d) / "ios-compile.yml"
                p.write_text(src.replace(old, new, 1), encoding="utf-8", newline="\n")
                rc, lines = check(p)
                unexpected += rc != want
                print(f"[{label if rc == want else 'NOT ' + label.upper()} rc={rc}] {name}: {lines[0] if lines else ''}")
        p = pathlib.Path(d) / "not-yaml.yml"
        p.write_text("on: [unclosed\n", encoding="utf-8")
        rc, lines = check(p)
        unexpected += rc != 2
        print(f"[{'refused' if rc == 2 else 'NOT REFUSED'} rc={rc}] unreadable YAML: {lines[0]}")
    rc, lines = check(WORKFLOW)
    unexpected += rc != 0
    print(f"[{'green' if rc == 0 else 'NOT GREEN'} rc={rc}] the shipped file: {lines[-1]}")
    print(f"PROVE-RED {'OK' if not unexpected else 'FAILED'}: {len(MUTATIONS)} mutations red, {len(STILL_GREEN)} legitimate spellings green, {unexpected} unexpected result(s)")
    return 0 if not unexpected else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--prove-red":
        return prove_red()
    rc, lines = check(pathlib.Path(argv[1]) if len(argv) > 1 else WORKFLOW)
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
