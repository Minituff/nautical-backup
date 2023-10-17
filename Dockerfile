# Use base docker image. Contains the docker commands we need to start and stop containers
FROM docker:24.0.6-cli

# Install dependencies
RUN apk add bash rsync tzdata dos2unix jq

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Move the entrypoint script to the root directory for ease of access
RUN mv app/entry.sh /entry.sh

# Make the script executable
RUN chmod +x app/backup.sh && dos2unix app/backup.sh

# Make the entry script executable
RUN chmod +x entry.sh && dos2unix entry.sh

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

# Log each rsync command to console before running (useful for debugging)
ENV LOG_RSYNC_COMMANDS="false"

# Use the default rsync args "-raq" (recursive, archive, quiet)
ENV USE_DEFAULT_RSYNC_ARGS="true"

# Apply custom rsync args (in addition to the default args)
ENV RSYNC_CUSTOM_ARGS=""

# Require the Docker Label `nautical-backup.enable=true` to be present on each contianer or it will be skipped.
ENV REQUIRE_LABEL="false"

# Run the entry script and pass all variables to it
ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
