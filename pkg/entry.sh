#!/usr/bin/with-contenv bash

if [ "$TEST_MODE" == "true" ]; then
    source pkg/utils.sh
    source pkg/logger.sh # Use the logger script
    # source pkg/env.sh
else
    # :nocov:
    source /app/logger.sh # Use the logger script
    source /app/utils.sh
    # source app/env.sh
    # :nocov:
fi

if [ "$TEST_MODE" != "true" ]; then
    # :nocov:
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
    # :nocov:
fi

# Verify the source and destination locations
verify_source_location $SOURCE_LOCATION
verify_destination_location $DEST_LOCATION

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    if [ "$TEST_MODE" == "true" ]; then
        source pkg/backup.sh
    else
        bash ./app/backup.sh
    fi
fi

# :nocov:
if [ "$EXIT_AFTER_INIT" = "true" ]; then
    logThis "Exiting since EXIT_AFTER_INIT is true" "INFO" "init"
    exit 0
fi

if [ "$RETURN_AFTER_INIT" = "true" ]; then
    logThis "Exiting since RETURN_AFTER_INIT is true" "INFO" "init"
    return
fi

# :nocov:
