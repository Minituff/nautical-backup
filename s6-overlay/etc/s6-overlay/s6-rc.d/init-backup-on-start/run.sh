#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script

if [ "$BACKUP_ON_START" = "true" ]; then
    logThis "Starting backup since BACKUP_ON_START is true" "INFO" "init"
    # The backup script must be run from the root directory
    cd /
    python3 /app/backup.py
fi