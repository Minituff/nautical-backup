#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script
source /app/utils.sh

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    logThis "Note - BACKUP_ON_START logs are not available until all containers are processed, however the report file updates in real-time." "INFO" "init"
    # The backup script must be run from the root directory
    cd /
    
    # Simlinks the nautical command to the backup script (python)
    # This is handled via the Dockerfile, but will run again if the `nautical` command is not found
    initialize_nautical

    # Run backup script
    nautical
fi

# S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0 must be set in the container enviornmet since the backup could take over 5 seconds