#!/bin/bash

EXIT_AFTER_INIT="true"
BACKUP_ON_START="false"
LOG_LEVEL="DEBUG"
CRON_SCHEDULE="0 8 * * *"

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
        exit 0
    else
        echo "Test Failed: Output does not match expected output."
        echo "Expected: $EXPECTED_OUTPUT"
        echo "Got: $ACTUAL_OUTPUT"
        exit 1
    fi
}

test_cron