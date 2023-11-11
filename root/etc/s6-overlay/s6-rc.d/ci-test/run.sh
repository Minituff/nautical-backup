#!/usr/bin/with-contenv bash
# shellcheck shell=bash

# This should only be used for Unit tests
if [ "$TEST_MODE" == "true" ]; then
    echo "--- RUNNING IN TEST MODE ---"
    with-contenv bash /tests/tests.sh
    s6-linux-init-shutdown now "Shutting down since tests completed..."
fi
