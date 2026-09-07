# The ETL toolchain, pinned. Every agent that builds the scenic index runs THIS, not whatever osmium happens
# to be on their box - because when two runs disagree the first suspect must never be "which osm2pgsql was
# that". Same rule as the swift image in .github/workflows/linux-core.yml: pinned BY DIGEST, because a tag
# moves and a moving tag is a silent toolchain change that no diff shows.
#
# Bumping the digest is a deliberate task with a re-recorded set of goldens, never a drive-by.
#
#   docker build -t scenic-etl services/etl
#   docker run --rm -v "$PWD:/w" -w /w scenic-etl osmium --version
#
# ubuntu:24.04 (noble), resolved 2026-09-07. Ubuntu rather than a GDAL vendor image: osmium-tool, osm2pgsql
# and gdal-bin are all in noble's archive, so one apt layer gets the whole toolchain from one distribution
# that pins them against each other, instead of three upstreams that do not.
FROM ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# osmium-tool   extract by bbox, tags-filter, and the tagged-PBF rewrite
# osm2pgsql     --flex import for the per-way feature pass
# gdal-bin      ogr2ogr / gdalwarp for 3DEP, canopy, impervious and the byway overlays
# python3-*     the etl package itself; from apt, not pip, because Debian's python3 is externally-managed
# sqlite3       corpus.sqlite is built and inspected here
RUN apt-get update -q \
 && apt-get install -y -q --no-install-recommends \
      ca-certificates \
      curl \
      gdal-bin \
      osmium-tool \
      osm2pgsql \
      python3 \
      python3-pytest \
      python3-yaml \
      sqlite3 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /w
