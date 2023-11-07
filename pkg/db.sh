#!/usr/bin/with-contenv bash

# Credit to: https://github.com/reddec/bash-db

# Helper function to decode base64
decode_base64() {
  base64 -d <<< "$1"
}

# Helper function to encode base64
encode_base64() {
  base64 -w 0 <<< "$1"
}

# Helper function to get the database path from parameters
get_db_path() {
  local db_path="$NAUTICAL_DB_PATH/$NAUTICAL_DB_NAME"
  if [[ "$1" == "--db" ]] && [[ -n "$2" ]]; then
    db_path="$2"
    # Remove the first two parameters (--db and path)
    shift 2
  fi
  echo "$db_path"
}

# Function to get value by key
get() {
  local db_path=$(get_db_path "$@")
  local key=$(encode_base64 "$1")
  sed -nr "s/^$key\ (.*$)/\1/p" "$db_path" | decode_base64
}

# Function to list all keys
list() {
  local db_path=$(get_db_path "$@")
  sed -nr "s/(^[^\ ]+)\ (.*$)/\1/p" "$db_path" | while read -r line; do decode_base64 "$line"; done
}

# Function to get the last added value
last() {
  local db_path=$(get_db_path "$@")
  tail -1 "$db_path" | cut -d ' ' -f2- | decode_base64
}

# Function to insert or update a record
put() {
  local db_path=$(get_db_path "$@")
  local key=$(encode_base64 "$1")
  local value=$(encode_base64 "$2")
  if [[ -z "$(grep "^$key " "$db_path")" ]]; then
    # Insert
    echo "$key $value" >> "$db_path"
  else
    # Update
    sed -i "s/^$key .*/$key $value/" "$db_path"
  fi
}

# Function to delete a record by key
delete() {
  local db_path=$(get_db_path "$@")
  local key=$(encode_base64 "$1")
  sed -i "/^$key /d" "$db_path"
}

# Function to show help
help() {
  echo '
Usage: db <get|list|last|put|delete> [--db <path>] <key> [value]

Commands:
get    - Get value of record by key
list   - List all keys in database
last   - Get the value of the last added record
put    - Insert or update record
delete - Delete record by key

Options:
--db   - Specify the database path (default is '"$NAUTICAL_DB_PATH/$NAUTICAL_DB_NAME"')

Example:
db put --db /path/to/db "key" "value"
'
}

# Start
case "$1" in
  get|list|last|put|delete)
    if [[ "$2" == "--help" ]]; then
      help
      exit 0
    fi
    "$@"
    ;;
  --help)
    help
    ;;
  *)
    echo "Unknown method '$1'"
    help
    exit 1
    ;;
esac
