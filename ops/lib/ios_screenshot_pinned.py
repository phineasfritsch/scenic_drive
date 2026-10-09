"""The ios-screenshot workflow's pinned structure and its --prove-red table (T-0235). DATA, no rules.

check-ios-compile-guardrails.py reads .github/workflows/ios-screenshot.yml under the SAME rules and the SAME
action allowlist it applies to ios-compile.yml, and compares the whole parsed file with expected() by equality.
This module exists only because that check is at CLAUDE.md's 300-line cap. It imports nothing from it, and the one
environment variable both jobs may carry arrives as an argument, so it is still defined in one place.
"""
import pathlib

WORKFLOW = pathlib.Path(__file__).resolve().parents[2] / ".github/workflows/ios-screenshot.yml"
PICK_STEP = "choose, create and boot the simulator"
BUILD_STEP = "build for that simulator"
CAPTURE_STEP = "install, launch, and screenshot light then dark"
# A work step that can be skipped is a green run that did nothing: the check refuses `if:` on these BY NAME.
UNSKIPPABLE = {PICK_STEP, BUILD_STEP, CAPTURE_STEP}

TOOLCHAIN_RUN = "xcodebuild -version\nxcrun simctl list runtimes\nxcrun simctl list devicetypes\n"
PICK_RUN = r'''test -d "$DEVELOPER_DIR" || { echo "ios-screenshot: $DEVELOPER_DIR is not on this image"; exit 1; }
mkdir -p "$GITHUB_WORKSPACE/DerivedData/screens"
xcrun simctl list -j runtimes > "$RUNNER_TEMP/runtimes.json"
python3 - "$RUNNER_TEMP/runtimes.json" "$RUNNER_TEMP/choice" <<'PY'
import json, re, sys
rts = [r for r in json.load(open(sys.argv[1]))["runtimes"]
       if r["name"].startswith("iOS ") and r.get("isAvailable") and r["version"].split(".")[0] == "26"]
if not rts:
    sys.exit("ios-screenshot: no available iOS 26.x runtime on this image - the list is printed above")
rt = max(rts, key=lambda r: [int(x) for x in r["version"].split(".")])
def rank(d):
    m = re.match(r"iPhone (\d+)", d["name"])
    return (int(m.group(1)), -len(d["name"]), d["name"]) if m else None
phones = [d for d in rt.get("supportedDeviceTypes", []) if rank(d)]
if not phones:
    sys.exit("ios-screenshot: " + rt["name"] + " lists no numbered iPhone device type")
dt = max(phones, key=rank)
print("ios-screenshot: runtime " + rt["name"] + " " + rt["identifier"] + " - the newest available iOS 26.x")
print("ios-screenshot: device type " + dt["name"] + " " + dt["identifier"] + " - its newest numbered iPhone")
open(sys.argv[2], "w").write(rt["identifier"] + " " + dt["identifier"] + "\n")
PY
read -r RUNTIME DEVTYPE < "$RUNNER_TEMP/choice"
UDID=$(xcrun simctl create scenic-screenshot "$DEVTYPE" "$RUNTIME")
echo "ios-screenshot: created $UDID"
echo "$UDID" > "$GITHUB_WORKSPACE/DerivedData/sim-udid"
xcrun simctl boot "$UDID"
xcrun simctl bootstatus "$UDID"
'''
BUILD_RUN = r'''UDID=$(cat "$GITHUB_WORKSPACE/DerivedData/sim-udid")
xcodebuild \
  -project apps/ios/ScenicDrive.xcodeproj \
  -scheme ScenicDrive \
  -destination "platform=iOS Simulator,id=$UDID" \
  -derivedDataPath "$GITHUB_WORKSPACE/DerivedData" \
  -disableAutomaticPackageResolution \
  CODE_SIGNING_ALLOWED=NO \
  build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"
'''
CAPTURE_RUN = r'''UDID=$(cat "$GITHUB_WORKSPACE/DerivedData/sim-udid")
BUNDLE=com.phineasfritsch.scenicdrive
SETTLE=15
PLAN_SETTLE=6
SHOTS="$GITHUB_WORKSPACE/DerivedData/screens"
APP=$(find "$GITHUB_WORKSPACE/DerivedData/Build/Products" -maxdepth 2 -name '*.app' -path '*-iphonesimulator/*')
test "$(printf '%s\n' "$APP" | grep -c .)" = 1 || { echo "ios-screenshot: expected exactly one simulator .app, found: $APP"; exit 1; }
xcrun simctl install "$UDID" "$APP"
alive() {
  ps -ww -o command= -p "$1" | grep ScenicDrive || { echo "ios-screenshot: ScenicDrive (pid $1) is not running $2 - it crashed"; exit 1; }
}
for LOOK in light dark ax5; do
  SIZE=()
  LIST="collapsed medium fastest settings paywall surprise drive onboarding disclaimer preview nothingPretty offered loop trip saved legal"
  if [ "$LOOK" = ax5 ]; then
    SIZE=(-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL)
    LIST="preview nothingPretty offered loop trip saved"
    xcrun simctl ui "$UDID" appearance light
  else
    xcrun simctl ui "$UDID" appearance "$LOOK"
  fi
  for SHOT in $LIST; do
    DONE=(-safety.disclaimer.acknowledged.v1 YES -vehicle.profile.v1 standard)
    WAIT=$SETTLE
    case "$SHOT" in
      fastest) DETENT=collapsed ROW=0 SCREEN=home NAME=home-$LOOK-$SHOT ;;
      settings|paywall|surprise|legal) DETENT=collapsed ROW=default SCREEN=$SHOT NAME=$SHOT-$LOOK ;;
      onboarding) DETENT=collapsed ROW=default SCREEN=home NAME=onboarding-$LOOK DONE=() ;;
      disclaimer) DETENT=collapsed ROW=default SCREEN=disclaimer NAME=disclaimer-$LOOK DONE=() ;;
      preview|nothingPretty|offered|loop|trip|saved) DETENT=collapsed ROW=default SCREEN=$SHOT NAME=plan-$SHOT-$LOOK WAIT=$PLAN_SETTLE ;;
      drive) DETENT=collapsed ROW=default SCREEN=drive NAME=drive-$LOOK
        xcrun simctl privacy "$UDID" grant location "$BUNDLE"
        xcrun simctl location "$UDID" start --speed=15 34.0905,-118.6370 34.0880,-118.6250 34.0855,-118.6150 34.0830,-118.6050 ;;
      *) DETENT=$SHOT ROW=default SCREEN=home NAME=home-$LOOK-$SHOT ;;
    esac
    LAUNCHED=$(xcrun simctl launch "$UDID" "$BUNDLE" -homeDetent "$DETENT" -menuRow "$ROW" -screen "$SCREEN" "${DONE[@]}" "${SIZE[@]}")
    echo "$LAUNCHED"
    PID=${LAUNCHED##*: }
    case "$PID" in ''|*[!0-9]*) echo "ios-screenshot: simctl launch printed no pid: $LAUNCHED"; exit 1;; esac
    sleep "$WAIT"
    alive "$PID" "${WAIT}s after the $LOOK $SHOT launch"
    xcrun simctl io "$UDID" screenshot --type=png "$SHOTS/$NAME.png"
    alive "$PID" "after the $LOOK $SHOT screenshot"
    xcrun simctl terminate "$UDID" "$BUNDLE"
  done
done
ls -l "$SHOTS"
'''
WHY_RUN = r'''tail -n 40 "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log" || true
find ~/Library/Logs/DiagnosticReports -name 'ScenicDrive*' -print -exec head -c 4000 {} \; || true
xcrun simctl spawn booted log show --last 5m --style compact --predicate 'process == "ScenicDrive"' | tail -n 60 || true
'''


