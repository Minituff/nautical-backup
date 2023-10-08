# Use base docker image. Contains the docker commands we need to start and stop containers
FROM docker:24.0.6

# Install dependencies
RUN apk add bash rsync

# Copy all necessary files into the container (from /pkg in the repository to /app in the container)
COPY pkg app

# Move the entrypoint script to the root directory for ease of access
RUN mv app/entry.sh /entry.sh

# Make the script executable
RUN chmod +x app/backup.sh

# Make the entry script executable
RUN chmod +x entry.sh

# Default = Every day at 4am
ENV CRON_SCHEDULE="0 4 * * *"

# Run the entry script and pass all variables to it
ENTRYPOINT [ "bash", "-c", "exec ./entry.sh \"${@}\"", "--"]
