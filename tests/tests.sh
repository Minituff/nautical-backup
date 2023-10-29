#!/bin/bash

export MOCK_DOCKER_PS_OUTPUT=""
DOCKER_COMMANDS_FILE=$(mktemp /tmp/docker_commands.XXXXXX)
RSYNC_COMMANDS_RFILE=$(mktemp /tmp/rsync_commands.XXXXXX)
export MOCK_DOCKER_INSPECT_OUTPUT=""
export DOCKER_COMMANDS_FILE
export RSYNC_COMMANDS_RFILE

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

reset_environment_variables() {
  TEST_MODE="true"
  LOG_LEVEL="ERROR"
  BACKUP_ON_START="true"
  REPORT_FILE="false"
  RUN_ONCE="false"

  TZ=""
  CRON_SCHEDULE=""
  USE_DEFAULT_RSYNC_ARGS=""
  REQUIRE_LABEL=""
  REPORT_FILE_LOG_LEVEL=""
  REPORT_FILE_ON_BACKUP_ONLY=""
  KEEP_SRC_DIR_NAME=""
  EXIT_AFTER_INIT=""
  LOG_RSYNC_COMMANDS=""
  SOURCE_LOCATION=""
  DEST_LOCATION=""
  TEST_SOURCE_LOCATION=""
  TEST_DEST_LOCATION=""
  SKIP_CONTAINERS=""
  SKIP_STOPPING=""
  RSYNC_CUSTOM_ARGS=""
  OVERRIDE_SOURCE_DIR=""
  OVERRIDE_DEST_DIR=""
}

clear_files() {
  >$RSYNC_COMMANDS_RFILE
  >$DOCKER_COMMANDS_FILE
}

teardown() {
  rm "$DOCKER_COMMANDS_FILE"
  rm "$RSYNC_COMMANDS_RFILE"
  rm -rf tests/src
  rm -rf tests/dest

  source pkg/logger.sh

  delete_report_file
}

cleanup_on_success() {
  reset_environment_variables
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
  cecho "RED" "X FAIL - $func_name $test_num"
}