def expected(job_env):
    """The whole workflow, as parsed YAML. Equality, not a scan."""
    return {
        "name": "ios-screenshot",
        "on": {"workflow_dispatch": None},
        "concurrency": {"group": "ios-screenshot-${{ github.ref }}", "cancel-in-progress": True},
        "permissions": {"contents": "read"},
        "defaults": {"run": {"shell": "bash"}},
        "jobs": {"simulator-screenshot": {
            "runs-on": "macos-15",
            "timeout-minutes": 30,
            "env": job_env,
            "steps": [
                {"uses": "actions/checkout@v4"},
                {"name": "toolchain and the simulators this image carries", "run": TOOLCHAIN_RUN},
                {"name": PICK_STEP, "run": PICK_RUN},
                {"name": BUILD_STEP, "run": BUILD_RUN},
                {"name": CAPTURE_STEP, "run": CAPTURE_RUN},
                {"name": "upload the screenshots", "uses": "actions/upload-artifact@v4",
                 "with": {"name": "ios-screenshots", "path": "DerivedData/screens/*.png", "retention-days": 7,
                          "if-no-files-found": "error"}},
                {"name": "why it failed", "if": "failure()", "run": WHY_RUN},
            ],
        }},
    }


# (what it breaks, exact text in the shipped workflow, replacement), each applied ALONE to a copy; an anchor that
# does not occur exactly once is a hard failure of --prove-red, never a skipped row.
ON = "on:\n  workflow_dispatch:\n"
PERMS = "permissions:\n  contents: read\n"
JOB = "  simulator-screenshot:\n    runs-on: macos-15\n"
ENVLINE = "      DEVELOPER_DIR: /Applications/Xcode_26.3.app/Contents/Developer\n"
OTHER_XCODE = "      DEVELOPER_DIR: /Applications/Xcode_16.4.app/Contents/Developer\n"
PICK = f"      - name: {PICK_STEP}\n        run: |\n"
BUILD = f"      - name: {BUILD_STEP}\n        run: |\n"
CAPTURE = f"      - name: {CAPTURE_STEP}\n        run: |\n"
GUARD = '          test -d "$DEVELOPER_DIR" || { echo "ios-screenshot: $DEVELOPER_DIR is not on this image"; exit 1; }\n'
TEE = 'build | tee "$GITHUB_WORKSPACE/DerivedData/xcodebuild.log"\n'
LAUNCH = ('              LAUNCHED=$(xcrun simctl launch "$UDID" "$BUNDLE" -homeDetent "$DETENT" -menuRow "$ROW"'
          ' -screen "$SCREEN" "${DONE[@]}" "${SIZE[@]}")\n')
