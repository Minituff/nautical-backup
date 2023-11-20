#!/usr/bin/with-contenv bash

# Change this as alpine updates
ALPINE_VERSION="3.18"

test_docker() {
    EXPECTED_OUTPUT="/usr/local/bin/docker"
    ACTUAL_OUTPUT=$(which docker)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which docker' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'docker --version' to check if it returns something
    if [[ $(docker --version) ]]; then
        echo "PASS: 'docker --version' returns a value."
    else
        echo "FAIL: 'docker --version' did not return a value."
        exit 1
    fi

    # Use 'docker ps' to check if it returns something
    if [[ $(docker ps) ]]; then
        echo "PASS: 'docker ps' returns a value."
    else
        echo "FAIL: 'docker ps' did not return a value."
        exit 1
    fi
}

test_cron() {
    # Expected output
    EXPECTED_OUTPUT="$CRON_SCHEDULE with-contenv bash nautical"

    # Run the command and capture its output
    ACTUAL_OUTPUT=$(crontab -l | grep bash)

    if [ "$ACTUAL_OUTPUT" != "$EXPECTED_OUTPUT" ]; then
        echo "FAIL: CRON output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" != "$EXPECTED_OUTPUT" ]; then
        echo "FAIL: CRON output does not match expected output."
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
        echo "FAIL: Bash does not match expected output."
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
        echo "FAIL: Rsync does not match expected output."
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
        echo "FAIL: Jq does not match expected output."
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
        echo "FAIL: Curl does not match expected output."
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
        echo "FAIL: Timeout does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'timeout 5s echo "hello"' to check if it returns something
    if [[ $(timeout 5s echo "hello") ]]; then
        echo "PASS: 'timeout 5s echo "hello"' returns a value."
    else
        echo "FAIL: 'timeout 5s echo "hello"' did not return a value."
        exit 1
    fi
}

test_tz() {
    EXPECTED_OUTPUT="America/Phoenix"
    ACTUAL_OUTPUT=$(echo $TZ)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'echo \$TZ' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: TimzeZone does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    ACTUAL_OUTPUT=$(date | grep MST)
    # Use 'date | grep MST' to check if it returns something
    if [[ $ACTUAL_OUTPUT ]]; then
        echo "PASS: 'date | grep MST' returns the correct TZ."
    else
        echo "FAIL: 'date | grep MST' did notthe correct TZ."
        echo "Got: $date"
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

test_python() {
    EXPECTED_OUTPUT="/usr/bin/python3"
    ACTUAL_OUTPUT=$(which python3)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "PASS: 'which python' returns $EXPECTED_OUTPUT"
    else
        echo "FAIL: Python does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi

    # Use 'python --version' to check if it returns something
    if [[ $(python3 --version) ]]; then
        echo "PASS: 'python3 --version' returns a value."
    else
        echo "FAIL: 'python3 --version' did not return a value."
        exit 1
    fi
}


test_self_container_id() {
    if [[ $(echo $SELF_CONTAINER_ID) ]]; then
        echo "PASS: 'SELF_CONTAINER_ID' returns a value."
    else
        echo "FAIL: 'SELF_CONTAINER_ID' did not return a value."
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
    ["TEST_MODE"]="2" # This not actually the default, but the mode that checks this value is #2
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
    ["HTTP_REST_API_ENABLED"]="false"
    ["HTTP_REST_API_USERNAME"]="admin"
    ["HTTP_REST_API_PASSWORD"]="password"
    
)

if [ "$1" == "test1" ]; then
    bash /app/entry.sh

    echo "Running integation tests..."

    test_docker
    test_cron
    test_tz
    test_bash
    test_rsync
    test_jq
    test_curl
    test_timeout
    test_alpine_release
    test_python
    test_self_container_id

    echo "All tests passed!"
elif [ "$1" == "test2" ]; then
    source /app/env.sh
    source /app/entry.sh
    echo "Testing default enviornment variables..."
    test_env_vars expected_env_vars
else
    echo "Invalid argument. Use either 'test1' or 'test2'."
    exit 1
fi
