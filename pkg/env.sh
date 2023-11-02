#!/usr/bin/env bash

if [ -z "$TEST_MODE" ]; then
    TEST_MODE="false"
fi
export TEST_MODE

if [ "$TEST_MODE" == "true" ]; then
    source pkg/logger.sh # Use the logger script
    source pkg/utils.sh

    NAUTICAL_VERSION=Test
    TARGETPLATFORM=TestPlatform
fi

create_new_report_file

logThis "Nautical Backup Version: $NAUTICAL_VERSION" "INFO" "init"
logThis "Built for the platform: $TARGETPLATFORM" "DEBUG" "init"

# ------ Default Variable Values ------ #

# Set default timezone
DEFAULT_TZ=Etc/UTC

# Default = Every day at 4am
DEFAULT_CRON_SCHEDULE="0 4 * * *"

# Default enable the report file
DEFAULT_REPORT_FILE="true"

# Run the backup immediately on start
DEFAULT_BACKUP_ON_START="false"

# Use the default rsync args "-ahq" (archive, human-readable, quiet)
DEFAULT_USE_DEFAULT_RSYNC_ARGS="true"

# Require the Docker Label `nautical-backup.enable=true` to be present on each contianer or it will be skipped.
DEFAULT_REQUIRE_LABEL="false"

# Set the default log level to INFO
DEFAULT_LOG_LEVEL="INFO"

# Set the default log level for the repot file to INFO
DEFAULT_REPORT_FILE_LOG_LEVEL="INFO"

# Only write to the report file when backups run, not on initialization
DEFAULT_REPORT_FILE_ON_BACKUP_ONLY="true"

# Mirrior the source directory name to the destination directory name
# When true, and an source dir override is applied, then the destination directory will be same same as the new source directory
DEFAULT_KEEP_SRC_DIR_NAME="true"

# Usually combined with BACKUP_ON_START. Essentially, this just exists the container after 1 run.
DEFAULT_EXIT_AFTER_INIT="false"

# Log the rsync commands to the console (and/or report file)
DEFAULT_LOG_RSYNC_COMMANDS="false"

# Run the backup only once and then exit (whether it is from CRON or BACKUP_ON_START)
DEFAULT_RUN_ONCE="false"

# Do not include a trailing slash
DEFAULT_SOURCE_LOCATION="/app/source"    
DEFAULT_DEST_LOCATION="/app/destination"
# Test directories
DEFAULT_TEST_SOURCE_LOCATION="tests/src"
DEFAULT_TEST_DEST_LOCATION="tests/dest"

DEFAULT_TEST_MODE="false"

# Run a curl request before the backup starts
DEFAULT_PRE_BACKUP_CURL=""
DEFAULT_POST_BACKUP_CURL=""

# ------ Default Empty Values------ #

DEFAULT_SKIP_CONTAINERS=""

DEFAULT_SKIP_STOPPING=""

# Apply custom rsync args (in addition to the default args)
DEFAULT_RSYNC_CUSTOM_ARGS=""

# Assuming OVERRIDE_SOURCE_DIR is passed as an environment variable in the format "container1:dir1,container2:dir2,..."
DEFAULT_OVERRIDE_SOURCE_DIR=""

# Assuming OVERRIDE_DEST_DIR is passed as an environment variable in the format "container1:dir1,container2:dir2,..."
DEFAULT_OVERRIDE_DEST_DIR=""

# Directores to be backed up that are not associated with a container
DEFAULT_ADDITIONAL_FOLDERS=""

# When do backup the additional folders? "before", "after", or "both" the container backups
DEFAULT_ADDITIONAL_FOLDERS_WHEN="before"

logThis "Perparing enviornment variables..." "DEBUG" "init"

if [ -z "$TEST_MODE" ]; then
    TEST_MODE=$DEFAULT_TEST_MODE
fi
logThis "TEST_MODE: $TEST_MODE" "DEBUG" "init"
export TEST_MODE

if [ -z "$TZ" ]; then
    TZ=$DEFAULT_TZ
fi
logThis "TZ: $TZ" "DEBUG" "init"
export TZ

if [ -z "$CRON_SCHEDULE" ]; then
    CRON_SCHEDULE=$DEFAULT_CRON_SCHEDULE
