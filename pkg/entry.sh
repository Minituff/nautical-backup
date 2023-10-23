#!/bin/bash

if [ "$TEST_MODE" == "true" ]; then
    echo "Running in test mode"
    source "$(dirname $0)"/logger.sh # Use the logger script
    source "$(dirname $0)"/utils.sh
    source "$(dirname $0)"/env.sh 
else
    source /app/logger.sh # Use the logger script
    source /app/utils.sh
    source app/env.sh
fi

# Echo the CRON schedule for logging/debugging
logThis "Installing CRON schedule: $CRON_SCHEDULE in TZ: $TZ" "DEBUG" "init"

# Dump the current cron jobs to a temporary file
crontab -l >tempcron

# Remove the existing cron job for your backup script from the file
sed -i '/\/app\/backup.sh/d' tempcron

# Add the new cron job to the file
echo "$CRON_SCHEDULE bash /app/backup.sh" >>tempcron

# Install the new cron jobs and remove the tempcron file
crontab tempcron && rm tempcron

# Verify the source and destination locations
verify_source_location $SOURCE_LOCATION
verify_destination_location $DEST_LOCATION

if [ "$BACKUP_ON_START" = "true" ]; then
    echo "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    bash ./app/backup.sh
fi

if [ "$EXIT_AFTER_INIT" = "true" ]; then
    echo "Exiting since EXIT_AFTER_INITis true" "INFO" "init"
    exit 0
fi

logThis "Initialization complete. Awaiting CRON schedule: $CRON_SCHEDULE" "INFO" "init"

/usr/sbin/crond -f -l 8 # Start cron and keep container running
