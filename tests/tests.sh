#!/bin/bash

export MOCK_DOCKER_PS_OUTPUT=""
export MOCK_DOCKER_INSPECT_OUTPUT=""
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
  elif [ "$1" == "inspect" ]; then
    echo -e "$MOCK_DOCKER_INSPECT_OUTPUT"
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

teardown(){
  rm "$DOCKER_COMMANDS_FILE"
  rm "$RSYNC_COMMANDS_RFILE"
  rm -rf tests/src
  rm -rf tests/dest

  source pkg/logger.sh

  delete_report_file
}

cleanup_on_success() {
  clear_files
  rm -rf tests/src
  rm -rf tests/dest
}

cleanup_on_fail() {
  cleanup_on_success
  exit 1
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

pass() {
  local func_name=$1
  local test_num=$2
  cecho "GREEN" "✔ PASS - $func_name $test_num"
}

fail() {
  local func_name=$1
  local test_num=$2
  cecho "RED" "X $func_name $test_num FAIL"
}

test_docker() {
  local mock_docker_ps_lines
  local disallowed_docker_output
  local expected_docker_output
  local test_name

  # Parse named parameters
  while [[ "$#" -gt 0 ]]; do
    case $1 in
    --name)
      test_name="$2"
      shift
      ;;
    --mock)
      mock_docker_ps_lines="$2"
      shift
      ;;
    --disallow)
      disallowed_docker_output="$2"
      shift
      ;;
    --expect)
      expected_docker_output="$2"
      shift
      ;;
    *)
      echo "Unknown parameter passed: $1"
      cleanup_on_fail
      ;;
    esac
    shift
  done

  IFS=$'\n' read -rd '' -a mock_docker_ps_lines_arr <<<"$mock_docker_ps_lines"
  IFS=$'\n' read -rd '' -a disallowed_docker_output_arr <<<"$disallowed_docker_output"
  IFS=$'\n' read -rd '' -a expected_docker_output_arr <<<"$expected_docker_output"

  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines_arr[@]}")

  source pkg/entry.sh

  test_passed=true # Initialize a flag to indicate test status

  mapfile -t docker_actual_output <"$DOCKER_COMMANDS_FILE"

  # Check if each expected command is in the actual output
  for expected_docker in "${expected_docker_output_arr[@]}"; do # Use the _arr array here
    found=false
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$expected_docker" ]]; then
        found=true
        break
      fi
    done
    if [ "$found" = false ]; then
      fail "$test_name"
      echo "'$expected_docker' not found in expected_docker_output."
      test_passed=false
      cleanup_on_fail
    fi
  done

  # Check if any disallowed command is in the actual output
  for disallowed_docker in "${disallowed_docker_output_arr[@]}"; do # Use the _arr array here
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$disallowed_docker" ]]; then
        fail "$test_name"
        echo "'$disallowed_docker' found in actual output but is disallowed."
        test_passed=false
        cleanup_on_fail
      fi
    done
  done

  if [ "$test_passed" = true ]; then
    pass "$test_name"
  else
    fail "$test_name" "Commands do not match expected output."
    echo "Expected:"
    printf "%s\n" "${expected_docker_output_arr[@]}"
    echo "Actual:"
    printf "%s\n" "${docker_actual_output[@]}"
    cleanup_on_fail
  fi
}

