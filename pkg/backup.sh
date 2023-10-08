#!/bin/bash

echo "Starting backup script..."

# Variables
source_location=/app/source # Do not include a trailing slash
dest_location=/app/destination  # Do not include a trailing slash

default_skips=("nautical-backup" "container2" "default_container3")  # Containers to skips

echo "Container backup starting..."

# Get the container ID of the current container
SELF_CONTAINER_ID=$(cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1)

containers=$(docker ps --format="{{.Names}}")  # Only get docker container names

# Define the name for the report file
report_file="Backup Report - $(date +'%Y-%m-%d').txt"

# Remove previous report files
rm -f "$dest_location/Backup Report - "*.txt

# Initialize the current report file with a header
echo "Backup Report - $(date)" > "$dest_location/$report_file"

# Get arguments:
# -s = skips
# -d = override dest_location
while getopts ":s:d:" opt; do
    case $opt in
    s) currs+=("$OPTARG") ;;
    d) dest_location=$OPTARG ;;
    esac
done

# Merge the default skips with provided skips
currs=("${currs[@]}" "${default_skips[@]}")
containers_completed=0

# Assumes the container name is the exact same as the directory name
log_entry() {
    local message="$1"
    echo "$message"
    echo "$(date) - $message" >> "$dest_location/$report_file"
}

StopContainers() {
    local container=$1

    if [ -d "$source_location/$container" ]; then
        log_entry "Directory $source_location/$container exists."

        log_entry "Stopping $container..."
        docker stop $container
        if [ $? -ne 0 ]; then
            log_entry "Error stopping container $container. Skipping backup for this container."
            return
        else
            log_entry "Container $container stopped."
        fi

        log_entry "Copying $source_location/$container to $dest_location/$container..."
        rsync -ah --info=progress2 --exclude '*.log' $source_location/$container/ $dest_location/$container/

        if [ $? -ne 0 ]; then
            log_entry "Error copying data for container $container. Skipping backup for this container."
            
            # Consider restarting the container immediately if the copy operation fails
            docker start $container
            if [ $? -ne 0 ]; then
                log_entry "Error restarting container $container. Please check manually!"
            else
                log_entry "Container $container restarted."
            fi

            return
        else
            log_entry "Copied $source_location/$container to $dest_location/$container."
        fi

        
        log_entry "Starting $container..."
        docker start $container
        if [ $? -ne 0 ]; then
            log_entry "Error restarting container $container. Please check manually!"
            return
        else
            log_entry "Container $container restarted."
        fi

        log_entry "$container completed."
        ((containers_completed++))
    else
        log_entry "Directory $source_location/$container does not exist. Skipping"
    fi
}



echo "Verifying source directory $source_location exists..." 
if [ -d "$source_location" ]; then
    echo "Destination directory $source_location exists." 
else
    echo "Error: Source directory $source_location does not exist."
    exit 1
fi

echo "Verifying destination directory $dest_location exists..." 
if [ -d "$dest_location" ]; then
    echo "Destination directory $dest_location exists." 
else
    echo "Error: Destination directory $dest_location does not exist."
    exit 1
fi

shift $((OPTIND - 1))
for container in $containers; do
    skip=0
    for cur in "${currs[@]}"; do
        if [ "$cur" == "$container" ]; then
            skip=1
        fi
    done
    if [ $skip -eq 0 ]; then
        StopContainers "$container"
    else
        echo "Skipping $container."
    fi
done

echo "Success. $containers_completed containers backed up!"