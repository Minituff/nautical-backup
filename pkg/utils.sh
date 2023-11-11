#!/usr/bin/with-contenv bash

source /app/logger.sh # Use the logger script

export_env() {
  local var_name="$1"
  local var_value="$2"
  local env_file="/var/run/s6/container_environment/$var_name"
  printf "%s" "$var_value" > "$env_file"
  export "${var_name}"
}

cecho() {
  RED="\033[0;31m"
  GREEN="\033[0;32m"  # <-- [0 means not bold
  YELLOW="\033[1;33m" # <-- [1 means bold
  CYAN="\033[1;36m"
  # ... Add more colors if you like

  NC="\033[0m" # No Color

  # printf "${(P)1}${2} ${NC}\n" # <-- zsh
  printf "${!1}${2} ${NC}\n" # <-- bash
}


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


initialize_logThis() {
    if [ ! -f "/usr/local/bin/logThis" ]; then
        logThis "Installing logThis script..." "DEBUG" "init"
        # Allows the logThis backup script to be run using `bash logThis`
        ln -s /app/logger.sh /usr/local/bin/logThis
        chmod +x /usr/local/bin/logThis
    fi
}

initialize_nautical() {
    if [ ! -f "/usr/local/bin/nautical" ]; then
        logThis "Installing nautical backup script..." "DEBUG" "init"
        # Allows the nautical backup script to be run using `bash nautical`
        ln -s /app/backup.sh /usr/local/bin/nautical
        chmod +x /usr/local/bin/nautical
    fi
}

# Function to initialize the database if it doesn't exist
initialize_db() {
    local db_path=$1
    local db_name=$2
    local db_full_path="$db_path/$db_name"

    if [ -f "$db_full_path" ]; then
        logThis "Connected to database at '$db_full_path'..." "DEBUG" "init"
    else
        logThis "Initializing databse at '$db_full_path'..." "DEBUG" "init"
        # Check if directory exists, if not create it
        if [ ! -d "$db_path" ]; then
            mkdir -p "$db_path"
        fi

        # Check if database file exists, if not create it
        if [ ! -f "$db_full_path" ]; then
            logThis "Datbase Path: $db_full_path" "DEBUG" "init"
            echo "{}" > "$db_full_path"
        fi

    fi

    if [ ! -f "/usr/local/bin/db" ]; then
        logThis "Installing database script..." "DEBUG" "init"
        # Allows the database script to be run using `bash db --help`
        # cp /app/db.sh /usr/local/bin/db
        ln -s /app/db.sh /usr/local/bin/db
        chmod +x /usr/local/bin/db
    fi

    db put "backup-running" "false"
}

verify_source_location() {
    local src_dir=$1
    logThis "Verifying source directory '$src_dir'..." "DEBUG" "init"
    # :nocov:
    if [ ! -d "$src_dir" ]; then
        logThis "Source directory '$src_dir' does not exist." "ERROR" "init"
        exit 1
    elif [ ! -r "$src_dir" ]; then
        logThis "No read access to source directory '$src_dir'." "ERROR" "init"
        exit 1
    fi
    # :nocov:
}

verify_destination_location() {
    local dest_dir=$1
    logThis "Verifying destination directory '$dest_dir'..." "DEBUG" "init"
    # :nocov:
    if [ ! -d "$dest_dir" ]; then
        logThis "Destination directory '$dest_dir' does not exist." "ERROR" "init"
        exit 1
    elif [ ! -r "$dest_dir" ]; then
        logThis "No read access to destination directory '$dest_dir'." "ERROR" "init"
        exit 1
    elif [ ! -w "$dest_dir" ]; then
        logThis "No write access to destination directory '$dest_dir'." "ERROR" "init"
        exit 1
    fi
    # :nocov:
}
