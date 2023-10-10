#!/bin/bash

echo "Starting backup script..."

# Convert the string back to an array
if [ ! -z "$CONTAINER_SKIP_LIST_STR" ]; then
    IFS=',' read -ra SKIP_CONTAINERS <<< "$CONTAINER_SKIP_LIST_STR"
fi

declare -A override_source_dirs

if [ ! -z "$OVERRIDE_SOURCE_DIR" ]; then
    IFS=',' read -ra PAIRS <<< "$OVERRIDE_SOURCE_DIR"
    for pair in "${PAIRS[@]}"; do
        IFS=':' read -ra KV <<< "$pair"
        override_source_dirs[${KV[0]}]=${KV[1]}
    done
fi

declare -A override_dest_dirs

if [ ! -z "$OVERRIDE_DEST_DIR" ]; then
    IFS=',' read -ra PAIRS <<< "$OVERRIDE_DEST_DIR"
    for pair in "${PAIRS[@]}"; do
        IFS=':' read -ra KV <<< "$pair"
        override_dest_dirs[${KV[0]}]=${KV[1]}
    done
fi

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
    echo "Backup Report - $(date)" > "$DEST_LOCATION/$report_file"
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
        echo "$(date) - $message" >> "$DEST_LOCATION/$report_file"
    fi
}


BackupContainer() {
    local container=$1

    
    local src_dir="$SOURCE_LOCATION/$container" # Determine the source directory to use for this container
    
    if [ ! -z "${override_source_dirs[$container]}" ]; then
        src_dir="$SOURCE_LOCATION/${override_source_dirs[$container]}"
        echo "Overriding source directory for $container to ${override_source_dirs[$container]}"
    fi

    local dest_dir="$DEST_LOCATION/$container" # Determine the source directory to use for this container

    if [ ! -z "${override_dest_dirs[$container]}" ]; then
        dest_dir="$DEST_LOCATION/${override_dest_dirs[$container]}"
        echo "Overriding destination directory for $container to ${override_dest_dirs[$container]}"
    fi

    if [ -d "$src_dir" ]; then

        log_entry "Stopping $container..."
        docker stop $container 2>&1 >/dev/null
        if [ $? -ne 0 ]; then
            log_entry "Error stopping container $container. Skipping backup for this container."
            return
        fi

        log_entry "Backing up $container data..."
        rsync -ah -q --info=progress2 --exclude '*.log' $src_dir/ $dest_dir/

        if [ $? -ne 0 ]; then
            log_entry "Error copying data for container $container. Skipping backup for this container."
            
            log_entry "Starting $container container..."
            docker start $container
            if [ $? -ne 0 ]; then
                log_entry "Error restarting container $container. Please check manually!"
                return
            fi

        fi

        
        log_entry "Starting $container container..."
        docker start $container 2>&1 >/dev/null
        if [ $? -ne 0 ]; then
            log_entry "Error restarting container $container. Please check manually!"
            return
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
    for cur in "${SKIP_CONTAINERS[@]}"; do
        if [ "$cur" == "$name" ]; then
            skip=1
            echo "Skipping $name based on name."
            break
        fi
        if [ "$cur" == "$id" ] ; then
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

echo "Success. $containers_completed containers backed up!"