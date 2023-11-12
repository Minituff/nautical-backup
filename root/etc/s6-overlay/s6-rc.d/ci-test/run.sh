#!/usr/bin/with-contenv bash
# shellcheck shell=bash

# This should only be used for Unit tests
if [ "$TEST_MODE" == "true" ]; then
    echo "--- RUNNING IN TEST MODE ---"
    cd /tests # The .simplecov must be detected in the directory from where the bashcov command is run from
    rm -rf coverage # Remove the coverage (if it exists)

    # Run the tests and capture their exit code
    with-contenv bashcov /tests/tests.sh
    exit_code=$?
    echo "$exit_code" > /run/s6-linux-init-container-results/exitcode
    echo "EXIT CODE: ${exit_code}"
    
    echo "Shutting down since tests completed..."

    halt
else
    if [ "$LOG_LEVEL" == "TRACE" ]; then
         echo "TRACE - TEST_MODE: FALSE"
    fi
fi
