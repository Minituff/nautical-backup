#!/usr/bin/env bash
#!/usr/bin/with-contenv bash

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
  local key="$1"

  jq --raw-output ".$key" "$db_path"
}

# Function to insert or update a record
# Only works at the root path
put() {
  local db_path=$(get_db_path "$@")
  local key="$1"
  local value="$2"

  jq --arg key "$key" --arg value "$value" '.[$key] = $value' "$db_path" > tmp && mv tmp "$db_path"
}

# Function to delete a record by key
delete() {
  local db_path=$(get_db_path "$@")
  local key="$1"

  jq "del(.$key)" "$db_path" > tmp && mv tmp "$db_path"
}

add_current_datetime() {
    local db_path=$(get_db_path "$@")
    local key="$1"  # The JSON key where the date and time will be added

    # Format the current date and time
    local datetime_format1=$(date +"%A, %B %d, %Y at %I:%M %p")
    local datetime_format2=$(date +"%m/%d/%y %I:%M")

    # Update or create the key with the formatted date and time
    jq --arg key "$key" --arg datetime1 "$datetime_format1" --arg datetime2 "$datetime_format2" \
       'if .[$key] then .[$key] |= if type == "array" then . + [$datetime1, $datetime2] else [$datetime1, $datetime2] end else .[$key] = [$datetime1, $datetime2] end' \
       "$db_path" > tmp && mv tmp "$db_path"
}




# Function to show help
help() {
  echo '
Usage: db <get|put|add_current_datetime|delete> [--db <path>] <key> [value]

Commands:
get    - Get value of record by key
put    - Insert or update record
add_current_datetime - Insert a date at a key
delete - Delete record by key

Options:
--db   - Specify the database path (default is '"$NAUTICAL_DB_PATH/$NAUTICAL_DB_NAME"')

Example:
db put --db /path/to/db "key" "value"
'
}

# Start
case "$1" in
  get|put|add_current_datetime|delete)
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
