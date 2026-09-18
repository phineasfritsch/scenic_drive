"""The guardrails on .github/workflows/ios-compile.yml, read as DATA (T-0157).

That workflow runs on a macOS runner. It is safe to have in the tree only while it is dispatch-only, read-only,
time-boxed, on the standard runner label, and unable to go green without compiling: a `push:` trigger added in
passing would put a macOS build on every commit of every branch, beside the Linux CI the fleet depends on.

Three review rounds each found a door the previous version did not watch - a job-level `permissions:` (it
REPLACES the workflow-level block), a step-level `shell:` and `continue-on-error`, `set +o pipefail` inside the
script, `if: false` on the build step (a skipped build is a green job that compiled nothing). Enumerating
doors is an arms race. So this check does two things: it names the dangerous edits it knows (good messages),
and then it compares the WHOLE parsed workflow with the structure pinned below (EXPECTED), after normalising
the few spellings GitHub treats as identical, and names the first path that differs. Changing what this job
is - any key, anywhere - means changing this file, deliberately, under review.

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
BUILD_STEP = "build for the iOS Simulator"

TOOLCHAIN_RUN = "xcodebuild -version\nswift --version\nls /Applications | grep -i '^Xcode' || true\n"
BUILD_RUN = "\n".join([
    'mkdir -p "$GITHUB_WORKSPACE/DerivedData"',
    "xcodebuild \\",
    "  -project apps/ios/ScenicDrive.xcodeproj \\",
    "  -scheme ScenicDrive \\",
    "  -destination 'generic/platform=iOS Simulator' \\",
    '  -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \\',
    "  -disableAutomaticPackageResolution \\",
    "  CODE_SIGNING_ALLOWED=NO \\",
    '  build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"',
]) + "\n"
STATUS_RUN = "git status --porcelain --untracked-files=all\nfind apps/ios -name Package.resolved -print\n"

# The whole workflow, as parsed YAML. Equality, not a scan.
EXPECTED = {
    "name": "ios-compile",
    "on": {"workflow_dispatch": None},
    "concurrency": {"group": "ios-compile-${{ github.ref }}", "cancel-in-progress": True},
    "permissions": {"contents": "read"},
    "defaults": {"run": {"shell": "bash"}},
    "jobs": {"simulator-build": {
        "runs-on": "macos-15",
        "timeout-minutes": 20,
        "steps": [
            {"uses": "actions/checkout@v4"},
            {"name": "toolchain", "run": TOOLCHAIN_RUN},
            {"name": BUILD_STEP, "run": BUILD_RUN},
            {"name": "what the build wrote into the tree", "if": "always()", "run": STATUS_RUN},
            {"name": "keep the log and any Package.resolved", "if": "always()", "uses": "actions/upload-artifact@v4",
             "with": {"name": "ios-compile-${{ github.run_id }}", "if-no-files-found": "warn",
                      "path": "DerivedData/xcodebuild.log\napps/ios/**/Package.resolved\n"}},
        ],
    }},
}


def normalise(doc):
    """The spellings GitHub treats as identical, folded to one: `on` read by PyYAML as the boolean True; `on:` as
    a string or a list; `runs-on:` as a one-element list."""
    d = dict(doc)
    if True in d and "on" not in d:
        d["on"] = d.pop(True)
    on = d.get("on")
    if isinstance(on, str):
        d["on"] = {on: None}
    elif isinstance(on, (list, tuple)):
        d["on"] = {str(x): None for x in on}
    jobs = d.get("jobs")
    if isinstance(jobs, dict):
        d["jobs"] = {}
        for name, job in jobs.items():
            job = dict(job) if isinstance(job, dict) else job
            if isinstance(job, dict) and isinstance(job.get("runs-on"), list) and len(job["runs-on"]) == 1:
                job["runs-on"] = job["runs-on"][0]
            d["jobs"][name] = job
    return d


def first_difference(want, got, path="workflow"):
    """The first path at which two parsed YAML structures differ, or None."""
    if isinstance(want, dict) and isinstance(got, dict):
        for k in want:
            if k not in got:
                return f"{path}.{k}: missing"
        for k in got:
            if k not in want:
                return f"{path}.{k}: a key the pinned workflow does not have (found {got[k]!r})"
        for k in want:
            d = first_difference(want[k], got[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(want, list) and isinstance(got, list):
        if len(want) != len(got):
            return f"{path}: {len(got)} item(s) where the pinned workflow has {len(want)}"
        for i, (w, g) in enumerate(zip(want, got)):
            d = first_difference(w, g, f"{path}[{i}]")
            if d:
                return d
        return None
    if type(want) is not type(got) or want != got:
        return f"{path}: differs from the pinned value (compared by equality)"
    return None


def named_problems(doc, raw):
    """The dangerous edits this check knows by name. Not the net - the net is first_difference."""
    out = []
    if set(doc.get("on") or {}) != {"workflow_dispatch"}:
        out.append(f"on: must be exactly workflow_dispatch, found {sorted(map(str, doc.get('on') or {}))}")
    if doc.get("permissions") != {"contents": "read"}:
        out.append(f"permissions: must be exactly contents: read, found {doc.get('permissions')!r}")
    if (doc.get("defaults") or {}).get("run", {}).get("shell") != "bash":
        out.append("defaults.run.shell: must be bash (pipefail), or a failed build piped into tee reports success")
    if "secrets." in raw:
        out.append("secrets.: this job references no secret; a personal token would be outside the read-only GITHUB_TOKEN")
    for name, job in (doc.get("jobs") or {}).items():
        for key, why in (("permissions", "a job-level block REPLACES the workflow-level one"),
                         ("defaults", "a job-level default can replace the bash shell"),
                         ("strategy", "a matrix multiplies the runner and can change its label"),
                         ("env", "an environment is a way to hand a token to a script"),
                         ("if", "a job that is skipped is a green run that compiled nothing"),
                         ("continue-on-error", "a failed build must fail the job")):
            if key in job:
                out.append(f"jobs.{name}.{key}: {why} - remove it (found {job[key]!r})")
        if job.get("runs-on") not in ALLOWED_RUNNERS:
            out.append(f"jobs.{name}.runs-on: must be one of {sorted(ALLOWED_RUNNERS)}, found {job.get('runs-on')!r}")
        t = job.get("timeout-minutes")
        if isinstance(t, bool) or not isinstance(t, int) or not 0 < t <= MAX_TIMEOUT_MINUTES:
            out.append(f"jobs.{name}.timeout-minutes: must be an integer in 1..{MAX_TIMEOUT_MINUTES}, found {t!r}")
        for i, s in enumerate(job.get("steps") or []):
            where = f"jobs.{name}.steps[{i}]"
            if s.get("name") == BUILD_STEP and "if" in s:
                out.append(f"{where}.if: a build step that can be SKIPPED is a green job that compiled nothing (found {s['if']!r})")
            if "shell" in s and s["shell"] != "bash":
                out.append(f"{where}.shell: {s['shell']!r} replaces the pipefail default - a failed build piped into tee would pass")
            if s.get("continue-on-error"):
                out.append(f"{where}.continue-on-error: a failed step must fail the job")
            if "uses" in s and s["uses"] not in ALLOWED_USES:
                out.append(f"{where}.uses: {s['uses']!r} is not in the allowlist {sorted(ALLOWED_USES)}")
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
        doc = normalise(doc)
        found = named_problems(doc, raw)
        diff = first_difference(EXPECTED, doc)
    except Exception as e:  # a shape this check did not expect is "cannot tell", never a verdict
        return 2, [f"IOS-COMPILE-GUARDRAILS REFUSING: {path.name} has a shape this check cannot judge: {type(e).__name__}"]
    if diff and not found:
        found = [diff]
    lines = [f"IOS-COMPILE-GUARDRAILS: {p}" for p in found]
    if found:
        return 1, lines + [f"IOS-COMPILE-GUARDRAILS FAIL: {len(found)} guardrail(s) gone in {path.name}"]
    return 0, [f"IOS-COMPILE-GUARDRAILS OK: {path.name} equals the pinned workflow: dispatch-only, contents: read, {sorted(ALLOWED_RUNNERS)}, time-boxed, and a build that cannot be skipped or fail green"]


# (what it breaks, exact text in the shipped workflow, replacement). --prove-red applies each ALONE to a copy
# outside the tree. A mutation that does not apply exactly once is a hard failure - a proof over a no-op would
# pass for the wrong reason.
JOB = "  simulator-build:\n    runs-on: macos-15\n"
BUILD = "      - name: build for the iOS Simulator\n        run: |\n"
MKDIR = '          mkdir -p "$GITHUB_WORKSPACE/DerivedData"\n'
TEE = 'build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"\n'
TOOL = "      - name: toolchain\n        run: |\n          xcodebuild -version\n          swift --version\n          ls /Applications | grep -i '^Xcode' || true\n\n"


def after(anchor, line):
    return anchor.replace("\n        run: |\n", f"\n        {line}\n        run: |\n")


MUTATIONS = [
    ("a push trigger added", "on:\n  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n  push:\n    branches: [main]\n"),
    ("on: as a list that includes push", "on:\n  workflow_dispatch:\n", "on: [workflow_dispatch, push]\n"),
    ("workflow_call beside workflow_dispatch", "on:\n  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n  workflow_call:\n"),
    ("workflow-level permissions widened", "permissions:\n  contents: read\n", "permissions:\n  contents: write\n"),
    ("JOB-level permissions: write-all", JOB, "  simulator-build:\n    permissions: write-all\n    runs-on: macos-15\n"),
    ("the shell default dropped", "defaults:\n  run:\n    shell: bash\n", "defaults:\n  run:\n    shell: sh\n"),
    ("STEP-level shell: sh on the build step", BUILD, after(BUILD, "shell: sh")),
    ("RUN-BODY: set +o pipefail above the build", MKDIR, "          set +o pipefail\n" + MKDIR),
    ("RUN-BODY: || true after the build pipeline", TEE, TEE.rstrip("\n") + " || true\n"),
    ("continue-on-error on the build step", BUILD, after(BUILD, "continue-on-error: true")),
    ("continue-on-error on the job", JOB, "  simulator-build:\n    continue-on-error: true\n    runs-on: macos-15\n"),
    ("SKIPPED BUILD: if: false on the build step", BUILD, after(BUILD, "if: false")),
    ("SKIPPED BUILD: a condition never true on dispatch", BUILD, after(BUILD, "if: github.event_name == 'push'")),
    ("SKIPPED JOB: if: false on the job", JOB, "  simulator-build:\n    if: false\n    runs-on: macos-15\n"),
    ("working-directory on the build step", BUILD, after(BUILD, "working-directory: apps/ios")),
    ("a step-level timeout of zero", BUILD, after(BUILD, "timeout-minutes: 0")),
    ("the toolchain step deleted", TOOL, ""),
    ("a token handed to the build step", BUILD, "      - name: build for the iOS Simulator\n        env:\n          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n        run: |\n"),
    ("a matrix on the job", JOB, "  simulator-build:\n    strategy:\n      matrix:\n        os: [macos-15, macos-15-xlarge]\n    runs-on: macos-15\n"),
    ("a larger runner", "    runs-on: macos-15\n", "    runs-on: macos-15-xlarge\n"),
    ("the timeout removed", "    timeout-minutes: 20\n", ""),
    ("the timeout as a boolean", "    timeout-minutes: 20\n", "    timeout-minutes: true\n"),
    ("derivedDataPath dropped", '            -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \\\n', ""),
    ("-disableAutomaticPackageResolution dropped", "            -disableAutomaticPackageResolution \\\n", ""),
    ("a push step", "          find apps/ios -name Package.resolved -print\n",
     "          find apps/ios -name Package.resolved -print\n          git push origin HEAD\n"),
    ("an unpinned run step", "      - name: toolchain\n", "      - name: anything else\n        run: echo hi\n      - name: toolchain\n"),
    ("a third-party action", "      - uses: actions/checkout@v4\n", "      - uses: actions/checkout@v4\n      - uses: someone/else@v1\n"),
]
# Legitimate spellings that must stay GREEN - a check that refuses them teaches people to stop running it.
STILL_GREEN = [
    ("on: as a bare string", "on:\n  workflow_dispatch:\n", "on: workflow_dispatch\n"),
    ("runs-on as a one-element list", "    runs-on: macos-15\n", "    runs-on: [macos-15]\n"),
    ("a comment added", "name: ios-compile\n", "# a comment changes nothing that runs\nname: ios-compile\n"),
]


def prove_red():
    if not WORKFLOW.is_file():
        print(f"PROVE-RED REFUSING: {WORKFLOW} does not exist")
        return 2
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