test_docker() {
  local mock_docker_ps_lines
  local mock_docker_labels
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
    --mock_ps)
      mock_docker_ps_lines="$2"
      shift
      ;;
    --disallow)
      disallowed_docker_output="$2"
      shift
      ;;
    --mock_labels)
      mock_docker_labels="$2"
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
  IFS=$'\n' read -rd '' -a mock_docker_labels_arr <<<"$mock_docker_labels"
  IFS=$'\n' read -rd '' -a disallowed_docker_output_arr <<<"$disallowed_docker_output"
  IFS=$'\n' read -rd '' -a expected_docker_output_arr <<<"$expected_docker_output"

  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines_arr[@]}")
  MOCK_DOCKER_INSPECT_OUTPUT=$(printf "%s\n" "${mock_docker_labels_arr[@]}")

  source pkg/entry.sh

  # If test_name is blank, return
  if [ -z "$test_name" ]; then
    return
  fi

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
    fi
  done

  # Check if any disallowed command is in the actual output
  for disallowed_docker in "${disallowed_docker_output_arr[@]}"; do # Use the _arr array here
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$disallowed_docker" ]]; then
        fail "$test_name"
        echo "'$disallowed_docker' found in actual output but is disallowed."
        test_passed=false
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
  local mock_docker_labels
  local expected_rsync_output
  local disallowed_rsync_output

  # Parse named parameters
  while [[ "$#" -gt 0 ]]; do
    case $1 in
    --name)
      test_name="$2"
      shift
      ;;
    --mock_ps)
      mock_docker_ps_lines="$2"
      shift
      ;;
    --mock_labels)
      mock_docker_labels="$2"
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
  IFS=$'\n' read -rd '' -a mock_docker_labels_arr <<<"$mock_docker_labels"
  IFS=$'\n' read -rd '' -a expected_rsync_output_arr <<<"$expected_rsync_output"
  IFS=$'\n' read -rd '' -a disallowed_rsync_output_arr <<<"$disallowed_rsync_output"

  # Set what the next docker ps command should return
  MOCK_DOCKER_PS_OUTPUT=$(printf "%s\n" "${mock_docker_ps_lines_arr[@]}")
  MOCK_DOCKER_INSPECT_OUTPUT=$(printf "%s\n" "${mock_docker_labels_arr[@]}")

  source pkg/entry.sh

  # If test_name is blank, return
  if [ -z "$test_name" ]; then
    return
  fi

  test_passed=true # Initialize a flag to indicate test status

  mapfile -t rsync_actual_output <"$RSYNC_COMMANDS_RFILE" # Make a copy because we reduce this array
  mapfile -t rsync_actual_output_copy <"$RSYNC_COMMANDS_RFILE"

  # Check if each expected command is in the actual output
  for expected_rsync in "${expected_rsync_output_arr[@]}"; do
    found=false

    # Loop through each actual rsync command
    for index in "${!rsync_actual_output[@]}"; do
      actual_rsync=${rsync_actual_output[index]}

      # If the expected rsync command is found in the actual output
      if [[ "$actual_rsync" == "$expected_rsync" ]]; then
        found=true

        # Remove the found element from the actual output array
        unset 'rsync_actual_output[index]'

        # Since we found a match, no need to continue this inner loop
        break
      fi
    done

    # If the expected rsync command was not found in the actual output
    if [ "$found" = false ]; then
      fail $test_name
      echo "RSYNC '$expected_rsync' not found in actual output."
      test_passed=false
    fi
  done

  # Check if the actual output array is larger than the expected output array
  if [[ ${#rsync_actual_output[@]} -gt 0 ]]; then
    fail $test_name
    echo "Actual output contains more lines than expected."
    test_passed=false
  fi

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
    printf "%s\n" "${rsync_actual_output_copy[@]}"
  fi
}

# ---- Actual Tests ----

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
    --name "Test Docker commands on default settings" \
    --mock_ps "$mock_docker_ps_lines" \
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
    echo "anthing_to_not_allow"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_rsync \
    --name "Test Rsync commands on default settings" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

test_skip_containers() {
  clear_files
  export BACKUP_ON_START="true"
  SKIP_CONTAINERS=container1,container-name2,container-name3
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container2/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$(
    echo "stop container2" &&
      echo "start container2"
  )

  test_docker \
    --name "Test SKIP_CONTAINERS" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  cleanup_on_success
}

test_enable_label() {
  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )
  mock_docker_label_lines=$(
    echo "\"com.docker.compose.oneoff\":\"False",\" &&
      echo "\"nautical-backup.enable\":\"false\""
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$()

  test_docker \
    --name "Test nautical-backup.enable=false" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  expected_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )
  mock_docker_label_lines=$(
    echo "{\"com.docker.compose.oneoff\":\"False",\" &&
      echo "\"nautical-backup.enable\":\"true\"}"
  )

  test_docker \
    --name "Test nautical-backup.enable=true" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output"

  cleanup_on_success
}

test_require_label() {
  clear_files
  export BACKUP_ON_START="true"
  export REQUIRE_LABEL=true
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )
  mock_docker_label_lines=$(
    echo "{\"com.docker.compose.oneoff\":\"False",\" &&
      echo "\"nautical-backup.enable\":\"false\"}"
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$()

  test_docker --name "Test REQUIRE_LABEL + nautical-backup.enable=false" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  test_docker --name "Test REQUIRE_LABEL no label" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  expected_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )
  mock_docker_label_lines=$(
    echo "{\"com.docker.compose.oneoff\":\"False",\" &&
      echo "\"nautical-backup.enable\":\"true\"}"
  )

  test_docker \
    --name "Test REQUIRE_LABEL + nautical-backup.enable=true" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output"

  cleanup_on_success
}

