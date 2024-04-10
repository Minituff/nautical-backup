#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script
source /app/utils.sh

# TODO: Make this call python file
install_cron(){
    # Echo the CRON schedule for logging/debugging
    logThis "Installing CRON schedule: $CRON_SCHEDULE in TZ: $TZ" "DEBUG" "init"

    # Dump the current cron jobs to a temporary file
    crontab -l >tempcron

    # Remove the existing cron job for your backup script from the file
    sed -i '/nautical/d' tempcron

    # Add the new cron job to the file
    echo "$CRON_SCHEDULE with-contenv nautical" >>tempcron

    # Install the new cron jobs and remove the tempcron file
    crontab tempcron && rm tempcron
}
install_cron

# Verify the source and destination locations
verify_source_location $SOURCE_LOCATION
verify_destination_location $DEST_LOCATION

#? Old bash methods
# initialize_db "$NAUTICAL_DB_PATH" "$NAUTICAL_DB_NAME"
# seed_db

# The script must be run from the root directory
cd /
with-contenv python3 /app/db.py

# Simlinks the nautical command to the backup script (python)
initialize_nautical


# :nocov:
if [ "$EXIT_AFTER_INIT" = "true" ]; then
    logThis "Exiting since EXIT_AFTER_INIT is true" "INFO" "init"
    exit 0
fi
# :nocov:
