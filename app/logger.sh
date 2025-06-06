#!/usr/bin/with-contenv bash

declare -A levels=([TRACE]=0 [DEBUG]=1 [INFO]=2 [WARN]=3 [ERROR]=4)

# Defaults
script_logging_level="INFO"
report_file_logging_level="INFO"
report_file_on_backup_only="true"

# Override the defaults
if [ ! -z "$LOG_LEVEL" ]; then
    script_logging_level=$LOG_LEVEL
fi

if [ ! -z "$REPORT_FILE_LOG_LEVEL" ]; then
    report_file_logging_level=$REPORT_FILE_LOG_LEVEL
fi

# Convert logging level variables to uppercase for array lookup
script_logging_level=$(echo "$script_logging_level" | tr '[:lower:]' '[:upper:]')
report_file_logging_level=$(echo "$report_file_logging_level" | tr '[:lower:]' '[:upper:]')


if [ ! -z "$REPORT_FILE_ON_BACKUP_ONLY" ]; then
    report_file_on_backup_only=$REPORT_FILE_ON_BACKUP_ONLY
fi

report_file="Backup Report - $(date +'%Y-%m-%d').txt"

delete_report_file() {
    rm -f "$DEST_LOCATION/Backup Report - "*.txt
}

create_new_report_file() {
    if [ "$REPORT_FILE" = "true" ]; then
        delete_report_file
        # Initialize the current report file with a header
        echo "Backup Report - $(date)" >"$DEST_LOCATION/$report_file"
    fi
}

logThis() {
    local log_message=$1
    local log_priority=${2:-INFO}
    local message_type=${3:-"default"}

    # Convert log_priority to uppercase
    log_priority=$(echo "$log_priority" | tr '[:lower:]' '[:upper:]')

    # Check if level exists
    if [ -z "${levels[$log_priority]}" ]; then
        echo "Invalid log level: $log_priority"
        return 1
    fi
    [[ ${levels[$log_priority]} ]] || return 1

    # Check if level is enough for console logging
    if ((${levels[$log_priority]} >= ${levels[$script_logging_level]})); then
        echo "${log_priority}: ${log_message}"
    fi

    # Check if level is enough for report file logging
    if [ "$REPORT_FILE" = "true" ] && ((${levels[$log_priority]} >= ${levels[$report_file_logging_level]})); then
        if ! ([ "$message_type" == "init" ] && [ "$report_file_on_backup_only" == "true" ]); then
            echo "$(date) - ${log_priority}: ${log_message}" >>"$DEST_LOCATION/$report_file"
        fi
    fi
}