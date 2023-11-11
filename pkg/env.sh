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

DEFAULT_HTTP_REST_API_ENABLED="true"
DEFAULT_HTTP_REST_API_USERNAME="admin"
DEFAULT_HTTP_REST_API_PASSWORD="password"

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

# Path to the Nautical database.
DEFAULT_NAUTICAL_DB_PATH="/config"
: "${NAUTICAL_DB_PATH:=$DEFAULT_NAUTICAL_DB_PATH}"
handle_env NAUTICAL_DB_PATH "$NAUTICAL_DB_PATH"

DEFAULT_NAUTICAL_DB_NAME="nautical-db.json"
: "${NAUTICAL_DB_NAME:=$DEFAULT_NAUTICAL_DB_NAME}"
handle_env NAUTICAL_DB_NAME "$NAUTICAL_DB_NAME"

if [ -z "$HTTP_REST_API_ENABLED" ]; then
    HTTP_REST_API_ENABLED=$DEFAULT_HTTP_REST_API_ENABLED
fi
handle_env HTTP_REST_API_ENABLED "$HTTP_REST_API_ENABLED"


if [ -z "$TEST_MODE" ]; then
    TEST_MODE=$DEFAULT_TEST_MODE
fi
handle_env TEST_MODE "$TEST_MODE"

if [ -z "$TZ" ]; then
    TZ=$DEFAULT_TZ
fi
handle_env TZ "$TZ"

if [ -z "$CRON_SCHEDULE" ]; then
    CRON_SCHEDULE=$DEFAULT_CRON_SCHEDULE
fi
handle_env CRON_SCHEDULE "$CRON_SCHEDULE"

if [ -z "$REPORT_FILE" ]; then
    REPORT_FILE=$DEFAULT_REPORT_FILE
fi
handle_env REPORT_FILE "$REPORT_FILE"

if [ -z "$BACKUP_ON_START" ]; then
    BACKUP_ON_START=$DEFAULT_BACKUP_ON_START
fi
handle_env BACKUP_ON_START "$BACKUP_ON_START"

if [ -z "$USE_DEFAULT_RSYNC_ARGS" ]; then
    USE_DEFAULT_RSYNC_ARGS=$DEFAULT_USE_DEFAULT_RSYNC_ARGS
fi
handle_env USE_DEFAULT_RSYNC_ARGS "$USE_DEFAULT_RSYNC_ARGS"

if [ -z "$HTTP_REST_API_USERNAME" ]; then
    HTTP_REST_API_USERNAME=$DEFAULT_HTTP_REST_API_USERNAME
fi
handle_env HTTP_REST_API_USERNAME "$HTTP_REST_API_USERNAME"

if [ -z "$HTTP_REST_API_PASSWORD" ]; then
    HTTP_REST_API_PASSWORD=$DEFAULT_HTTP_REST_API_PASSWORD
fi
logThis "HTTP_REST_API_PASSWORD: *******" "DEBUG" "init"
export_env HTTP_REST_API_PASSWORD "$HTTP_REST_API_PASSWORD"

if [ -z "$REQUIRE_LABEL" ]; then
    REQUIRE_LABEL=$DEFAULT_REQUIRE_LABEL
fi
handle_env REQUIRE_LABEL "$REQUIRE_LABEL"

if [ -z "$LOG_LEVEL" ]; then
    LOG_LEVEL=$DEFAULT_LOG_LEVEL
fi
handle_env LOG_LEVEL "$LOG_LEVEL"

if [ -z "$REPORT_FILE_LOG_LEVEL" ]; then
    REPORT_FILE_LOG_LEVEL=$DEFAULT_REPORT_FILE_LOG_LEVEL
fi
handle_env REPORT_FILE_LOG_LEVEL "$REPORT_FILE_LOG_LEVEL"

if [ -z "$REPORT_FILE_ON_BACKUP_ONLY" ]; then
    REPORT_FILE_ON_BACKUP_ONLY=$DEFAULT_REPORT_FILE_ON_BACKUP_ONLY
fi
handle_env REPORT_FILE_ON_BACKUP_ONLY "$REPORT_FILE_ON_BACKUP_ONLY"

if [ -z "$KEEP_SRC_DIR_NAME" ]; then
    KEEP_SRC_DIR_NAME=$DEFAULT_KEEP_SRC_DIR_NAME
fi
handle_env KEEP_SRC_DIR_NAME "$KEEP_SRC_DIR_NAME"

if [ -z "$EXIT_AFTER_INIT" ]; then
    EXIT_AFTER_INIT=$DEFAULT_EXIT_AFTER_INIT
fi
handle_env EXIT_AFTER_INIT "$EXIT_AFTER_INIT"

if [ -z "$LOG_RSYNC_COMMANDS" ]; then
    LOG_RSYNC_COMMANDS=$DEFAULT_LOG_RSYNC_COMMANDS
fi
handle_env LOG_RSYNC_COMMANDS "$LOG_RSYNC_COMMANDS"