ALIVE = '              alive "$PID" "${WAIT}s after the $LOOK $SHOT launch"\n'
PLAN_SETTLE = "          PLAN_SETTLE=6\n"
PLAN_ARM = "NAME=plan-$SHOT-$LOOK WAIT=$PLAN_SETTLE ;;"
SHOTS_LIST = ('            LIST="collapsed medium fastest settings paywall surprise drive onboarding disclaimer'
              ' preview nothingPretty offered loop trip saved legal"\n')
LOOKS = "          for LOOK in light dark ax5; do\n"
AX5_SIZE = "              SIZE=(-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL)\n"
AX5_LIST = '              LIST="preview nothingPretty offered loop trip saved"\n'
LS = '          ls -l "$SHOTS"\n'


def after(anchor, line):
    return anchor.replace("\n        run: |\n", f"\n        {line}\n        run: |\n")


MUTATIONS = [
    ("a push trigger added", ON, ON + "  push:\n    branches: [main]\n"),
    ("on: as a list that includes pull_request", ON, "on: [workflow_dispatch, pull_request]\n"),
    ("a schedule beside workflow_dispatch", ON, ON + "  schedule:\n    - cron: '0 6 * * *'\n"),
    ("workflow-level permissions widened", PERMS, "permissions:\n  contents: write\n"),
    ("JOB-level permissions: write-all", JOB, "  simulator-screenshot:\n    permissions: write-all\n    runs-on: macos-15\n"),
    ("the shell default dropped", "defaults:\n  run:\n    shell: bash\n", "defaults:\n  run:\n    shell: sh\n"),
    ("STEP-level shell: sh on the capture step", CAPTURE, after(CAPTURE, "shell: sh")),
    ("RUN-BODY: set +o pipefail above the build", "          xcodebuild \\\n", "          set +o pipefail\n          xcodebuild \\\n"),
    ("RUN-BODY: || true after the build pipeline", TEE, TEE.rstrip("\n") + " || true\n"),
    ("continue-on-error on the capture step", CAPTURE, after(CAPTURE, "continue-on-error: true")),
    ("continue-on-error on the job", JOB, "  simulator-screenshot:\n    continue-on-error: true\n    runs-on: macos-15\n"),
    ("SKIPPED CAPTURE: if: false on the capture step", CAPTURE, after(CAPTURE, "if: false")),
    ("SKIPPED BUILD: a condition never true on dispatch", BUILD, after(BUILD, "if: github.event_name == 'push'")),
    ("SKIPPED PICK: if: false on the simulator step", PICK, after(PICK, "if: false")),
    ("SKIPPED JOB: if: false on the job", JOB, "  simulator-screenshot:\n    if: false\n    runs-on: macos-15\n"),
    ("a larger runner", "    runs-on: macos-15\n", "    runs-on: macos-15-xlarge\n"),
    ("a matrix on the job", JOB, "  simulator-screenshot:\n    strategy:\n      matrix:\n        os: [macos-15, macos-15-xlarge]\n    runs-on: macos-15\n"),
    ("the timeout removed", "    timeout-minutes: 30\n", ""),
    ("the timeout above the cap", "    timeout-minutes: 30\n", "    timeout-minutes: 45\n"),
    ("a SECOND env key at the job level", ENVLINE, ENVLINE + "      GH_TOKEN: a-token\n"),
    ("DEVELOPER_DIR pointed elsewhere (the image default, 16.4)", ENVLINE, OTHER_XCODE),
    ("env: at the WORKFLOW level, inherited by every job", PERMS, PERMS + "\nenv:\n  DEVELOPER_DIR: /Applications/Xcode_16.4.app/Contents/Developer\n"),
    ("a token handed to the capture step", CAPTURE, f"      - name: {CAPTURE_STEP}\n        env:\n          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}\n        run: |\n"),
    ("the DEVELOPER_DIR existence guard deleted (a silent fall back to the image default)", GUARD, ""),
    ("a third-party action", "      - uses: actions/checkout@v4\n", "      - uses: actions/checkout@v4\n      - uses: someone/else@v1\n"),
    ("upload-artifact unpinned", "        uses: actions/upload-artifact@v4\n", "        uses: actions/upload-artifact@main\n"),
    ("a push step", LS, LS + "          git push origin HEAD\n"),
    ("a commit step", "      - name: upload the screenshots\n",
     "      - name: keep them\n        run: git add -f DerivedData/screens && git commit -m screens\n      - name: upload the screenshots\n"),
    ("CRASH UNSEEN: the liveness check after the settle deleted", ALIVE, ""),
    ("CRASH UNSEEN: || true after the launch", LAUNCH, LAUNCH.rstrip("\n") + " || true\n"),
    ("T-0271: the -screen argument dropped (settings and paywall shots become home shots)", LAUNCH,
     LAUNCH.replace(' -screen "$SCREEN"', "")),
    ("T-0336: onboarding done for no shot (every shot but drive becomes onboarding)", LAUNCH,
     LAUNCH.replace(' "${DONE[@]}"', "")),
    ("T-0324: the drive shot dropped", SHOTS_LIST, SHOTS_LIST.replace(" drive onboarding", " onboarding")),
    ("T-0336: the plan-sheet shots dropped", SHOTS_LIST,
     SHOTS_LIST.replace(" preview nothingPretty offered loop trip saved", "")),
    ("T-0346: the AX5 pass dropped (no plan card seen at the largest text size)", LOOKS,
     LOOKS.replace(" ax5;", ";")),
    ("T-0346: the AX5 pass launched at the default text size", LAUNCH, LAUNCH.replace(' "${SIZE[@]}"', "")),
    ("T-0346: the AX5 pass at a smaller accessibility size (AX3)", AX5_SIZE,
     AX5_SIZE.replace("AccessibilityXXXL", "AccessibilityL")),
    ("T-0346: the AX5 trip card dropped (the card this task was filed for)", AX5_LIST,
     AX5_LIST.replace(" trip", "")),
    ("T-0346: the AX5 pass shoots every home screen too (the 30-minute cap)", AX5_LIST,
     SHOTS_LIST.replace("            ", "              ")),
    ("T-0336: the plan-offered shot dropped (T-0334's offer card unseen)", SHOTS_LIST,
     SHOTS_LIST.replace(" nothingPretty offered", " nothingPretty")),
    ("T-0336: the onboarding and legal shots dropped", SHOTS_LIST,
     SHOTS_LIST.replace(" onboarding disclaimer", "").replace(' legal"', '"')),
    ("T-0271: the settings and paywall shots dropped", SHOTS_LIST,
     '            LIST="collapsed medium fastest"\n'),
    ("a hard-coded device instead of the one chosen from the image's own lists",
     '            -destination "platform=iOS Simulator,id=$UDID" \\\n', "            -destination 'platform=iOS Simulator,name=iPhone 16' \\\n"),
    ("the runtime list no longer printed first", "          xcrun simctl list runtimes\n", ""),
    ("no settle before the capture (a black frame)", "          SETTLE=15\n", "          SETTLE=0\n"),
    ("T-0346: no settle before a plan-sheet capture", PLAN_SETTLE, "          PLAN_SETTLE=0\n"),
    ("T-0346: the plan shots wait the map settle (the 30-minute cap)", PLAN_ARM,
     "NAME=plan-$SHOT-$LOOK ;;"),
    ("T-0346: the wait chosen per shot but never slept", '              sleep "$WAIT"\n', ""),
    ("an empty capture uploads green", "          if-no-files-found: error\n", "          if-no-files-found: ignore\n"),
]
# Legitimate spellings that must stay GREEN - a check that refuses them teaches people to stop running it.
STILL_GREEN = [
    ("on: as a bare string", ON, "on: workflow_dispatch\n"),
    ("runs-on as a one-element list", "    runs-on: macos-15\n", "    runs-on: [macos-15]\n"),
    ("a comment added", "name: ios-screenshot\n", "# a comment changes nothing that runs\nname: ios-screenshot\n"),
]
