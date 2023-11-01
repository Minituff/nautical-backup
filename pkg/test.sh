#!/bin/bash
# Change this as alpine updates
ALPINE_VERSION="3.18"

test_cron() {
    # Expected output
    EXPECTED_OUTPUT="$CRON_SCHEDULE bash /app/backup.sh"
    EXPECTED_OUTPUT2="0 8 * * * bash /app/backup.sh" # Requires setting in the docker compose or CLI

    # Run the command and capture its output
    ACTUAL_OUTPUT=$(crontab -l | grep bash)

    if [ "$ACTUAL_OUTPUT" != "$EXPECTED_OUTPUT" ]; then
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" != "$EXPECTED_OUTPUT" ]; then
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    echo "PASS: 'crontab -l | grep' bash returns $EXPECTED_OUTPUT"
}

test_bash() {
    EXPECTED_OUTPUT="/bin/bash"
    ACTUAL_OUTPUT=$(which bash)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which bash' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'bash --version' to check if it returns something
    if [[ $(bash --version) ]]; then
        echo "PASS: 'bash --version' returns a value."
    else
        echo "FAIL: 'bash --version' did not return a value."
        exit 1
    fi
}

test_rsync() {
    EXPECTED_OUTPUT="/usr/bin/rsync"
    ACTUAL_OUTPUT=$(which rsync)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which rsync' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'rsync --version' to check if it returns something
    if [[ $(rsync --version) ]]; then
        echo "PASS: 'rsync --version' returns a value."
    else
        echo "FAIL: 'rsync --version' did not return a value."
        exit 1
    fi
}

test_jq() {
    EXPECTED_OUTPUT="/usr/bin/jq"
    ACTUAL_OUTPUT=$(which jq)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which jq' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'jq --help' to check if it returns something
    if [[ $(jq --help) ]]; then
        echo "PASS: 'jq --help' returns a value."
    else
        echo "FAIL: 'jq --help' did not return a value."
        exit 1
    fi
}


test_curl() {
    EXPECTED_OUTPUT="/usr/bin/curl"
    ACTUAL_OUTPUT=$(which curl)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which curl' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'curl --version' to check if it returns something
    if [[ $(curl --version) ]]; then
        echo "PASS: 'curl --version' returns a value."
    else
        echo "FAIL: 'curl --version' did not return a value."
        exit 1
    fi
}

test_timeout() {
    EXPECTED_OUTPUT="/usr/bin/timeout"
    ACTUAL_OUTPUT=$(which timeout)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which timeout' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'timeout --version' to check if it returns something
    if [[ $(timeout --version) ]]; then
        echo "PASS: 'timeout --version' returns a value."
    else
        echo "FAIL: 'timeout --version' did not return a value."
        exit 1
    fi
}


test_tz() {
    EXPECTED_OUTPUT="America/Los_Angeles"
    ACTUAL_OUTPUT=$(echo $TZ)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'echo \$TZ' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'date | grep PDT' to check if it returns something
    if [[ $(date | grep PDT) ]]; then
        echo "PASS: 'date | grep PDT' returns a value."
    else
        echo "FAIL: 'date | grep PDT' did not return a value."
        exit 1
    fi
}

test_alpine_release() {
    # Capture the output of the command
    local output=$(cat /etc/alpine-release)
    
    # Check if the output starts with "3.18"
    if [[ $output == $ALPINE_VERSION* ]]; then
        echo "PASS: Alpine release is correct."
    else
        echo "FAIL: Alpine release."
        echo "Expected:"
        echo "$ALPINE_VERSION*"
        echo "Actual"
        echo "$output"
        exit 1
    fi
}

# Function to test if environment variables have expected values
test_env_vars() {
    local -n env_vars_to_test=$1 # Use nameref to pass associative array by reference
    local test_passed=true

    for var in "${!env_vars_to_test[@]}"; do
        if [ "${!var}" != "${env_vars_to_test[$var]}" ]; then
            echo "FAIL: '$var' expected value '${env_vars_to_test[$var]}', got '${!var}'."
            test_passed=false
        else
            echo "PASS: '$var' has expected value '${env_vars_to_test[$var]}'."
        fi
    done

    if [ "$test_passed" = true ]; then
        echo "All environment variables have expected values."
    else
        echo "Some environment variables do not have expected values."
        exit 1
    fi
}

# Declare an associative array with environment variable names and expected values
declare -A expected_env_vars=(
    ["TZ"]="Etc/UTC"
    ["TEST_MODE"]="false"
    ["CRON_SCHEDULE"]="0 4 * * *"
    ["REPORT_FILE"]="true"
    ["BACKUP_ON_START"]="false"
    ["USE_DEFAULT_RSYNC_ARGS"]="true"
    ["REQUIRE_LABEL"]="false"
    ["LOG_LEVEL"]="INFO"
    ["REPORT_FILE_LOG_LEVEL"]="INFO"
    ["REPORT_FILE_ON_BACKUP_ONLY"]="true"
    ["KEEP_SRC_DIR_NAME"]="true"
    ["EXIT_AFTER_INIT"]="false"
    ["LOG_RSYNC_COMMANDS"]="false"
    ["RUN_ONCE"]="false"
    ["SOURCE_LOCATION"]="/app/source"
    ["DEST_LOCATION"]="/app/destination"
    ["SKIP_CONTAINERS"]=""
    ["SKIP_STOPPING"]=""
    ["RSYNC_CUSTOM_ARGS"]=""
    ["OVERRIDE_SOURCE_DIR"]=""
    ["DEFAULT_OVERRIDE_DEST_DIR"]=""
    ["ADDITIONAL_FOLDERS"]=""
    ["ADDITIONAL_FOLDERS_WHEN"]="before"
    ["PRE_BACKUP_CURL"]=""
    ["POST_BACKUP_CURL"]=""
)

if [ "$1" == "test1" ]; then
    bash /entry.sh

    echo "Running integation tests..."

    test_cron
    test_tz
    test_bash
    test_rsync
    test_jq
    test_curl
    test_timeout
    test_alpine_release

    echo "All tests passed!"
elif [ "$1" == "test2" ]; then
    # source /app/env.sh
    source /entry.sh
    echo "Testing default enviornment variables..."
    test_env_vars expected_env_vars
else
    echo "Invalid argument. Use either 'test1' or 'test2'."
    exit 1
fi
