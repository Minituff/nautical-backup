# Use base docker image. Contains the docker commands we need to start and stop containers
FROM docker:24.0.6-cli-alpine3.18@sha256:789420937a26ebec564c47161164faf74d9de353539273ae7904229a5f3e5b54

# The platform this image is created for (linux/amd64, linux/arm64)
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM}

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

# Install dependencies
RUN apk add --no-cache \
    bash="${BASH_VERSION}" \
    rsync="${RSYNC_VERSION}" \
    tzdata="${TZ_DATA_VERSION}" \
    dos2unix="${DOS2UNIX_VERSION}" \
    jq="${JQ_VERSION}"

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
