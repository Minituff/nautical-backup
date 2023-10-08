#!/bin/bash

# Echo the CRON schedule for logging/debugging
echo "Installing CRON schedule: $CRON_SCHEDULE"

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

# Add any container names specified in the SKIP_CONTAINERS environment variable to the skip list
if [ ! -z "$SKIP_CONTAINERS" ]; then
    # Remove quotes and leading/trailing whitespaces
    cleaned_skip_containers=$(echo "$SKIP_CONTAINERS" | sed "s/'//g;s/\"//g" | tr -d ' ')
    
    # Split by commas into an array
    IFS=',' read -ra ADDITIONAL_SKIPS <<< "$cleaned_skip_containers"

    # Add to the default skips
    CONTAINER_SKIP_LIST=("${CONTAINER_SKIP_LIST[@]}" "${ADDITIONAL_SKIPS[@]}")
fi

if [ ! -z "$SKIP_CONTAINERS" ]; then
    echo "SKIP_CONTAINERS: ${CONTAINER_SKIP_LIST[@]}"
fi

# Get the container ID of the current container
export SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)
# Add the self container ID to the default skips
CONTAINER_SKIP_LIST+=("$SELF_CONTAINER_ID")


CONTAINER_SKIP_LIST_STR=$(IFS=,; echo "${CONTAINER_SKIP_LIST[*]}") # Convert the array to a string
export CONTAINER_SKIP_LIST_STR # Export the string


echo "Initialization complete. Awaiting CRON schedule: $CRON_SCHEDULE"



# Start cron and keep container running
/usr/sbin/crond -f -l 8
