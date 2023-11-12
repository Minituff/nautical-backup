#!/usr/bin/with-contenv bash
# shellcheck shell=bash

# This should only be used for Unit tests
if [ "$TEST_MODE" == "true" ]; then
    echo "--- RUNNING IN TEST MODE ---"
    cd /tests # The .simplecov must be detected in the directory from where the bashcov command is run from
    rf -rf coverage # Remove the coverage (if it exists)
    with-contenv bashcov /tests/tests.sh
    echo "Shutting down since tests completed..."
    halt
    # s6-linux-init-shutdown now 
    # echo "$e" > /run/s6-linux-init-container-results/exitcode
else
    if [ "$LOG_LEVEL" == "TRACE" ]; then
         echo "TRACE - TEST_MODE: FALSE"
    fi
fi
