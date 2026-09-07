#!/bin/sh
# Xcode Cloud runs this right after cloning, before resolving packages.
# Kept deliberately tiny: the open stack (MapLibre, Ferrostar) needs no download tokens, so there is no
# ~/.netrc to write. It prints the toolchain so a wrong-Xcode build is diagnosable from the log.
set -eu
echo "ci_post_clone: $(xcodebuild -version | tr '\n' ' ')"
echo "ci_post_clone: $(swift --version 2>&1 | head -1)"
echo "ci_post_clone: branch=${CI_BRANCH:-?} workflow=${CI_WORKFLOW:-?} build=${CI_BUILD_NUMBER:-?}"
