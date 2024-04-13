#!/usr/bin/env bash

test_watchtower_backup_file() {

  local expected="This is a test file"
  local report_file="test-file.txt"
  local dest_location="destination/watchtower-test"

  local file_path="$dest_location/$report_file"

  
    if [ ! -f "$file_path" ]; then
        echo "'$file_path' not found. Exiting..."
        exit 1
    fi

  actual=$(tail -n 1 "$file_path")
  if [[ ! "$actual" =~ "$expected" ]]; then
    echo "Test Failed: Expected message not found in report file."
    echo "Actual:"
    echo "$actual"
    echo "Expected:"
    echo "$expected"
    exit 1
  fi

  echo "PASS: $report_file found in $dest_location"
}


test_config_json_file() {

  local report_file="nautical-db.json"
  local dest_location="config"

  local file_path="$dest_location/$report_file"

  
    if [ ! -f "$file_path" ]; then
        echo "'$file_path' not found. Exiting..."
        exit 1
    fi

    echo "PASS: $report_file found in $dest_location"
}

test_watchtower_backup_file
test_config_json_file