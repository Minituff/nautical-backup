#!/bin/bash

echo "Starting backup script..."

# Convert the string back to an array
if [ ! -z "$CONTAINER_SKIP_LIST_STR" ]; then
    IFS=',' read -ra SKIP_CONTAINERS <<<"$CONTAINER_SKIP_LIST_STR"
fi

# Convert the string back to an array
if [ ! -z "$SKIP_STOPPING_STR" ]; then
    IFS=',' read -ra SKIP_STOPPING <<<"$SKIP_STOPPING_STR"
fi

# Function to populate override directories
populate_override_dirs() {
    local -n override_dirs_ref=$1 # Use nameref to update the associative array passed as argument
    local override_var=$2         # The environment variable containing the override info

    if [ ! -z "$override_var" ]; then
        IFS=',' read -ra PAIRS <<<"$override_var"
        for pair in "${PAIRS[@]}"; do
            IFS=':' read -ra KV <<<"$pair"
            override_dirs_ref[${KV[0]}]=${KV[1]}
        done
    fi
}

# Declare associative arrays for source and destination overrides
declare -A override_source_dirs
declare -A override_dest_dirs

# Populate the arrays
populate_override_dirs override_source_dirs "$OVERRIDE_SOURCE_DIR"
populate_override_dirs override_dest_dirs "$OVERRIDE_DEST_DIR"

# Fetch both container names and IDs
containers=$(docker ps --no-trunc --format="{{.ID}}:{{.Names}}")
number_of_containers=$(echo "$containers" | wc -l)
number_of_containers=$((number_of_containers - 1)) # Subtract 1 to exclude the container running the script

echo "Processing $number_of_containers containers..."

# Define the name for the report file
report_file="Backup Report - $(date +'%Y-%m-%d').txt"

# Remove previous report files

# Initialize the current report file with a header
if [ "$REPORT_FILE" = "true" ]; then
    rm -f "$DEST_LOCATION/Backup Report - "*.txt
    # Initialize the current report file with a header
    echo "Backup Report - $(date)" >"$DEST_LOCATION/$report_file"
fi

default_rsync_args="-ahq"
if [ "$USE_DEFAULT_RSYNC_ARGS" = "false" ]; then
    default_rsync_args=""
fi

# Global variables to hold rsync arguments
custom_args=""
if [ ! -z "$RSYNC_CUSTOM_ARGS" ]; then
    custom_args="$RSYNC_CUSTOM_ARGS"
fi

# Get arguments:
# -s = skips
# -d = override DEST_LOCATION
while getopts ":s:d:" opt; do
    case $opt in
    s) currs+=("$OPTARG") ;;
    d) DEST_LOCATION=$OPTARG ;;
    esac
done

# Merge the default skips with provided skips
currs=("${currs[@]}" "${SKIP_CONTAINERS[@]}")
containers_completed=0

# Assumes the container name is the exact same as the directory name
log_entry() {
    local message="$1"
    echo "$message"

    if [ "$REPORT_FILE" = "true" ]; then
        echo "$(date) - $message" >>"$DEST_LOCATION/$report_file"
    fi
}

BackupContainer() {
    local container=$1

    local skip_stopping=0
    for skip in "${SKIP_STOPPING[@]}"; do
        if [ "$skip" == "$container" ]; then
            skip_stopping=1
            log_entry "Skipping stopping of $container as it's in the SKIP_STOPPING list."
            break
        fi
    done

    # Use docker inspect to get the labels for the container
    labels=$(docker inspect --format '{{json .Config.Labels}}' $id)

    # Check if the label nautical-backup.skip is set to true
    if echo "$labels" | grep -q '"nautical-backup.stop-before-backup":"false"'; then
        log_entry "Skipping stopping of $container because of label."
        skip_stopping=1
    fi

    local src_dir="$SOURCE_LOCATION/$container"
    if [ ! -z "${override_source_dirs[$container]}" ]; then
        src_dir="$SOURCE_LOCATION/${override_source_dirs[$container]}"
        log_entry "Overriding source directory for $container to ${override_source_dirs[$container]}"
    fi

    if echo "$labels" | grep -q '"nautical-backup.override-source-dir"'; then
        new_src_dir=$(echo "$labels" | jq -r '.["nautical-backup.override-source-dir"]')
        src_dir="$SOURCE_LOCATION/$new_src_dir"
        log_entry "Overriding source directory for $container to $new_src_dir from label"
    fi

    local dest_dir="$DEST_LOCATION/$container"
    if [ ! -z "${override_dest_dirs[$container]}" ]; then
        dest_dir="$DEST_LOCATION/${override_dest_dirs[$container]}"
        log_entry "Overriding destination directory for $container to ${override_dest_dirs[$container]}"
    fi

    if echo "$labels" | grep -q '"nautical-backup.override-destination-dir"'; then
        new_destination_dir=$(echo "$labels" | jq -r '.["nautical-backup.override-destination-dir"]')
        dest_dir="$DEST_LOCATION/$new_destination_dir"
        log_entry "Overriding destination directory for $container to $new_destination_dir from label"
    fi

    if [ -d "$src_dir" ]; then
        if [ $skip_stopping -eq 0 ]; then
            log_entry "Stopping $container..."
            docker stop $container 2>&1 >/dev/null
            if [ $? -ne 0 ]; then
                log_entry "Error stopping container $container. Skipping backup for this container."
                return
            fi
        fi

        log_entry "Backing up $container data..."
        if [ "$LOG_RSYNC_COMMANDS" = "true" ]; then
            echo rsync $default_rsync_args $custom_args $src_dir/ $dest_dir/
        fi
        eval rsync $default_rsync_args $custom_args $src_dir/ $dest_dir/

        if [ $? -ne 0 ]; then
            log_entry "Error copying data for container $container. Skipping backup for this container."
        fi

        if [ $skip_stopping -eq 0 ]; then
            log_entry "Starting $container container..."
            docker start $container 2>&1 >/dev/null
            if [ $? -ne 0 ]; then
                log_entry "Error restarting container $container. Please check manually!"
                return
            fi
        fi

        log_entry "$container completed."
        ((containers_completed++))
    else
        log_entry "Directory $src_dir does not exist. Skipping"
    fi
}

# Loop through all running containers
IFS=$'\n'
for entry in $containers; do
    id=${entry%%:*}
    name=${entry##*:}
    skip=0

    if [ "$REQUIRE_LABEL" = "true" ]; then
        skip=1 # Skip by default unless lable is found
    fi

    # Use docker inspect to get the labels for the container
    labels=$(docker inspect --format '{{json .Config.Labels}}' $id)

    if echo "$labels" | grep -q '"nautical-backup.enable":"true"'; then
        echo "Enabling $name based on label."
        skip=0
    fi

    if echo "$labels" | grep -q '"nautical-backup.skip":"true"'; then
        echo "Skipping $name based on label."
        skip=1 # Add the container to the skip list
    fi

    for cur in "${SKIP_CONTAINERS[@]}"; do
        if [ "$cur" == "$name" ]; then
            skip=1
            echo "Skipping $name based on name."
            break
        fi
        if [ "$cur" == "$id" ]; then
            skip=1
            if [ "$cur" == "$SELF_CONTAINER_ID" ]; then
                break # Exclude self from logs
            fi
            echo "Skipping $name based on ID $id."
            break
        fi
    done

    if [ $skip -eq 0 ]; then
        BackupContainer "$name"
    fi
done

containers_skipped=$((number_of_containers - containers_completed))

echo "Success. $containers_completed containers backed up! $containers_skipped skipped."
