#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    bash nautical
fi