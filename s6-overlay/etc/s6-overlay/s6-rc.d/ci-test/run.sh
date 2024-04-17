#!/usr/bin/with-contenv bash
# shellcheck shell=bash

# This should only be used for Unit tests
if [ "$TEST_MODE" != "-1" ]; then
    echo "--- RUNNING IN TEST MODE ("$TEST_MODE") ---"
    
    # Set exit code to 0, will be overwritten for each test. Tests are only run 1 at at time
    exit_code=0

    # Run the tests and capture their exit code
    if [ "$TEST_MODE" == "1" ]; then
        with-contenv bash /tests/_integration_tests.sh test1
        exit_code=$?
    elif [ "$TEST_MODE" == "2" ]; then
        with-contenv bash /tests/_integration_tests.sh test2
        exit_code=$?
    elif [ "$TEST_MODE" == "3" ]; then
        with-contenv bash /tests/_integration_tests.sh test3
        exit_code=$?

        bash /tests/_fix_coverage_paths.sh
    elif [ "$TEST_MODE" == "4" ]; then
        cd /tests       # The .simplecov must be detected in the directory from where the bashcov command is run from
        rm -rf /coverage/* # Remove the coverage (if it exists)
        # with-contenv bashcov /tests/_tests.sh
        # TODO: Add python integration tests
        exit_code=$?
    else
        echo "UNKNOWN TEST MODE: ${TEST_MODE}"
    fi

    # Tell S6 which exit code to use when the container exits
    echo "$exit_code" >/run/s6-linux-init-container-results/exitcode

    echo "Shutting down container since tests completed. EXIT CODE: ${exit_code}"

    kill -SIGTERM 1  # Quit the container

else
    if [ "$LOG_LEVEL" == "TRACE" ]; then
        echo "TRACE: TEST_MODE: ${TEST_MODE}"
    fi
fi
