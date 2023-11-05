# Use base docker image; it contains the docker commands we need to start and stop containers.
# Use this tool https://github.com/estesp/manifest-tool to get the multiplatform SHA. 
# For example: docker run --rm mplatform/mquery docker:cli
FROM docker:24.0.7-cli-alpine3.18@sha256:43651800218f833f6d09f586df8b174866a31b38e905ef1721658243cbe460a5

# The platform this image is created for (linux/amd64, linux/arm64)
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM}

# Nautical Version (for example "v0.2.1") or "main" if not set
ARG NAUTICAL_VERSION="main"
ENV NAUTICAL_VERSION=${NAUTICAL_VERSION}

LABEL maintainer="minituff"


# Set version for s6 overlay 
ARG S6_OVERLAY_VERSION="3.1.5.0"
# amd64 = "x86_64". arm = "aarch64"
ARG S6_OVERLAY_ARCH="x86_64" 

# Install S6 Overlay
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_OVERLAY_ARCH}.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-${S6_OVERLAY_ARCH}.tar.xz

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Packages are sourced from https://pkgs.alpinelinux.org/packages tracked from https://repology.org/projects/?inrepo=alpine_3_18
# Renovate-Bot will update this Dockerfile once and updae is realsed to these packages. The comments are needed to match pkg info.

# renovate: datasource=repology depName=alpine_3_18/bash versioning=loose
ENV BASH_VERSION="5.2.15-r5"
# renovate: datasource=repology depName=alpine_3_18/rsync versioning=loose
ENV RSYNC_VERSION="3.2.7-r4"
# renovate: datasource=repology depName=alpine_3_18/tzdata versioning=loose
ENV TZ_DATA_VERSION="2023c-r1"
# renovate: datasource=repology depName=alpine_3_18/dos2unix versioning=loose
ENV DOS2UNIX_VERSION="7.4.4-r1"
# renovate: datasource=repology depName=alpine_3_18/jq versioning=loose
ENV JQ_VERSION="1.6-r3"
# renovate: datasource=repology depName=alpine_3_18/curl versioning=loose
ENV CURL_VERSION="8.4.0-r0"
# renovate: datasource=repology depName=alpine_3_18/socat versioning=loose
ENV SOCAT_VERSION="1.7.4.4-r1"

# Install dependencies
RUN \
    echo "**** install build packages ****" && \
    apk add --no-cache --virtual=build-dependencies \
    dos2unix="${DOS2UNIX_VERSION}" && \
    echo "**** install runtime packages ****" && \
    apk add --no-cache \
    bash="${BASH_VERSION}" \
    rsync="${RSYNC_VERSION}" \
    tzdata="${TZ_DATA_VERSION}" \
    jq="${JQ_VERSION}" \ 
    curl="${CURL_VERSION}" \
    socat="${SOCAT_VERSION}" && \
    echo "**** Makeing the entire /app folder executable ****" && \
    chmod -R +x /app && \
    echo "**** Making the all files in the /app folder Unix format ****" && \
    find /app -type f -print0 | xargs -0 dos2unix && \
    echo "**** cleanup ****" && \
    apk del --purge \
    build-dependencies && \
    mv app/entry.sh /entry.sh

# add local files
COPY --chmod=755 root/ /

# Run the entry script and pass all variables to it
ENTRYPOINT ["/init"]
# ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