fi
logThis "CRON_SCHEDULE: $CRON_SCHEDULE" "DEBUG" "init"
export CRON_SCHEDULE

if [ -z "$REPORT_FILE" ]; then
    REPORT_FILE=$DEFAULT_REPORT_FILE
fi
logThis "REPORT_FILE: $REPORT_FILE" "DEBUG" "init"
export REPORT_FILE

if [ -z "$BACKUP_ON_START" ]; then
    BACKUP_ON_START=$DEFAULT_BACKUP_ON_START
fi
logThis "BACKUP_ON_START: $BACKUP_ON_START" "DEBUG" "init"
export BACKUP_ON_START

if [ -z "$USE_DEFAULT_RSYNC_ARGS" ]; then
    USE_DEFAULT_RSYNC_ARGS=$DEFAULT_USE_DEFAULT_RSYNC_ARGS
fi
logThis "USE_DEFAULT_RSYNC_ARGS: $USE_DEFAULT_RSYNC_ARGS" "DEBUG" "init"
export USE_DEFAULT_RSYNC_ARGS

if [ -z "$REQUIRE_LABEL" ]; then
    REQUIRE_LABEL=$DEFAULT_REQUIRE_LABEL
fi
logThis "REQUIRE_LABEL: $REQUIRE_LABEL" "DEBUG" "init"
export REQUIRE_LABEL

if [ -z "$LOG_LEVEL" ]; then
    LOG_LEVEL=$DEFAULT_LOG_LEVEL
fi
logThis "LOG_LEVEL: $LOG_LEVEL" "DEBUG" "init"
export LOG_LEVEL

if [ -z "$REPORT_FILE_LOG_LEVEL" ]; then
    REPORT_FILE_LOG_LEVEL=$DEFAULT_REPORT_FILE_LOG_LEVEL
fi
logThis "REPORT_FILE_LOG_LEVEL: $REPORT_FILE_LOG_LEVEL" "DEBUG" "init"
export REPORT_FILE_LOG_LEVEL

if [ -z "$REPORT_FILE_ON_BACKUP_ONLY" ]; then
    REPORT_FILE_ON_BACKUP_ONLY=$DEFAULT_REPORT_FILE_ON_BACKUP_ONLY
fi
logThis "REPORT_FILE_ON_BACKUP_ONLY: $REPORT_FILE_ON_BACKUP_ONLY" "DEBUG" "init"
export REPORT_FILE_ON_BACKUP_ONLY

if [ -z "$KEEP_SRC_DIR_NAME" ]; then
    KEEP_SRC_DIR_NAME=$DEFAULT_KEEP_SRC_DIR_NAME
fi
logThis "KEEP_SRC_DIR_NAME: $KEEP_SRC_DIR_NAME" "DEBUG" "init"
export KEEP_SRC_DIR_NAME

if [ -z "$EXIT_AFTER_INIT" ]; then
    EXIT_AFTER_INIT=$DEFAULT_EXIT_AFTER_INIT
fi
logThis "EXIT_AFTER_INIT: $EXIT_AFTER_INIT" "DEBUG" "init"
export EXIT_AFTER_INIT

if [ -z "$LOG_RSYNC_COMMANDS" ]; then
    LOG_RSYNC_COMMANDS=$DEFAULT_LOG_RSYNC_COMMANDS
else
    logThis "LOG_RSYNC_COMMANDS: $LOG_RSYNC_COMMANDS" "DEBUG" "init"
fi
export LOG_RSYNC_COMMANDS

if [ -z "$RUN_ONCE" ]; then
    RUN_ONCE=$DEFAULT_RUN_ONCE
else
    logThis "RUN_ONCE: $RUN_ONCE" "DEBUG" "init"
fi
export RUN_ONCE

if [ -z "$ADDITIONAL_FOLDERS_WHEN" ]; then
    ADDITIONAL_FOLDERS_WHEN=$DEFAULT_ADDITIONAL_FOLDERS_WHEN
else
    logThis "ADDITIONAL_FOLDERS_WHEN: $ADDITIONAL_FOLDERS_WHEN" "DEBUG" "init"
fi
export ADDITIONAL_FOLDERS_WHEN

if [ -z "$PRE_BACKUP_CURL" ]; then
    PRE_BACKUP_CURL=$DEFAULT_PRE_BACKUP_CURL
