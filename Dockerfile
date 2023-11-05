# Use base docker image; it contains the docker commands we need to start and stop containers.
# Use this tool https://github.com/estesp/manifest-tool to get the multiplatform SHA. 
# For example: docker run --rm mplatform/mquery docker:cli
FROM docker:24.0.7-cli-alpine3.18@sha256:43651800218f833f6d09f586df8b174866a31b38e905ef1721658243cbe460a5

# The platform this image is created for (linux/amd64, linux/arm64)
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM}

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
RUN apk add --no-cache \
    bash="${BASH_VERSION}" \
    rsync="${RSYNC_VERSION}" \
    tzdata="${TZ_DATA_VERSION}" \
    dos2unix="${DOS2UNIX_VERSION}" \
    jq="${JQ_VERSION}" \ 
    curl="${CURL_VERSION}" \
    socat="${SOCAT_VERSION}"

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Make the entire /app folder executable
RUN chmod -R +x /app

# Make the all files in the /app folder Unix format
RUN find /app -type f -print0 | xargs -0 dos2unix

# Not needed anymore, so we can delete it
RUN apk del dos2unix

# Move the entrypoint script to the root directory for ease of access
RUN mv app/entry.sh /entry.sh

# Nautical Version (for example "v0.2.1") or "main" if not set
ARG NAUTICAL_VERSION="main"
ENV NAUTICAL_VERSION=${NAUTICAL_VERSION}

# Run the entry script and pass all variables to it
ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
