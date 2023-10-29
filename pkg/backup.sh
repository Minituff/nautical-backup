#!/bin/bash

if [ "$TEST_MODE" == "true" ]; then
    source pkg/logger.sh # Use the logger script
else
    source /app/logger.sh # Use the logger script
fi

logThis "Starting backup..."

# Convert the string back to an array
if [ ! -z "$CONTAINER_SKIP_LIST_STR" ]; then
    IFS=',' read -ra SKIP_CONTAINERS <<<"$CONTAINER_SKIP_LIST_STR"
fi

# Convert the string back to an array
if [ ! -z "$SKIP_STOPPING_STR" ]; then
    IFS=',' read -ra SKIP_STOPPING <<<"$SKIP_STOPPING_STR"
fi

# Convert the string back to an array
# if [ ! -z "$ADDITIONAL_FOLDERS_LIST_STR" ]; then
#     IFS=',' read -ra ADDITIONAL_FOLDERS <<<"$ADDITIONAL_FOLDERS_LIST_STR"
# fi

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

logThis "Processing $number_of_containers containers..."

# Define the name for the report file
report_file="Backup Report - $(date +'%Y-%m-%d').txt"

DEFAULT_RSYNC_ARGS="-ahq"
default_rsync_args="-ahq"
if [ "$USE_DEFAULT_RSYNC_ARGS" = "false" ]; then
    logThis "Disabling default rsync arguments ($DEFAULT_RSYNC_ARGS)" "DEBUG"
    default_rsync_args=""
fi

# Global variables to hold rsync arguments
custom_args=""
if [ ! -z "$RSYNC_CUSTOM_ARGS" ]; then
    logThis "Adding custom rsync arguments ($RSYNC_CUSTOM_ARGS)" "DEBUG"
    custom_args="$RSYNC_CUSTOM_ARGS"
fi

# Merge the default skips with provided skips
currs=("${currs[@]}" "${SKIP_CONTAINERS[@]}")
containers_completed=0

BackupAdditionalFolders() {
    IFS=',' read -ra new_additional_folders <<< "$1"
    local new_default_rsync_args=$2
    local new_custom_args=$3

    if [ -z "$ADDITIONAL_FOLDERS" ]; then
        return
    fi

    for additional_folder in "${new_additional_folders[@]}" ; do
        local src_dir="$SOURCE_LOCATION/$additional_folder"
        local dest_dir="$DEST_LOCATION/$additional_folder"

        logThis "Backing up $additional_folder as it's in the ADDITIONAL_FOLDERS list." "DEBUG"

        logThis "RUNNING: 'rsync $new_default_rsync_args $new_custom_args $src_dir/ $dest_dir/'" "DEBUG"

        eval rsync $new_default_rsync_args $new_custom_args $src_dir/ $dest_dir/

        logThis "Backed up folder '$additional_folder'" "INFO"

    done
}