if [ -z "$RUN_ONCE" ]; then
    RUN_ONCE=$DEFAULT_RUN_ONCE
fi
handle_env RUN_ONCE "$RUN_ONCE"

if [ -z "$ADDITIONAL_FOLDERS_WHEN" ]; then
    ADDITIONAL_FOLDERS_WHEN=$DEFAULT_ADDITIONAL_FOLDERS_WHEN
fi
handle_env ADDITIONAL_FOLDERS_WHEN "$ADDITIONAL_FOLDERS_WHEN"

if [ -z "$PRE_BACKUP_CURL" ]; then
    PRE_BACKUP_CURL=$DEFAULT_PRE_BACKUP_CURL
fi
handle_env PRE_BACKUP_CURL "$PRE_BACKUP_CURL"

if [ -z "$POST_BACKUP_CURL" ]; then
    POST_BACKUP_CURL=$DEFAULT_POST_BACKUP_CURL
fi
handle_env POST_BACKUP_CURL "$POST_BACKUP_CURL"

# ------ Default Empty Values ------ #

if [ -z "$ADDITIONAL_FOLDERS" ]; then
    ADDITIONAL_FOLDERS=$DEFAULT_ADDITIONAL_FOLDERS
fi
handle_env ADDITIONAL_FOLDERS "$ADDITIONAL_FOLDERS"

if [ -z "$SKIP_CONTAINERS" ]; then
    SKIP_CONTAINERS=$DEFAULT_SKIP_CONTAINERS
fi
handle_env SKIP_CONTAINERS "$SKIP_CONTAINERS"

if [ -z "$SKIP_STOPPING" ]; then
    SKIP_STOPPING=$DEFAULT_SKIP_STOPPING
fi
handle_env SKIP_STOPPING "$SKIP_STOPPING"

if [ -z "$RSYNC_CUSTOM_ARGS" ]; then
    RSYNC_CUSTOM_ARGS=$DEFAULT_RSYNC_CUSTOM_ARGS
fi
handle_env RSYNC_CUSTOM_ARGS "$RSYNC_CUSTOM_ARGS"

if [ -z "$OVERRIDE_SOURCE_DIR" ]; then
    OVERRIDE_SOURCE_DIR=$DEFAULT_OVERRIDE_SOURCE_DIR
fi
handle_env OVERRIDE_SOURCE_DIR "$OVERRIDE_SOURCE_DIR"

if [ -z "$OVERRIDE_DEST_DIR" ]; then
    OVERRIDE_DEST_DIR=$DEFAULT_OVERRIDE_DEST_DIR
fi
handle_env OVERRIDE_DEST_DIR "$OVERRIDE_DEST_DIR"

# ----- Variables Requiring Logic ----- #

if [ "$TEST_MODE" == "true" ]; then
    SOURCE_LOCATION=$DEFAULT_TEST_SOURCE_LOCATION
    DEST_LOCATION=$DEFAULT_TEST_DEST_LOCATION
else
    SOURCE_LOCATION=$DEFAULT_SOURCE_LOCATION
    DEST_LOCATION=$DEFAULT_DEST_LOCATION
fi
handle_env SOURCE_LOCATION "$SOURCE_LOCATION"
handle_env DEST_LOCATION "$DEST_LOCATION"


# Declare the CONTAINER_SKIP_LIST array
# CONTAINER_SKIP_LIST=()


echo "1 SKIP_CONTAINERS (env) $SKIP_CONTAINERS"
# Populate the skip list
# process_csv CONTAINER_SKIP_LIST "$SKIP_CONTAINERS"
# echo "2 CONTAINER_SKIP_LIST (env) $CONTAINER_SKIP_LIST"

# Get the container ID of the current container
# SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)
# handle_env SELF_CONTAINER_ID "$SELF_CONTAINER_ID"
# CONTAINER_SKIP_LIST_STR="$SKIP_CONTAINERS,$SELF_CONTAINER_ID"

handle_env CONTAINER_SKIP_LIST_STR "$SKIP_CONTAINERS"
echo "2 CONTAINER_SKIP_LIST_STR $CONTAINER_SKIP_LIST_STR"



process_csv SKIP_STOPPING_LIST "$SKIP_STOPPING"

SKIP_STOPPING_LIST=()
# Convert the array to a string
SKIP_STOPPING_STR=$(
    IFS=,
    echo "${SKIP_STOPPING[*]}"
)                        
handle_env CONTAINER_SKIP_LIST_STR "$CONTAINER_SKIP_LIST_STR"

ADDITIONAL_FOLDERS_LIST=()
process_csv ADDITIONAL_FOLDERS_LIST "$ADDITIONAL_FOLDERS"
# Convert the array to a string
ADDITIONAL_FOLDERS_LIST_STR=$(
    IFS=,
    echo "${ADDITIONAL_FOLDERS_LIST[*]}"
)
handle_env ADDITIONAL_FOLDERS_LIST_STR  "$ADDITIONAL_FOLDERS_LIST_STR" # Export the string


set -a