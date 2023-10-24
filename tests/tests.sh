#!/bin/bash

export MOCK_DOCKER_PS_OUTPUT=""
DOCKER_COMMANDS_FILE=$(mktemp /tmp/docker_commands.XXXXXX)
RSYNC_COMMANDS_RFILE=$(mktemp /tmp/rsync_commands.XXXXXX)
export DOCKER_COMMANDS_FILE
export RSYNC_COMMANDS_RFILE

export TEST_MODE="true"
export LOG_LEVEL="ERROR"

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
  echo "$@" >>"$RSYNC_COMMANDS_RFILE"
  /usr/bin/rsync "$@" # Call the real rsync
}
export -f rsync

print_array() {
  local arr=("$@")
  for i in "${arr[@]}"; do
    echo "$i"
  done
}

clear_files() {
  >$RSYNC_COMMANDS_RFILE
  >$DOCKER_COMMANDS_FILE
}

# ---- Actual Tests ----

test_docker_ps() {
  clear_files
  export BACKUP_ON_START="true"
  pwd
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  declare -a mock_docker_ps_lines=(
    "abc123:container1"
    "def456:container2"
    "ghi789:container3"
  )
  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines[@]}")

  source pkg/entry.sh

  declare -a expected_docker_output=(
    "ps --no-trunc --format={{.ID}}:{{.Names}}"
    "inspect --format {{json .Config.Labels}} abc123"
    "inspect --format {{json .Config.Labels}} def456"
    "inspect --format {{json .Config.Labels}} ghi789"
    "stop container1"
    "start container1"
  )

  test_passed=true # Initialize a flag to indicate test status
  # Read the lines from the file into an array

  mapfile -t docker_actual_output <"$DOCKER_COMMANDS_FILE"

  # Check if each expected command is in the actual output
  for expected_docker in "${expected_docker_output[@]}"; do
    if ! printf '%s\n' "${docker_actual_output[@]}" | grep -q -F "$expected_docker"; then
      echo "FAIL: DOCKER '$expected_docker' not found in actual output."
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
    print_array "${docker_actual_output[@]}"
    exit 1
  fi

}

test_rsync() {
  clear_files
  export BACKUP_ON_START="true"

  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  declare -a mock_docker_ps_lines=(
    "abc123:container1"
    "def456:container2"
    "ghi789:container3"
  )
  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines[@]}")

  source pkg/entry.sh

  declare -a expected_rsync_output=(
    "-ahq tests/src/container1/ tests/dest/container1/"
    "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_passed=true # Initialize a flag to indicate test status
  # Read the lines from the file into an array

  # Check if each expected command is in the actual output

  mapfile -t rsync_actual_output <"$RSYNC_COMMANDS_RFILE"

  for expected_rsync in "${expected_rsync_output[@]}"; do
    found=false
    for actual_rsync in "${rsync_actual_output[@]}"; do
      if [[ "$actual_rsync" == "$expected_rsync" ]]; then
        found=true
        break
      fi
    done
    if [ "$found" = false ]; then
      echo "FAIL: RSYNC '$expected_rsync' not found in actual output."
      test_passed=false
    fi
  done

  if [ "$test_passed" = true ]; then
    echo "PASS: All expected commands were found."
  else
    echo "FAIL: Commands do not match expected output."
    echo "Expected:"
    print_array "${expected_rsync_output[@]}"
    echo "Actual:"
    print_array "${rsync_actual_output[@]}"
  fi

}


test_skip_containers() {
  clear_files
  export BACKUP_ON_START="true"
  SKIP_CONTAINERS=container1,container-name2,container-name3


  mkdir -p tests/source/container1 && touch tests/source/container1/test.txt
  mkdir -p tests/destination

  declare -a mock_docker_ps_lines=(
    "abc123:container1"
    "def456:container2"
    "ghi789:container3"
  )
  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines[@]}")

  source pkg/entry.sh

  declare -a expected_docker_output=(
    "ps --no-trunc --format={{.ID}}:{{.Names}}"
    "inspect --format {{json .Config.Labels}} abc123"
    "inspect --format {{json .Config.Labels}} def456"
    "inspect --format {{json .Config.Labels}} ghi789"
  )

  test_passed=true # Initialize a flag to indicate test status
  # Read the lines from the file into an array

  mapfile -t docker_actual_output <"$DOCKER_COMMANDS_FILE"

  # Check if each expected command is in the actual output
  for expected_docker in "${expected_docker_output[@]}"; do
    if ! printf '%s\n' "${docker_actual_output[@]}" | grep -q -F "$expected_docker"; then
      echo "FAIL: DOCKER '$expected_docker' not found in actual output."
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
    print_array "${docker_actual_output[@]}"
    exit 1
  fi

}

# Run the tests
test_docker_ps
test_rsync
# test_skip_containers

# Cleanup
rm "$DOCKER_COMMANDS_FILE"
rm "$RSYNC_COMMANDS_RFILE"
rm -rf tests/src
rm -rf tests/dest

source pkg/logger.sh

delete_report_file