test_override_src() {
  clear_files
  export BACKUP_ON_START="true"
  export OVERRIDE_SOURCE_DIR=container1:container1-override,container2:container2-override,container3:container3-new
  mkdir -p tests/src/container1-override && touch tests/src/container1-override/test.txt
  mkdir -p tests/src/container3-new && touch tests/src/container3-new/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1-override/ tests/dest/container1-override/" &&
      echo "-ahq tests/src/container3-new/ tests/dest/container3-new/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container3/ tests/dest/container3/"
  )

  test_rsync \
    --name "Test Source override (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --disallow "$disallowed_rsync_output" \
    --expect "$expected_rsync_output"

  cleanup_on_success
  mkdir -p tests/src/container-override && touch tests/src/container-override/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.override-source-dir\":\"container-override\"}"
  )
  expected_rsync_output=$(
    echo "-ahq tests/src/container-override/ tests/dest/container-override/"
  )
  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/"
  )

  test_rsync \
    --name "Test Source override (label)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output" \
    --mock_labels "$mock_docker_label_lines"

  reset_environment_variables
}

test_override_dest() {
  clear_files
  export BACKUP_ON_START="true"
  export OVERRIDE_DEST_DIR=container1:container1-override,container2:container2-override,container3:container3-new
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container3 && touch tests/src/container3/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1-override/" &&
      echo "-ahq tests/src/container3/ tests/dest/container3-new/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container3/ tests/dest/container3/"
  )

  test_rsync \
    --name "Test Destination override (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --disallow "$disallowed_rsync_output" \
    --expect "$expected_rsync_output"

  cleanup_on_success
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.override-destination-dir\":\"container-override\"}"
  )
  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container-override/"
  )
  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/"
  )

  test_rsync \
    --name "Test Destination override (label)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output" \
    --mock_labels "$mock_docker_label_lines"

  cleanup_on_success
}

test_skip_stopping_env() {
  clear_files
  export BACKUP_ON_START="true"
  export SKIP_STOPPING=container1,example2
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$(
    echo "ps --no-trunc --format={{.ID}}:{{.Names}}" &&
      echo "inspect --format {{json .Config.Labels}} abc123"
  )

  test_docker \
    --name "Test SKIP_STOPPING Docker (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/"
  )

  clear_files

  test_rsync \
    --name "Test SKIP_STOPPING Rsync (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output"

  cleanup_on_success
}

test_skip_stopping_label_false() {
  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$(
    echo "ps --no-trunc --format={{.ID}}:{{.Names}}" &&
      echo "inspect --format {{json .Config.Labels}} abc123"
  )

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.stop-before-backup\":\"false\"}"
  )

  test_docker \
    --name "Test SKIP_STOPPING Docker (label=false)" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/"
  )

  clear_files

  test_rsync \
    --name "Test SKIP_STOPPING Rsync (label=false)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --mock_labels "$mock_docker_label_lines"

  cleanup_on_success
}

test_skip_stopping_label_true() {
  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  expected_docker_output=$(
    echo "ps --no-trunc --format={{.ID}}:{{.Names}}" &&
      echo "inspect --format {{json .Config.Labels}} abc123" &&
      echo "stop container1" &&
      echo "start container1"
  )

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.stop-before-backup\":\"true\"}"
  )

  test_docker \
    --name "Test SKIP_STOPPING Docker (label=true)" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --expect "$expected_docker_output"

  expected_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/"
  )

  clear_files

  test_rsync \
    --name "Test SKIP_STOPPING Rsync (label=true)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --mock_labels "$mock_docker_label_lines"

  cleanup_on_success
}

test_report_file() {
  clear_files
  export BACKUP_ON_START="true"
  export REPORT_FILE="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  test_docker \
    --name "Test Docker commands on default settings" \
    --mock_ps "$mock_docker_ps_lines"

  # Look for .txt files in the folder
  txt_files=$(find "tests/dest" -maxdepth 1 -type f -name "*.txt")

  if [[ -z "$txt_files" ]]; then
    fail "Test Report File not found when REPORT_FILE=true"
    echo "No .txt files found in '$folder_path'."
    exit 1
  else
    pass "Test Report File (enabled)"
  fi

  cleanup_on_success

  export REPORT_FILE="false"
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  test_docker \
    --name "Test Docker commands on default settings" \
    --mock_ps "$mock_docker_ps_lines"

  # Look for .txt files in the folder
  txt_files=$(find "tests/dest" -maxdepth 1 -type f -name "*.txt")

  if [[ -z "$txt_files" ]]; then
    pass "Test Report File (disabled)"
  else
    fail "Test Report File found when REPORT_FILE=false"
    echo "No .txt files found in '$folder_path'."
    exit 1
  fi

  cleanup_on_success
}

