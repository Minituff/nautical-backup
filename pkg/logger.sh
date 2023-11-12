#!/usr/bin/with-contenv bash

declare -A levels=([TRACE]=0 [DEBUG]=1 [INFO]=2 [WARN]=3 [ERROR]=4)

# Defaults
script_logging_level="INFO"
report_file_logging_level="INFO"
report_file_on_backup_only="true"

# This is needed since the logger is called first. Otherwise it would be in env.sh
# if [ "$TEST_MODE" == "true" ]; then
#     SOURCE_LOCATION="tests/src"
#     printf "${SOURCE_LOCATION}" > /var/run/s6/container_environment/SOURCE_LOCATION
#     export SOURCE_LOCATION
    
#     DEST_LOCATION="tests/dest"
#     printf "${DEST_LOCATION}" > /var/run/s6/container_environment/DEST_LOCATION
#     export DEST_LOCATION
# fi

# Override the defaults
if [ ! -z "$LOG_LEVEL" ]; then
    script_logging_level=$LOG_LEVEL
fi

if [ ! -z "$REPORT_FILE_LOG_LEVEL" ]; then
    report_file_logging_level=$REPORT_FILE_LOG_LEVEL
fi

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

    # Check if level exists
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

# logThis "SOURCE_LOCATION: ${SOURCE_LOCATION}" "DEBUG" "INIT"
# logThis "DEST_LOCATION: ${DEST_LOCATION}" "DEBUG" "INIT"