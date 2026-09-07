---
id: T-0038
title: services/etl/Dockerfile was never created - T-0023 shipped without the pinned ETL image
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:50:28Z
lease_expires_at: 2026-09-07T18:50:28Z
worktree: ../wt/T-0038
branch: task/T-0038
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-22
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`T-0023`'s brief required `services/etl/Dockerfile` pinned BY DIGEST with osmium-tool, osm2pgsql, GDAL and
python. It was never written. The file does not exist, `git ls-files services/etl` does not list it, and
reviewer-12 signed the task off anyway - nothing in the suite reads it, so nothing went red.

That matters for T-0024 onward: the Bay Area extract runs osmium/osm2pgsql, and without a pinned image every
agent runs a different toolchain and blames the data when the output differs.

- `services/etl/Dockerfile`, base image pinned by `@sha256:` digest (same rule as `swift:6.1-noble` in
  `.github/workflows/linux-core.yml`), with osmium-tool, osm2pgsql, GDAL/ogr2ogr and python3.
- A test that the Dockerfile exists and its `FROM` line carries a `@sha256:` digest - anchored on the file, not
  a comment, so "we'll pin it later" fails the suite instead of passing quietly.
- Demonstrate red: delete the digest from `FROM`, show the test fail, restore, show it pass.

## Log
- 2026-09-07T15:50:28Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:50:28Z

- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-21 is taken, so agent/reviewer-22.
  Branch stacked on `task/T-0023`, which owns `services/etl/` and is reviewed but not merged (CI is down).

- **The image.** `services/etl/Dockerfile`, `FROM ubuntu:24.04@sha256:33ceb719...987517`, resolved 2026-09-07
  with `docker buildx imagetools inspect ubuntu:24.04`. Ubuntu rather than a GDAL vendor image because noble
  ships osmium-tool, osm2pgsql and gdal-bin in one archive that pins them against each other, instead of three
  upstreams that do not.

- **Built it, rather than asserting it builds.** In WSL, against the real digest:

      $ docker build -q -t scenic-etl:t0038 .
      sha256:6055593233884b3c93dc7495a2d633edd9544ff4223bf2cd4e65307b68944cd6

      $ docker run --rm scenic-etl:t0038 ...
      osmium version 1.16.0
      osm2pgsql version 1.11.0
      GDAL 3.8.4, released 2024/02/08          (ogr2ogr and gdalinfo both)
      Python 3.12.3
      sqlite3 3.45.1
      pyyaml 6.0.1  pytest 7.4.4

- **Ran this repo's own ETL suite inside it**, which is the thing the image exists for:

      $ docker run --rm -v "$d/etl:/w" -w /w scenic-etl:t0038 python3 -m pytest -q
      ..................s........................                              [100%]

- **The tests** (`services/etl/tests/test_dockerfile.py`, 7 of them) read the Dockerfile's INSTRUCTIONS, never
  its comments: continuations joined, comments and blanks dropped, then assertions on FROM and RUN. Every one
  demonstrated red by mutating the Dockerfile and restoring it:

      RED: osmium-tool dropped from the package list -> exit 1  test_every_tool_the_pipeline_shells_out_to_is_installed
      RED: gdal-bin dropped                          -> exit 1  test_every_tool_the_pipeline_shells_out_to_is_installed
      RED: apt-get dist-upgrade added                -> exit 1  test_the_package_list_is_not_upgraded_out_from_under_the_pin
      RED: installs by piping the internet into a shell -> exit 1  test_nothing_is_installed_by_piping_the_internet_into_a_shell
      RED: a second FROM sneaks in                   -> exit 1  test_there_is_exactly_one_base_image (+2)
      RED: digest stripped from FROM                 -> exit 1  test_the_base_image_is_pinned_by_digest
      RED: FROM ubuntu:latest                        -> exit 1  test_the_base_image_is_pinned_by_digest, ..._not_a_floating_tag
      GREEN restored                                 -> exit 0, Dockerfile byte-identical to the start

- **One of those tests was decorative and the red run is what caught it.** The pipe-to-shell check originally
  asked whether the literal string `"curl | bash"` appeared in the RUN body. It passed against
  `RUN curl -fsSL https://example.org/x.sh | bash` - which is what the pattern looks like in the wild - so it
  could not go red for the thing it was named after. Replaced with a regex over each RUN instruction
  separately, then re-demonstrated red. The harness script now asserts that each mutation actually changed the
  file before running pytest, so a demo can never silently test nothing.

- **Running the suite in the image found a real bug in T-0023's work, which is mine.**
  `test_the_manifest_is_actually_tracked_by_git` computed the repo root as `Path(__file__).parents[3]`. That
  arithmetic is right in a checkout and wrong everywhere else: inside the image, where only `services/etl` is
  mounted, it raised `IndexError: 3` out of pathlib without ever mentioning the manifest. reviewer-18 checked
  the "git missing from PATH" case and found it errored loudly; nobody checked "not inside a work tree", and
  the two fail differently.

  Fixed here rather than filed, because it is a live crash in a file this task's `touches:` already covers and
  this branch already contains T-0023: ask git for the root (`git rev-parse --show-toplevel`), skip LOUDLY
  when there is no work tree or no git binary, and keep failing when git IS present and the file is untracked.
  The missing-binary case needed its own arm - `subprocess.run` raises `FileNotFoundError` rather than
  returning non-zero, so the first version of the fix still died with a traceback in the image.

  Both behaviours re-demonstrated:

      in a checkout, manifest un-staged:  FAILED ...::test_the_manifest_is_actually_tracked_by_git   (still red)
      in a checkout, restored:            1 passed
      in the image (no git):              SKIPPED [1] tests/test_manifest.py:47: git is not installed here,
                                          cannot check tracking: [Errno 2] No such file or directory: 'git'

  A skip is not as good as a check. It is visible in the report, `ops/test` counts skips separately, and
  `ops/test` always runs in a checkout - so the branch CI takes is the one that enforces. Whoever reviews this
  should push on whether that is good enough, or whether the ETL image should simply ship git.

- **Verification, all local** (GitHub Actions has been refusing to execute since ~15:11 UTC: a recent run
  reports "recent account payments have failed or your spending limit needs to be increased", so every job on
  every branch dies in seconds with zero steps):

      $ bash ops/test        -> TESTS linux=93/76 ios=skipped failed=0 skipped=0 / OK      exit 0
      $ bash ops/check-pins  -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0          exit 0
      $ bash ops/queue-check -> QUEUE OK (39 tasks)                                        exit 0

  linux goes 86 -> 93: seven new Dockerfile tests.

- Handing to agent/reviewer-22; state -> review.