test_custom_rsync_args_env() {
  clear_files
  export BACKUP_ON_START="true"
  export USE_DEFAULT_RSYNC_ARGS="false"
  export RSYNC_CUSTOM_ARGS=-aq

  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2"
  )

  expected_rsync_output=$(
    echo "-aq tests/src/container1/ tests/dest/container1/" &&
      echo "-aq tests/src/container2/ tests/dest/container2/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_rsync \
    --name "Testing custom rsync args (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

test_custom_rsync_args_label() {
  clear_files
  export BACKUP_ON_START="true"

  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2"
  )
  mock_docker_label_lines=$(
    echo "{\"nautical-backup.use-default-rsync-args\":\"false\"," &&
      echo "\"nautical-backup.rsync-custom-args\":\"-aq\"}"
  )
  expected_rsync_output=$(
    echo "-aq tests/src/container1/ tests/dest/container1/" &&
      echo "-aq tests/src/container2/ tests/dest/container2/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_rsync \
    --name "Testing custom rsync args (label)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --mock_labels "$mock_docker_label_lines" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

test_custom_rsync_args_both() {
  clear_files
  export BACKUP_ON_START="true"
  export USE_DEFAULT_RSYNC_ARGS="false"
  export RSYNC_CUSTOM_ARGS=-something

  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/src/container2 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2"
  )
  mock_docker_label_lines=$(
    echo "{\"nautical-backup.use-default-rsync-args\":\"false\"," &&
      echo "\"nautical-backup.rsync-custom-args\":\"-aq\"}"
  )
  expected_rsync_output=$(
    echo "-aq tests/src/container1/ tests/dest/container1/" &&
      echo "-aq tests/src/container2/ tests/dest/container2/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1/" &&
      echo "-ahq tests/src/container2/ tests/dest/container2/"
  )

  test_rsync \
    --name "Testing custom rsync args (label & env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --mock_labels "$mock_docker_label_lines" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

test_report_file_on_backup_only() {
  clear_files
  export BACKUP_ON_START="true"
  export REPORT_FILE="true"
  export REPORT_FILE_ON_BACKUP_ONLY="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  test_docker \
    --mock_ps "$mock_docker_ps_lines"

  # Look for .txt files in the folder
  txt_files=$(find "tests/dest" -maxdepth 1 -type f -name "*.txt")

  if [[ -z "$txt_files" ]]; then
    fail "REPORT_FILE_ON_BACKUP_ONLY=true did not creat a report file on backup"
    echo "No .txt files found in '$folder_path'."
    exit 1
  else
    pass "REPORT_FILE_ON_BACKUP_ONLY=true created a report file on backup"
  fi

  cleanup_on_success
  clear_files
  export BACKUP_ON_START="false"
  export REPORT_FILE="true"
  export REPORT_FILE_ON_BACKUP_ONLY="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  test_docker \
    --mock_ps "$mock_docker_ps_lines"

  # Look for .txt files in the folder
  txt_files=$(find "tests/dest" -maxdepth 1 -type f -name "*.txt")

  if [[ -z "$txt_files" ]]; then
    fail "REPORT_FILE_ON_BACKUP_ONLY=true did not create a repott file on Initialize"
    echo "No .txt files found in '$folder_path'."
    exit 1
  else
    pass "REPORT_FILE_ON_BACKUP_ONLY=true did not create a repott file on Initialize"
  fi

  cleanup_on_success
}

test_keep_src_dir_name_env() {
  clear_files
  export BACKUP_ON_START="true"
  export KEEP_SRC_DIR_NAME="true"
  test_override_dest
  cleanup_on_success

  export BACKUP_ON_START="true"
  export KEEP_SRC_DIR_NAME="false"
  export OVERRIDE_SOURCE_DIR=container1:container1-override,container2:container2-override,container3:container3-new
  mkdir -p tests/src/container1-override && touch tests/src/container1-override/test.txt
  mkdir -p tests/src/container3-new && touch tests/src/container3-new/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1" &&
      echo "def456:container2" &&
      echo "ghi789:container3"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1-override/ tests/dest/container1/" &&
      echo "-ahq tests/src/container3-new/ tests/dest/container3/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1-override/" &&
      echo "-ahq tests/src/container3/ tests/dest/container3-new/"
  )

  test_rsync \
    --name "Test Source override with KEEP_SRC_DIR_NAME (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --disallow "$disallowed_rsync_output" \
    --expect "$expected_rsync_output"

  cleanup_on_success
}

test_keep_src_dir_name_label() {
  clear_files

  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1-new && touch tests/src/container1-new/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.keep_src_dir_name\":\"false\"," &&
      echo "\"nautical-backup.override-source-dir\":\"container1-new\"}"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/container1-new/ tests/dest/container1/"
  )

  disallowed_rsync_output=$(
    echo "-ahq tests/src/container1/ tests/dest/container1-override-bad/"
  )

  test_rsync \
    --name "Test Source override with KEEP_SRC_DIR_NAME=false (env)" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --disallow "$disallowed_rsync_output" \
    --expect "$expected_rsync_output"

  mock_docker_label_lines=$(
    echo "{\"nautical-backup.keep_src_dir_name\":\"true\"," &&
      echo "\"nautical-backup.override-source-dir\":\"container1-new\"}"
  )

  clear_files

  expected_rsync_output=$(
    echo "-ahq tests/src/container1-new/ tests/dest/container1-new/"
  )

  test_rsync \
    --name "Test Source override with KEEP_SRC_DIR_NAME=true (label)" \
    --mock_ps "$mock_docker_ps_lines" \
    --mock_labels "$mock_docker_label_lines" \
    --disallow "$disallowed_rsync_output" \
    --expect "$expected_rsync_output"

  cleanup_on_success
}

test_backup_on_start() {
  clear_files
  export BACKUP_ON_START="false"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  disallowed_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  expected_docker_output=$(
    echo "ps --no-trunc --format={{.ID}}:{{.Names}}" &&
      echo "inspect --format {{json .Config.Labels}} abc123" &&
      echo "stop container1" &&
      echo "start container1"
  )

  test_docker \
    --name "Test BACKUP_ON_START=false" \
    --mock_ps "$mock_docker_ps_lines" \
    --disallow "$disallowed_docker_output"

  cleanup_on_success

  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$(
    echo "abc123:container1"
  )

  expected_docker_output=$(
    echo "stop container1" &&
      echo "start container1"
  )

  test_docker \
    --name "Test BACKUP_ON_START=true" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_docker_output"

  cleanup_on_success
}

test_logThis() {
  clear_files
  source pkg/logger.sh

  # Temporarily redirect stdout and stderr
  exec 3>&1 4>&2
  exec 1>test_output.log 2>&1

  # Test Case 1: Test with INFO level
  script_logging_level="INFO"
  logThis "This is an info message" "INFO"
  expected="INFO: This is an info message"
  actual=$(cat test_output.log | tr -d '\n' | tr -d '\000') # Remove new line and null bytes
  if [[ "$actual" != "$expected" ]]; then
    exec 1>&3 2>&4
    fail "Test Logger"
    echo "Test Case 1 failed: Expected '$expected', got '$actual'"
    exit 1
  fi

  >test_output.log # Clear log file

  # Test Case 2: Test with DEBUG level and script_logging_level set to INFO
  script_logging_level="INFO"
  logThis "This is a debug message" "DEBUG"
  expected=""
  actual=$(cat test_output.log | tr -d '\n' | tr -d '\000') # Remove new line and null bytes
  if [[ "$actual" != "$expected" ]]; then
    exec 1>&3 2>&4
    fail "Test Logger"
    echo "Test Case 2 failed: Expected '$expected', got '$actual'"
    exit 1
  fi

  >test_output.log # Clear log file

  # Test Case 3: Test with DEBUG level and script_logging_level set to DEBUG
  script_logging_level="DEBUG"
  logThis "This is a debug message" "DEBUG"
  expected="DEBUG: This is a debug message"
  actual=$(cat test_output.log | tr -d '\n' | tr -d '\000') # Remove new line and null bytes
  if [[ "$actual" != "$expected" ]]; then
    exec 1>&3 2>&4
    fail "Test Logger"
    echo "Test Case 3 failed: Expected '$expected', got '$actual'"
    exit 1
  fi

  >test_output.log # Clear log file

  # Add more test cases as needed

  # Restore stdout and stderr
  exec 1>&3 2>&4

  # Cleanup
  rm test_output.log

  pass "Test Logger"
  cleanup_on_success
}

test_logThis_report_file() {
  clear_files
  source pkg/logger.sh

  # Mock DEST_LOCATION and report_file
  DEST_LOCATION="./test_dest_report"
  report_file="test_report.log"
  mkdir -p "$DEST_LOCATION"
  touch "$DEST_LOCATION/$report_file"

  # Enable report file logging
  REPORT_FILE="true"
  report_file_logging_level="INFO"

  # Test Case: INFO level message
  logThis "Test INFO message" "INFO"
  expected="INFO: Test INFO message"

  # Check report file
  actual=$(tail -n 1 "$DEST_LOCATION/$report_file")
  if [[ ! "$actual" =~ "$expected" ]]; then
    fail "Test Logger Report File"
    echo "Test Case Report File failed: Expected message not found in report file."
    echo "Actual:"
    echo "$actual"
    echo "Expected:"
    echo "$expected"
    exit 1
  fi

  # Cleanup
  rm -rf "$DEST_LOCATION"

  pass "Test Logger Report File"
  cleanup_on_success
}

test_additional_folders() {
  clear_files
  export BACKUP_ON_START="true"
  export ADDITIONAL_FOLDERS="add1,add2"

  mkdir -p tests/src/add1 && touch tests/src/add1/test.txt
  mkdir -p tests/src/add2 && touch tests/src/add2/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$()

  disallowed_rsync_output=$(
    echo "anthing_to_not_allow"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/add1/ tests/dest/add1/" &&
      echo "-ahq tests/src/add2/ tests/dest/add2/"
  )

  test_rsync \
    --name "Test additional folders" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success

  clear_files
  export BACKUP_ON_START="true"
  export USE_DEFAULT_RSYNC_ARGS="false"
  export RSYNC_CUSTOM_ARGS="-aq"
  export ADDITIONAL_FOLDERS="add1"

  mkdir -p tests/src/add1 && touch tests/src/add1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$()

  disallowed_rsync_output=$(
    echo "-ahq tests/src/add1/ tests/dest/add1/"
  )

  expected_rsync_output=$(
    echo "-aq tests/src/add1/ tests/dest/add1/"
  )

  test_rsync \
    --name "Test additional folders with custom args" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success

  clear_files
  export BACKUP_ON_START="true"
  export ADDITIONAL_FOLDERS="add1"
  export ADDITIONAL_FOLDERS_WHEN="both"

  mkdir -p tests/src/add1 && touch tests/src/add1/test.txt
  mkdir -p tests/dest

  mock_docker_ps_lines=$()

  disallowed_rsync_output=$(
    echo "anthing_to_not_allow"
  )

  expected_rsync_output=$(
    echo "-ahq tests/src/add1/ tests/dest/add1/" &&
      echo "-ahq tests/src/add1/ tests/dest/add1/"
  )

  test_rsync \
    --name "Test additional folders both" \
    --mock_ps "$mock_docker_ps_lines" \
    --expect "$expected_rsync_output" \
    --disallow "$disallowed_rsync_output"

  cleanup_on_success
}

# ---- Call Tests ----
reset_environment_variables

# Run the tests
test_rsync_commands
test_docker_commands
test_skip_containers
test_enable_label
test_require_label
test_override_src
test_override_dest
test_skip_stopping_env
test_skip_stopping_label_true
test_skip_stopping_label_false
test_report_file
test_custom_rsync_args_env
test_custom_rsync_args_label
test_custom_rsync_args_both
test_keep_src_dir_name_env
test_keep_src_dir_name_label
test_backup_on_start
test_report_file_on_backup_only
test_logThis
test_logThis_report_file
test_additional_folders

# Cleanup
teardown
