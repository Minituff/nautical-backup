# Use base docker image. Contains the docker commands we need to start and stop containers
FROM docker:24.0.6-cli

# Install dependencies
RUN apk add bash rsync tzdata dos2unix

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Move the entrypoint script to the root directory for ease of access
RUN mv app/entry.sh /entry.sh

# Make the script executable
RUN chmod +x app/backup.sh && dos2unix app/backup.sh

# Make the entry script executable
RUN chmod +x entry.sh && dos2unix entry.sh

# Set default timezone
ENV TZ=Etc/UTC

# Default = Every day at 4am
ENV CRON_SCHEDULE="0 4 * * *"

# Default enable the report file
ENV REPORT_FILE="true"

# Run the backup immediately on start
ENV BACKUP_ON_START="false"

# Run the entry script and pass all variables to it
ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
