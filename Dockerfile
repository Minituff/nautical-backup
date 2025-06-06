# Use base docker image; it contains the docker commands we need to start and stop containers.
# Use this tool https://github.com/estesp/manifest-tool to get the multiplatform SHA. 
# For example: docker run --rm mplatform/mquery docker:cli
FROM docker:24.0.7-cli-alpine3.18@sha256:a2a608408fa15d6694543a7308c2bfd1a7ea90a0e4ca989d0471ca7b8348fabb

# The platform this image is created for (linux/amd64, linux/arm64)
ARG TARGETPLATFORM
ENV TARGETPLATFORM=${TARGETPLATFORM}

# Nautical Version (for example "v0.2.1") or "main" if not set
ARG NAUTICAL_VERSION="main"
ENV NAUTICAL_VERSION=${NAUTICAL_VERSION}

LABEL maintainer="minituff" \
  # Prevent self backups
  nautical-backup.enable="false" \
  nautical-backup.stop-before-backup="false"

ARG TEST_MODE="-1"

# renovate: datasource=github-releases depName=just-containers/s6-overlay versioning=loose
ENV S6_OVERLAY_VERSION="3.1.6.2"

# Install S6 Overlay
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz

# This is needed because each arch needs a different S6 build. All other S6 files are the same
RUN apk add --no-cache curl --virtual=s6build-dependencies && \
    S6_OVERLAY_ARCH=$(case "${TARGETPLATFORM}" in \
            "linux/amd64")   echo "x86_64";; \
            "linux/arm64")   echo "aarch64";; \
	        *)	echo "x86_64";; \
          esac) && \
    echo "Installing S6 Overlay v${S6_OVERLAY_VERSION} -${S6_OVERLAY_ARCH} for ${TARGETPLATFORM}" && \
    curl -sSL "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_OVERLAY_ARCH}.tar.xz" -o "/tmp/s6-arch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-arch.tar.xz && \
    apk del --purge s6build-dependencies

# Add s6 optional symlinks (helps fix paths)
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-symlinks-noarch.tar.xz
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-symlinks-arch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-symlinks-arch.tar.xz

# Copy all necessary files into the container (from /app in the repository to /app in the container)
COPY app app
COPY requirements.txt app/requirements.txt

# Packages are sourced from https://pkgs.alpinelinux.org/packages?branch=v3.18&repo=main tracked from https://repology.org/projects/?inrepo=alpine_3_18
# Renovate-Bot will update this Dockerfile once and updae is realsed to these packages. The comments are needed to match pkg info.

# renovate: datasource=repology depName=alpine_3_18/bash versioning=loose
ENV BASH_VERSION="5.2.15"
# renovate: datasource=repology depName=alpine_3_18/rsync versioning=loose
ENV RSYNC_VERSION="3.2.7"
# renovate: datasource=repology depName=alpine_3_18/tzdata versioning=loose
ENV TZ_DATA_VERSION="2024"
# renovate: datasource=repology depName=alpine_3_18/dos2unix versioning=loose
ENV DOS2UNIX_VERSION="7.4.4"
# renovate: datasource=repology depName=alpine_3_18/jq versioning=loose
ENV JQ_VERSION="1.6"
# renovate: datasource=repology depName=alpine_3_18/curl versioning=loose
ENV CURL_VERSION="8.9.1"
# renovate: datasource=repology depName=alpine_3_18/7zip versioning=loose
ENV SEVENZIP_VERSION="22.01"
# renovate: datasource=repology depName=alpine_3_18/python3 versioning=loose
ENV PYTHON_VERSION="3.11"
# renovate: datasource=repology depName=alpine_3_18/py3-pip versioning=loose
ENV PIP_VERSION="23.1.2"
# renovate: datasource=repology depName=alpine_3_18/ruby-full versioning=loose
ENV RUBY_VERSION="3.2.4"

# Hide the S6 init logs. 2 = start and stop operations, 1 = warnings and errors, 0 = errors. Default 2: Options 0 (low) -- 5 (high)
ENV S6_VERBOSITY=1

# Set the maximum time to wait for services to be ready (0=forever). Needed for BACKUP_ON_START since it could take time.
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# Install dependencies
RUN \
    echo "**** Install build packages (will be uninstalled later) ****" && \
    apk add --no-cache --virtual=build-dependencies \
    dos2unix=~"${DOS2UNIX_VERSION}" && \
    echo "**** Install runtime packages (required at runtime) ****" && \
    apk add --no-cache \
    bash>="${BASH_VERSION}" \
    rsync>="${RSYNC_VERSION}" \
    tzdata>="${TZ_DATA_VERSION}" \
    jq>="${JQ_VERSION}" \ 
    curl>="${CURL_VERSION}" \
    7zip>="${SEVENZIP_VERSION}" \
    python3>="${PYTHON_VERSION}" \
    py3-pip>="${PIP_VERSION}" && \
    echo "**** Making the entire /app folder executable ****" && \
    chmod -R +x /app && \
    echo "**** Making the all files in the /app folder Unix format ****" && \
    find /app -type f -print0 | xargs -0 dos2unix && \
    echo "**** Making all files in ./etc/s6-overlay/s6-rc.d Unix format ****" && \
    find ./etc/s6-overlay/s6-rc.d -type f -print0 | xargs -0 dos2unix && \
    echo "**** Install Python packages ****" && \
    python3 -m pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
    echo "**** Cleanup ****" && \
    apk del --purge build-dependencies

# Conditionally execute commands based on TESTMODE
RUN if [ "$TEST_MODE" != "-1" ]; then \
      echo "=== TEST MODE ENABLED ===" && \
      echo "**** Installing TEST packages ****" && \
      apk add --no-cache \
      ruby-full=~"${RUBY_VERSION}" && \
      echo "**** Installing ruby packages (for tests) ****" && \
      gem install bashcov simplecov-cobertura simplecov-html; \
    fi

# Required for Python imports to work
ENV PYTHONPATH="."

# Add S6 files
COPY --chmod=755 s6-overlay/ /

VOLUME [ "/app/source" ]
VOLUME [ "/app/destination" ]
VOLUME [ "/config" ]

# Only should be exposed when running in test mode
VOLUME [ "/tests" ]

# Publish this port to enable the HTTP endpoints
EXPOSE 8069

# Hit the healthcheck endpoint to ensure the container is healthy every 30 seconds
HEALTHCHECK --start-period=10s --interval=20s --timeout=10s CMD curl --fail http://localhost:8069 || exit 1   

# Run the entry script and pass all variables to it
ENTRYPOINT ["/init"]
