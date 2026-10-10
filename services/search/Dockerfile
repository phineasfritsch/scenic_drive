# Photon 1.3.0 for Scenic Drive's address search (T-0359 R1). Built by the owner on the search VPS; never by an agent.
# The base is pinned by its index digest and the jar by the sha256 GitHub publishes for the release asset, so a
# moved tag or a swapped jar fails the build instead of shipping. ops/lib/check-search-pins.py refuses either unpinned.
FROM eclipse-temurin:21-jre@sha256:cff19e6215689161eb6162c11b86b0c60ddf802164f2eaf48d570f8fb79a36c5

ARG PHOTON_VERSION=1.3.0
ADD --checksum=sha256:a89707c0045e4807b2a1180e132e68e108d998709f48b6c94b98a6e281f571a5 \
    https://github.com/komoot/photon/releases/download/1.3.0/photon-1.3.0.jar /opt/photon/photon.jar

RUN useradd --system --home-dir /data --shell /usr/sbin/nologin photon
USER photon
WORKDIR /data

# /data holds photon_data/, unpacked from the US 1.0 db (README). -listen-ip 0.0.0.0 is inside the compose network
# only: compose publishes no Photon port. -max-results caps `limit` at the Worker's SEARCH_LIMIT.
EXPOSE 2322
ENTRYPOINT ["java", "-Xmx6g", "-jar", "/opt/photon/photon.jar", "serve", "-data-dir", "/data", \
            "-listen-ip", "0.0.0.0", "-listen-port", "2322", "-max-results", "8", "-default-language", "en", \
            "-query-timeout", "5"]
