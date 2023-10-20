# Use base docker image. Contains the docker commands we need to start and stop containers
FROM docker:24.0.6-cli

ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "I am running on $BUILDPLATFORM, building for $TARGETPLATFORM"
ENV BUILDPLATFORM=${BUILDPLATFORM}
ENV TARGETPLATFORM=${TARGETPLATFORM}

# Install dependencies
RUN apk add bash rsync tzdata dos2unix jq

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Make the entire /app folder executable
RUN chmod -R +x /app

# Make the all files in the /app folder Unix format
RUN find /app -type f -print0 | xargs -0 dos2unix

# Move the entrypoint script to the root directory for ease of access
RUN mv app/entry.sh /entry.sh

# Nautical Version (for example "v0.2.1") or "main" if not set
ARG NAUTICAL_VERSION="main"
ENV NAUTICAL_VERSION=${NAUTICAL_VERSION}

# Set default timezone
ENV TZ=Etc/UTC

# Default = Every day at 4am
ENV CRON_SCHEDULE="0 4 * * *"

# Default enable the report file
ENV REPORT_FILE="true"

# Run the backup immediately on start
ENV BACKUP_ON_START="false"

# Use the default rsync args "-raq" (recursive, archive, quiet)
ENV USE_DEFAULT_RSYNC_ARGS="true"

# Apply custom rsync args (in addition to the default args)
ENV RSYNC_CUSTOM_ARGS=""

# Require the Docker Label `nautical-backup.enable=true` to be present on each contianer or it will be skipped.
ENV REQUIRE_LABEL="false"

# Set the default log level to INFO
ENV LOG_LEVEL="INFO"

# Set the default log level for the repot file to INFO
ENV REPORT_FILE_LOG_LEVEL="INFO"

# Only write to the report file when backups run, not on initialization
ENV REPORT_FILE_ON_BACKUP_ONLY="true"

# Mirrior the source directory name to the destination directory name
# When true, and an source dir override is applied, then the destination directory will be same same as the new source directory 
ENV KEEP_SRC_DIR_NAME="true"

# Run the entry script and pass all variables to it
ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
