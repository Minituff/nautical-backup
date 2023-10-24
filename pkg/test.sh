#!/bin/bash

bash /entry.sh

echo "Running tests..."

test_cron() {
    # Expected output
    EXPECTED_OUTPUT="$CRON_SCHEDULE bash /app/backup.sh"

    # Run the command and capture its output
    ACTUAL_OUTPUT=$(crontab -l | grep bash)

    # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "Test Passed: Output matches expected output."
    else
        echo "Test Failed: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi
}



test_bash() {
    EXPECTED_OUTPUT="/bin/bash"
    ACTUAL_OUTPUT=$(which bash)

        # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "Test Passed: Output matches expected output."
    else
        echo "Test Failed: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi
}

test_rsync() {
    EXPECTED_OUTPUT="/usr/bin/rsync"
    ACTUAL_OUTPUT=$(which rsync)

        # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "Test Passed: Rsync is installed"
    else
        echo "Test Failed: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi
}

test_jq(){
    EXPECTED_OUTPUT="/usr/bin/jq"
    ACTUAL_OUTPUT=$(which jq)

        # Compare the actual output to the expected output
    if [ "$ACTUAL_OUTPUT" == "$EXPECTED_OUTPUT" ]; then
        echo "Test Passed: QJ is installed"
    else
        echo "Test Failed: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi
}

test_cron
exit 1 # This should fail
test_bash
test_rsync
test_jq
echo "All tests passed!"