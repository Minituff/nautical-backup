if [ "$TEST_MODE" == "true" ]; then
    echo "--- Running utils.sh in test mode ---"
    source ../pkg/logger.sh # Use the logger script
else
    source /app/logger.sh # Use the logger script
fi

# Function to populate a list array
process_csv() {
    local -n skip_list_ref=$1 # Use nameref to update the array passed as argument
    local skip_var=$2         # The environment variable containing the skip list

    if [ ! -z "$skip_var" ]; then
        # Remove quotes and leading/trailing whitespaces
        local cleaned_skip_var=$(echo "$skip_var" | sed "s/'//g;s/\"//g" | tr -d ' ')

        # Split by commas into an array
        IFS=',' read -ra ADDITIONAL_SKIPS <<<"$cleaned_skip_var"

        # Add to the existing skip list
        skip_list_ref=("${skip_list_ref[@]}" "${ADDITIONAL_SKIPS[@]}")
    fi
}

verify_source_location() {
    local src_dir=$1
    logThis "Verifying source directory $src_dir..." "DEBUG" "init"
    if [ ! -d "$src_dir" ]; then
        logThis "Error: Source directory $src_dir does not exist." "ERROR" "init"
        exit 1
    elif [ ! -r "$src_dir" ]; then
        logThis "Error: No read access to source directory $src_dir." "ERROR" "init"
        exit 1
    fi
}

verify_destination_location() {
    local dest_dir=$1
    logThis "Verifying destination directory $dest_dir..." "DEBUG" "init"
    if [ ! -d "$dest_dir" ]; then
        logThis "Error: Destination directory $dest_dir does not exist." "ERROR" "init"
        exit 1
    elif [ ! -r "$dest_dir" ]; then
        logThis "Error: No read access to destination directory $dest_dir." "ERROR" "init"
        exit 1
    elif [ ! -w "$dest_dir" ]; then
        logThis "Error: No write access to destination directory $dest_dir." "ERROR" "init"
        exit 1
    fi
}
