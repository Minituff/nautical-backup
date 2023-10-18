#!/bin/bash

declare -A levels=([DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3)
script_logging_level=$LOG_LEVEL
report_file_logging_level=$REPORT_FILE_LOG_LEVEL

report_file="Backup Report - $(date +'%Y-%m-%d').txt"

create_new_report_file() {
    if [ "$REPORT_FILE" = "true" ]; then
        rm -f "$DEST_LOCATION/Backup Report - "*.txt
        # Initialize the current report file with a header
        echo "Backup Report - $(date)" >"$DEST_LOCATION/$report_file"
    fi
}

logThis() {
    local log_message=$1
    local log_priority=${2:-INFO}

    # Check if level exists
    [[ ${levels[$log_priority]} ]] || return 1

    # Check if level is enough for console logging
    if ((${levels[$log_priority]} >= ${levels[$script_logging_level]})); then
        echo "${log_priority}: ${log_message}"
    fi

    # Check if level is enough for report file logging
    if [ "$REPORT_FILE" = "true" ] && ((${levels[$log_priority]} >= ${levels[$report_file_logging_level]})); then
        echo "$(date) - ${log_priority}: ${log_message}" >>"$DEST_LOCATION/$report_file"
    fi
}
