#!/usr/bin/with-contenv bash

if [ ! -z "$TEST_MODE" ] && [ "$TEST_MODE" != "-1" ]; then
    if [ ! -z "$TEST_MODE" ]; then
        NAUTICAL_VERSION="Test-${TEST_MODE}"
    fi
    if [ ! -z "$TARGETPLATFORM" ]; then
        TARGETPLATFORM=TestPlatform
    fi
fi

source /app/utils.sh # This also loads the logger

handle_env() {
    # Export and log this env
    local var_name="$1"
    local var_value="$2"
    if [ ! -z "${var_value}" ]; then
        logThis "$var_name: $var_value" "DEBUG" "init"
    else
        logThis "$var_name: $var_value" "TRACE" "init"
    fi
    export_env "$var_name" "$var_value"
}

: "${REPORT_FILE:=true}" && handle_env REPORT_FILE "$REPORT_FILE"

create_new_report_file
logThis "Nautical Backup Version: $NAUTICAL_VERSION" "INFO" "init"
logThis "Built for the platform: $TARGETPLATFORM" "DEBUG" "init"

logThis "Perparing enviornment variables..." "DEBUG" "init"

# Path to the defaults file
DEFAULTS_FILE="/app/defaults.env"

# Check if the defaults file exists
if [ ! -f "$DEFAULTS_FILE" ]; then
    logThis "Enviornment defaults file not found: $DEFAULTS_FILE" "ERROR" "init"
    exit 1
fi

logThis "Found defaults.env" "DEBUG" "init"
# Read each line in the defaults file
while IFS= read -r line; do
    # Skip empty lines and lines starting with #
    [[ -z "$line" || "$line" == \#* ]] && continue

    # Extract variable name and value
    var="${line%%=*}"
    default_value="${line#*=}"

    # Handle empty string default_value
    if [ "$default_value" == '""' ]; then
        default_value=""
    fi

    # Set the variable to default if not already set
    if [ -z "${!var}" ]; then
        declare "$var=$default_value"
        handle_env "$var" "${!var}"
    fi
done <"$DEFAULTS_FILE"

# Get the container ID of the current container (Does not work on arm64)
SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)
if [ -z "${SELF_CONTAINER_ID}" ]; then
    SELF_CONTAINER_ID=$(cat etc/hostname) # Workaround for arm64
    if [ -z "${SELF_CONTAINER_ID}" ]; then
        SELF_CONTAINER_ID="nautical-backup"
    fi
fi
handle_env SELF_CONTAINER_ID "$SELF_CONTAINER_ID"
