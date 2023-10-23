#!/bin/bash

export MOCK_DOCKER_PS_OUTPUT=""
RSYNC_COMMANDS_RUN=()
DOCKER_COMMANDS_RUN=()
DOCKER_COMMANDS_FILE=$(mktemp /tmp/docker_commands.XXXXXX)
export DOCKER_COMMANDS_FILE

export TEST_MODE="true"

# Mock function for docker
docker() {
  # Capture the command
  echo "$@" >>"$DOCKER_COMMANDS_FILE"

  # Mock behavior based on command
  if [ "$1" == "ps" ]; then
    echo -e "$MOCK_DOCKER_PS_OUTPUT"
  fi
}
export -f docker

# Mock function for rsync
rsync() {
  RSYNC_COMMANDS_RUN+=("$@") # Capture the command for later verification
  echo "RSYNC_COMMANDS_RUN: rsync $@" >&2
  /usr/bin/rsync "$@" # Call the real rsync
}
export -f rsync

print_array() {
  local arr=("$@")
  for i in "${arr[@]}"; do
    echo "$i"
  done
}

# Test function
test_docker_ps() {

  declare -a mock_docker_ps_lines=(
    "abc123:container1"
    "def456:container2"
    "ghi789:container3"
  )
  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines[@]}")

  source ./pkg/entry.sh
  ../pkg/backup.sh

  declare -a expected_output=(
    "ps --no-trunc --format={{.ID}}:{{.Names}}"
    "inspect --format {{json .Config.Labels}} abc123"
    "inspect --format {{json .Config.Labels}} def456"
    "inspect --format {{json .Config.Labels}} ghi789"
  )

  # Read the lines from the file into an array
  mapfile -t actual_output <"$DOCKER_COMMANDS_FILE"

  # Initialize a flag to indicate test status
  test_passed=true

  # Check if each expected command is in the actual output
  for expected in "${expected_output[@]}"; do
    if ! printf '%s\n' "${actual_output[@]}" | grep -q -F "$expected"; then
      echo "FAIL: '$expected' not found in actual output."
      test_passed=false
    fi
  done

  if [ "$test_passed" = true ]; then
    echo "PASS: All expected commands were found."
  else
    echo "FAIL: Commands do not match expected output."
    echo "Expected:"
    print_array "${expected_output[@]}"
    echo "Actual:"
    print_array "${actual_output[@]}"
  fi

}

# Run the test
test_docker_ps
rm "$DOCKER_COMMANDS_FILE"
