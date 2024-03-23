#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    #TODO: This may need to become `python3 /app/backup.py` if the script is not executable
    nautical
fi