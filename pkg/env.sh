#!/usr/bin/with-contenv bash

if [ -z "$TEST_MODE" ]; then
    TEST_MODE="false"
fi
export TEST_MODE

if [ "$TEST_MODE" == "true" ]; then
    NAUTICAL_VERSION=Test
    TARGETPLATFORM=TestPlatform
fi

source /app/utils.sh # This also loads the logger

create_new_report_file
logThis "Nautical Backup Version: $NAUTICAL_VERSION" "INFO" "init"
logThis "Built for the platform: $TARGETPLATFORM" "DEBUG" "init"

logThis "Perparing enviornment variables..." "DEBUG" "init"

handle_env() {
  # Export and log this env
  local var_name="$1"
  local var_value="$2"

  logThis "$var_name: $var_value" "DEBUG" "init"
  export_env "$var_name" "$var_value"
}


# Path to the defaults file
DEFAULTS_FILE="/app/defaults.env"

# Check if the defaults file exists
if [ ! -f "$DEFAULTS_FILE" ]; then
    logThis "Defaults file not found: $DEFAULTS_FILE" "ERROR" "init"
    exit 1
fi

logThis "Found defaults.env" "DEBUG" "init"
# Read each line in the defaults file
while IFS='=' read -r var default_value; do

    # Skip empty lines and lines starting with "#"
    [[ -z "$var" || "$var" == \#* ]] && continue
    echo "VAR: $var"

    # Set the variable to default if not already set
    if [ -z "${!var}" ]; then
        declare "$var=$default_value"
        handle_env "$var" "${!var}"
    fi
done < "$DEFAULTS_FILE"
