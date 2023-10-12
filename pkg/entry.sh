#!/bin/bash

# Echo the CRON schedule for logging/debugging
echo "Installing CRON schedule: $CRON_SCHEDULE in TZ: $TZ"

# Dump the current cron jobs to a temporary file
crontab -l > tempcron

# Remove the existing cron job for your backup script from the file
sed -i '/\/app\/backup.sh/d' tempcron

# Add the new cron job to the file
echo "$CRON_SCHEDULE bash /app/backup.sh" >> tempcron

# Install the new cron jobs
crontab tempcron
rm tempcron

# Variables
export SOURCE_LOCATION=/app/source # Do not include a trailing slash
export DEST_LOCATION=/app/destination  # Do not include a trailing slash


echo "Verifying source directory..." 
if [ ! -d "$SOURCE_LOCATION" ]; then
    echo "Error: Source directory $SOURCE_LOCATION does not exist."
    exit 1
elif [ ! -r "$SOURCE_LOCATION" ]; then
    echo "Error: No read access to source directory $SOURCE_LOCATION."
    exit 1
fi

echo "Verifying destination directory..." 
if [ ! -d "$DEST_LOCATION" ]; then
    echo "Error: Destination directory $DEST_LOCATION does not exist."
    exit 1
elif [ ! -r "$DEST_LOCATION" ]; then
    echo "Error: No read access to destination directory $DEST_LOCATION."
    exit 1
elif [ ! -w "$DEST_LOCATION" ]; then
    echo "Error: No write access to destination directory $DEST_LOCATION."
    exit 1
fi

CONTAINER_SKIP_LIST=()  # Containers to skips

# Function to populate the skip list array
process_csv() {
    local -n skip_list_ref=$1  # Use nameref to update the array passed as argument
    local skip_var=$2           # The environment variable containing the skip list

    if [ ! -z "$skip_var" ]; then
        # Remove quotes and leading/trailing whitespaces
        local cleaned_skip_var=$(echo "$skip_var" | sed "s/'//g;s/\"//g" | tr -d ' ')
        
        # Split by commas into an array
        IFS=',' read -ra ADDITIONAL_SKIPS <<< "$cleaned_skip_var"

        # Add to the existing skip list
        skip_list_ref=("${skip_list_ref[@]}" "${ADDITIONAL_SKIPS[@]}")
    fi
}

# Declare the CONTAINER_SKIP_LIST array
CONTAINER_SKIP_LIST=()
SKIP_STOPPING_LIST=()

# Populate the skip list
process_csv CONTAINER_SKIP_LIST "$SKIP_CONTAINERS"
process_csv SKIP_STOPPING_LIST "$SKIP_STOPPING"


if [ ! -z "$SKIP_CONTAINERS" ]; then
    echo "SKIP_CONTAINERS: ${CONTAINER_SKIP_LIST[@]}"
fi

if [ ! -z "$SKIP_STOPPING" ]; then
    echo "SKIP_STOPPING: ${SKIP_STOPPING_LIST[@]}"
fi

# Get the container ID of the current container
export SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)
# Add the self container ID to the default skips
CONTAINER_SKIP_LIST+=("$SELF_CONTAINER_ID")

CONTAINER_SKIP_LIST_STR=$(IFS=,; echo "${CONTAINER_SKIP_LIST[*]}") # Convert the array to a string
export CONTAINER_SKIP_LIST_STR # Export the string

SKIP_STOPPING_STR=$(IFS=,; echo "${SKIP_STOPPING[*]}") # Convert the array to a string
export SKIP_STOPPING_STR # Export the string

# Assuming OVERRIDE_SOURCE_DIR is passed as an environment variable in the format "container1:dir1,container2:dir2,..."
if [ ! -z "$OVERRIDE_SOURCE_DIR" ]; then
    echo "OVERRIDE_SOURCE_DIR: ${OVERRIDE_SOURCE_DIR}"
fi
export OVERRIDE_SOURCE_DIR

# Assuming OVERRIDE_DEST_DIR is passed as an environment variable in the format "container1:dir1,container2:dir2,..."
if [ ! -z "$OVERRIDE_DEST_DIR" ]; then
    echo "OVERRIDE_DEST_DIR: ${OVERRIDE_DEST_DIR}"
fi
export OVERRIDE_DEST_DIR

if [ "$REPORT_FILE" = "false" ]; then
    echo "REPORT_FILE: $REPORT_FILE"
fi

# Set rsync custom arguments if specified
if [ ! -z "$RSYNC_CUSTOM_ARGS" ]; then
    echo "RSYNC_CUSTOM_ARGS: $RSYNC_CUSTOM_ARGS"
fi

if [ "$LOG_RSYNC_COMMANDS" = "true" ]; then
    echo "LOG_RSYNC_COMMANDS: $LOG_RSYNC_COMMANDS"
fi

if [ "$USE_DEFAULT_RSYNC_ARGS" = "false" ]; then
    echo "USE_DEFAULT_RSYNC_ARGS: $USE_DEFAULT_RSYNC_ARGS"
fi


if [ "$BACKUP_ON_START" = "true" ]; then
    echo "BACKUP_ON_START: $BACKUP_ON_START"
    bash ./app/backup.sh
fi

echo "Initialization complete. Awaiting CRON schedule: $CRON_SCHEDULE"



# Start cron and keep container running
/usr/sbin/crond -f -l 8