else
    logThis "PRE_BACKUP_CURL: $PRE_BACKUP_CURL" "DEBUG" "init"
fi
export PRE_BACKUP_CURL

if [ -z "$POST_BACKUP_CURL" ]; then
    POST_BACKUP_CURL=$DEFAULT_POST_BACKUP_CURL
else
    logThis "POST_BACKUP_CURL: $POST_BACKUP_CURL" "DEBUG" "init"
fi
export POST_BACKUP_CURL

# ------ Default Empty Values ------ #

if [ -z "$ADDITIONAL_FOLDERS" ]; then
    ADDITIONAL_FOLDERS=$DEFAULT_ADDITIONAL_FOLDERS
else
    logThis "ADDITIONAL_FOLDERS: $ADDITIONAL_FOLDERS" "DEBUG" "init"
fi

if [ -z "$SKIP_CONTAINERS" ]; then
    SKIP_CONTAINERS=$DEFAULT_SKIP_CONTAINERS
else
    logThis "SKIP_CONTAINERS: ${SKIP_CONTAINERS}" "DEBUG" "init"
fi

if [ -z "$SKIP_STOPPING" ]; then
    SKIP_STOPPING=$DEFAULT_SKIP_STOPPING
else
    logThis "SKIP_STOPPING: ${SKIP_STOPPING}" "DEBUG" "init"
fi

if [ -z "$RSYNC_CUSTOM_ARGS" ]; then
    RSYNC_CUSTOM_ARGS=$DEFAULT_RSYNC_CUSTOM_ARGS
else
    logThis "RSYNC_CUSTOM_ARGS: $RSYNC_CUSTOM_ARGS" "DEBUG" "init"
fi
export RSYNC_CUSTOM_ARGS

if [ -z "$OVERRIDE_SOURCE_DIR" ]; then
    OVERRIDE_SOURCE_DIR=$DEFAULT_OVERRIDE_SOURCE_DIR
else
    logThis "OVERRIDE_SOURCE_DIR: $OVERRIDE_SOURCE_DIR" "DEBUG" "init"
fi
export OVERRIDE_SOURCE_DIR

if [ -z "$OVERRIDE_DEST_DIR" ]; then
    OVERRIDE_DEST_DIR=$DEFAULT_OVERRIDE_DEST_DIR
else
    logThis "OVERRIDE_DEST_DIR: $OVERRIDE_DEST_DIR" "DEBUG" "init"

fi
export OVERRIDE_DEST_DIR

# ----- Variables Requiring Logic ----- #

if [ "$TEST_MODE" == "true" ]; then
    SOURCE_LOCATION=$DEFAULT_TEST_SOURCE_LOCATION
    DEST_LOCATION=$DEFAULT_TEST_DEST_LOCATION
else
    SOURCE_LOCATION=$DEFAULT_SOURCE_LOCATION
    DEST_LOCATION=$DEFAULT_DEST_LOCATION
fi
export SOURCE_LOCATION
export DEST_LOCATION

# Declare the CONTAINER_SKIP_LIST array
CONTAINER_SKIP_LIST=()
SKIP_STOPPING_LIST=()

# Populate the skip list
process_csv CONTAINER_SKIP_LIST "$SKIP_CONTAINERS"
process_csv SKIP_STOPPING_LIST "$SKIP_STOPPING"

# Get the container ID of the current container
export SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)
# Add the self container ID to the default skips
CONTAINER_SKIP_LIST+=("$SELF_CONTAINER_ID")

# Convert the array to a string
CONTAINER_SKIP_LIST_STR=$(
    IFS=,
    echo "${CONTAINER_SKIP_LIST[*]}"
)
export CONTAINER_SKIP_LIST_STR # Export the string

# Convert the array to a string
SKIP_STOPPING_STR=$(
    IFS=,
    echo "${SKIP_STOPPING[*]}"
)                        
export SKIP_STOPPING_STR # Export the string

ADDITIONAL_FOLDERS_LIST=()
process_csv ADDITIONAL_FOLDERS_LIST "$ADDITIONAL_FOLDERS"
# Convert the array to a string
ADDITIONAL_FOLDERS_LIST_STR=$(
    IFS=,
    echo "${ADDITIONAL_FOLDERS_LIST[*]}"
)
export ADDITIONAL_FOLDERS_LIST_STR # Export the string