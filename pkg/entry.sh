#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script
source /app/utils.sh

if [ "$TEST_MODE" != "true" ]; then
    # :nocov:
    # Echo the CRON schedule for logging/debugging
    logThis "Installing CRON schedule: $CRON_SCHEDULE in TZ: $TZ" "DEBUG" "init"

    # Dump the current cron jobs to a temporary file
    crontab -l >tempcron

    # Remove the existing cron job for your backup script from the file
    sed -i '/nautical/d' tempcron

    # Add the new cron job to the file
    echo "$CRON_SCHEDULE bash nautical" >>tempcron

    # Install the new cron jobs and remove the tempcron file
    crontab tempcron && rm tempcron
    # :nocov:
fi

# Verify the source and destination locations
verify_source_location $SOURCE_LOCATION
verify_destination_location $DEST_LOCATION

initialize_db "$NAUTICAL_DB_PATH" "$NAUTICAL_DB_NAME"
initialize_nautical

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    bash nautical
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