test_rsync() {
  local test_name
  local mock_docker_ps_lines
  local expected_rsync_output
  local disallowed_rsync_output

  # Parse named parameters
  while [[ "$#" -gt 0 ]]; do
    case $1 in
    --name)
      test_name="$2"
      shift
      ;;
    --mock)
      mock_docker_ps_lines="$2"
      shift
      ;;
    --expect)
      expected_rsync_output="$2"
      shift
      ;;
    --disallow)
      disallowed_rsync_output="$2"
      shift
      ;;
    *)
      echo "Unknown parameter passed: $1"
      cleanup_on_fail
      ;;
    esac
    shift
  done

  IFS=$'\n' read -rd '' -a mock_docker_ps_lines_arr <<<"$mock_docker_ps_lines"
  IFS=$'\n' read -rd '' -a expected_rsync_output_arr <<<"$expected_rsync_output"
  IFS=$'\n' read -rd '' -a disallowed_rsync_output_arr <<<"$disallowed_rsync_output"

  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines_arr[@]}")

  source pkg/entry.sh

  test_passed=true # Initialize a flag to indicate test status

  mapfile -t rsync_actual_output <"$RSYNC_COMMANDS_RFILE"

  # Check if each expected command is in the actual output
  for expected_rsync in "${expected_rsync_output_arr[@]}"; do
    found=false
    for actual_rsync in "${rsync_actual_output[@]}"; do
      if [[ "$actual_rsync" == "$expected_rsync" ]]; then
        found=true
        break
      fi
    done
    if [ "$found" = false ]; then
      fail $test_name
      echo "RSYNC '$expected_rsync' not found in actual output."
      test_passed=false
    fi
  done

  # Check if any disallowed command is in the actual output
  for disallowed_rsync in "${disallowed_rsync_output_arr[@]}"; do
    for actual_rsync in "${rsync_actual_output[@]}"; do
      if [[ "$actual_rsync" == "$disallowed_rsync" ]]; then
        fail $test_name
        echo "RSYNC '$disallowed_rsync' found in actual output but is disallowed."
        test_passed=false
      fi
    done
  done

  if [ "$test_passed" = true ]; then
    pass $test_name
  else
    fail "$test_name"
    echo "Expected:"
    printf "%s\n" "${expected_rsync_output_arr[@]}"
    echo "Actual:"
    printf "%s\n" "${rsync_actual_output[@]}"
  fi
}

# ---- Actual Tests ----

test_skip_containers() {
  clear_files
  export BACKUP_ON_START="true"
  SKIP_CONTAINERS=container1,container-name2,container-name3

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
  )

  test_passed=true # Initialize a flag to indicate test status
  # Read the lines from the file into an array

  mapfile -t docker_actual_output <"$DOCKER_COMMANDS_FILE"

  # Check if each expected command is in the actual output
  for expected_docker in "${expected_docker_output[@]}"; do
    found=false
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$expected_docker" ]]; then
        found=true
        break
      fi
    done
    if [ "$found" = false ]; then
      fail "${FUNCNAME[0]}"
      echo "'$expected_docker' not found in expected_docker_output."
      test_passed=false
      cleanup_on_fail
    fi
  done

  declare -a expected_rsync_output=(
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
      echo "${FUNCNAME[0]} FAIL: RSYNC '$expected_rsync' not found in actual output."
      test_passed=false
    fi
  done

  if [ "$test_passed" = true ]; then
    pass ${FUNCNAME[0]} "1/2"
  else
    fail ${FUNCNAME[0]} "2/2"
    echo "Expected:"
    print_array "${expected_rsync_output[@]}"
    echo "Actual:"
    print_array "${rsync_actual_output[@]}"
  fi

  if [ "$test_passed" = true ]; then
    pass ${FUNCNAME[0]} "2/2"
  else
    fail ${FUNCNAME[0]} "2/2"
    echo "Expected:"
    print_array "${expected_output[@]}"
    echo "Actual:"
    print_array "${docker_actual_output[@]}"
    cleanup_on_fail
  fi

}

test_docker_commands() {
  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  disallowed_docker_output=$(
    echo "stop container2" &&
      echo "start container2" &&
      echo "stop container3" &&
      echo "start container3"
  )

  expected_docker_output=$(
    echo "ps --no-trunc --format={{.ID}}:{{.Names}}" &&
      echo "inspect --format {{json .Config.Labels}} abc123" &&
      echo "stop container1" &&
      echo "start container1"
  )

  test_docker \
    --name "Test Docker Commands on default settings" \
    --mock "$mock_docker_ps_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"
  
  cleanup_on_success
}

test_rsync_commands() {
  clear_files
  export BACKUP_ON_START="true"

  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  disallowed_rsync_output=$(
    echo "stop container3" &&
      echo "start container3"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_rsync \
    --name "Test Rsync on default settings" \
    --mock "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

# Run the tests
test_rsync_commands
test_docker_commands
# test_skip_containers

# Cleanup
teardown