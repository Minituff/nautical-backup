#!/bin/bash

if [ "$TEST_MODE" == "true" ]; then
    source pkg/logger.sh # Use the logger script
    source pkg/utils.sh
    source pkg/env.sh
else
    source /app/logger.sh # Use the logger script
    source /app/utils.sh
    source app/env.sh
fi

if [ "$TEST_MODE" == "false" ]; then
    echo "Skipping CRON schedule installation in test mode"

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
fi

# Verify the source and destination locations
verify_source_location $SOURCE_LOCATION
verify_destination_location $DEST_LOCATION

if [ "$BACKUP_ON_START" = "true" ]; then
    echo "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    if [ "$TEST_MODE" == "true" ]; then
        source pkg/backup.sh
    else
        bash ./app/backup.sh
    fi
fi

if [ "$EXIT_AFTER_INIT" = "true" ]; then
    echo "Exiting since EXIT_AFTER_INIT is true" "INFO" "init"
    exit 0
fi

logThis "Initialization complete. Awaiting CRON schedule: $CRON_SCHEDULE" "INFO" "init"

if [ "$TEST_MODE" == "false" ]; then
    /usr/sbin/crond -f -l 8 # Start cron and keep container running
fi