BackupContainer() {
    local container=$1
    local labels=$2

    local skip_stopping=0
    for skip in "${SKIP_STOPPING[@]}"; do
        if [ "$skip" == "$container" ]; then
            skip_stopping=1
            logThis "Skipping stopping of $container as it's in the SKIP_STOPPING list." "DEBUG"
            break
        fi
    done

    if echo "$labels" | grep -q '"nautical-backup.stop-before-backup":"false"'; then
        logThis "Skipping stopping of $container because of label." "DEBUG"
        skip_stopping=1
    fi

    local src_dir="$SOURCE_LOCATION/$container"
    local src_name="$container"
    if [ ! -z "${override_source_dirs[$container]}" ]; then
        src_dir="$SOURCE_LOCATION/${override_source_dirs[$container]}"
        src_name="${override_source_dirs[$container]}" # Override source name
        logThis "Overriding source directory for $container to ${override_source_dirs[$container]}" "DEBUG"
    fi

    if echo "$labels" | grep -q '"nautical-backup.override-source-dir"'; then
        src_name=$(echo "$labels" | jq -r '.["nautical-backup.override-source-dir"]') # Override source name
        src_dir="$SOURCE_LOCATION/$src_name"
        logThis "Overriding source directory for $container to $src_name from label" "DEBUG"
    fi

    # Start with the source directory as as the destination directory (unless overridden or disabled)
    local dest_dir="$DEST_LOCATION/${src_name}"

    if [ "$KEEP_SRC_DIR_NAME" = "false" ] || echo "$labels" | grep -q '"nautical-backup.keep_src_dir_name":"false"'; then
        logThis "Setting destination directory for $container back to container name" "DEBUG"
        dest_dir="$DEST_LOCATION/$container" # Set back to container name
    fi
    if echo "$labels" | grep -q '"nautical-backup.keep_src_dir_name":"true"'; then
        dest_dir="$DEST_LOCATION/${src_name}"
    fi

    if [ ! -z "${override_dest_dirs[$container]}" ]; then
        dest_dir="$DEST_LOCATION/${override_dest_dirs[$container]}"
        logThis "Overriding destination directory for $container to ${override_dest_dirs[$container]}" "DEBUG"
    fi

    if echo "$labels" | grep -q '"nautical-backup.override-destination-dir"'; then
        new_destination_dir=$(echo "$labels" | jq -r '.["nautical-backup.override-destination-dir"]')
        dest_dir="$DEST_LOCATION/$new_destination_dir"
        logThis "Overriding destination directory for $container to $new_destination_dir from label" "DEBUG"
    fi

    if [ -d "$src_dir" ]; then
        if [ $skip_stopping -eq 0 ]; then
            logThis "Stopping $container..."
            docker stop $container 2>&1 >/dev/null
            if [ $? -ne 0 ]; then
                logThis "Error stopping container $container. Skipping backup for this container." "ERROR"
                return
            fi
        fi

        if echo "$labels" | grep -q '"nautical-backup.use-default-rsync-args":"true"'; then
            logThis "Using default rsync args ($DEFAULT_RSYNC_ARGS) for $container" "DEBUG"
            default_rsync_args=$DEFAULT_RSYNC_ARGS
        elif echo "$labels" | grep -q '"nautical-backup.use-default-rsync-args":"false"'; then
            logThis "Not using default rsync args ($DEFAULT_RSYNC_ARGS) for $container" "DEBUG"
            default_rsync_args=""
        fi

        if echo "$labels" | grep -q '"nautical-backup.rsync-custom-args"'; then
            new_custom_rsync_args=$(echo "$labels" | jq -r '.["nautical-backup.rsync-custom-args"]')
            custom_args=$new_custom_rsync_args
            logThis "Using custom rsync args for $container" "DEBUG"
        fi

        logThis "Backing up $container data..."
        logThis "RUNNING: 'rsync $default_rsync_args $custom_args $src_dir/ $dest_dir/'" "DEBUG"

        # Run rsync
        eval rsync $default_rsync_args $custom_args $src_dir/ $dest_dir/

        if [ $? -ne 0 ]; then
            logThis "Error copying data for container $container. Skipping backup for this container." "ERROR"
        fi

        if [ $skip_stopping -eq 0 ]; then
            logThis "Starting $container container..."
            docker start $container 2>&1 >/dev/null
            if [ $? -ne 0 ]; then
                logThis "Error restarting container $container. Please check manually!" "ERROR"
                return
            fi
        fi

        logThis "$container completed."
        ((containers_completed++))
    else
        logThis "Directory $src_dir does not exist. Skipping" "WARN"
    fi
}

if [ "$ADDITIONAL_FOLDERS_WHEN" = "before" ] ; then
    BackupAdditionalFolders $ADDITIONAL_FOLDERS_LIST_STR $default_rsync_args $custom_args
fi

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
    local labels=$(docker inspect --format '{{json .Config.Labels}}' $id)

    if echo "$labels" | grep -q '"nautical-backup.enable":"true"'; then
        logThis "Enabling $name based on label." "DEBUG"
        skip=0 # Do not skip the container
    elif echo "$labels" | grep -q '"nautical-backup.enable":"false"'; then
        logThis "Skipping $name based on label." "DEBUG"
        skip=1 # Add the container to the skip list
    elif [ "$REQUIRE_LABEL" = "true" ]; then
        if [ "$id" != "$SELF_CONTAINER_ID" ]; then
            logThis "Skipping $name as 'nautical-backup.enable=true' was not found and REQUIRE_LABEL is true." "DEBUG"
        fi
    fi

    for cur in "${SKIP_CONTAINERS[@]}"; do
        if [ "$cur" == "$name" ]; then
            skip=1
            logThis "Skipping $name based on name." "DEBUG"
            break
        fi
        if [ "$cur" == "$id" ]; then
            skip=1
            if [ "$cur" == "$SELF_CONTAINER_ID" ]; then
                break # Exclude self from logs
            fi
            logThis "Skipping $name based on ID $id." "DEBUG"
            break
        fi
    done

    if [ $skip -eq 0 ]; then
        new_additional_folders_from_label=$(echo "$labels" | jq -r '.["nautical-backup.additional-folders"]')
        # if echo "$labels" | grep -q '"nautical-backup.additional-folder.when":"before"'; then
        #     new_additional_folders_from_label=$(echo "$labels" | jq -r '.["nautical-backup.rsync-custom-args"]')
        # fi
        BackupContainer "$name" "$labels"
        # if echo "$labels" | grep -q '"nautical-backup.additional-folder.when":"after"'; then
        #     new_additional_folders_from_label=$(echo "$labels" | jq -r '.["nautical-backup.rsync-custom-args"]')
        # fi
    fi
done

containers_skipped=$((number_of_containers - containers_completed))

logThis "Success. $containers_completed containers backed up! $containers_skipped skipped." "INFO"

if [ "$ADDITIONAL_FOLDERS_WHEN" = "after" ] ; then
    BackupAdditionalFolders $ADDITIONAL_FOLDERS_LIST_STR $default_rsync_args $custom_args
fi

if [ "$RUN_ONCE" = "true" ]; then
    logThis "Exiting since RUN_ONCE is true" "INFO" "init"
    exit 0
fi
