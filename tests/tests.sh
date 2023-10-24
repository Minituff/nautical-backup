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

# Color echo
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

# ---- Actual Tests ----

test_docker_ps() {
  clear_files
  export BACKUP_ON_START="true"
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

  declare -a disallowed_docker_output=(
    "stop container2"
    "start container2"
    "stop container3"
    "start container3"
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
      exit 1
    fi
  done

  # Check if any disallowed command is in the actual output
  for disallowed_docker in "${disallowed_docker_output[@]}"; do
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$disallowed_docker" ]]; then
        fail "${FUNCNAME[0]}"
        echo "'$disallowed_docker' found in actual output but is disallowed."
        test_passed=false
        exit 1
      fi
    done
  done

  if [ "$test_passed" = true ]; then
    pass ${FUNCNAME[0]}
  else
    fail ${FUNCNAME[0]}
    echo "Expected:"
    print_array "${expected_docker_output[@]}"
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
      echo "${FUNCNAME[0]} FAIL: RSYNC '$expected_rsync' not found in actual output."
      test_passed=false
    fi
  done

  if [ "$test_passed" = true ]; then
    pass ${FUNCNAME[0]}
  else
    fail ${FUNCNAME[0]}
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
      exit 1
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
    exit 1
  fi

}

test_docker() {
  local mock_docker_ps_lines
  local disallowed_docker_output
  local expected_docker_output
  local test_name

  # Parse named parameters
  while [[ "$#" -gt 0 ]]; do
    case $1 in
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
    --name)
      test_name="$2"
      shift
      ;;
    *)
      echo "Unknown parameter passed: $1"
      exit 1
      ;;
    esac
    shift
  done

  IFS=$'\n' read -rd '' -a mock_docker_ps_lines_arr <<<"$mock_docker_ps_lines"
  IFS=$'\n' read -rd '' -a disallowed_docker_output_arr <<<"$disallowed_docker_output"
  IFS=$'\n' read -rd '' -a expected_docker_output_arr <<<"$expected_docker_output"

  clear_files
  export BACKUP_ON_START="true"
  mkdir -p tests/src/container1 && touch tests/src/container1/test.txt
  mkdir -p tests/dest

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
      exit 1
    fi
  done

  # Check if any disallowed command is in the actual output
  for disallowed_docker in "${disallowed_docker_output_arr[@]}"; do # Use the _arr array here
    for docker_actual in "${docker_actual_output[@]}"; do
      if [[ "$docker_actual" == "$disallowed_docker" ]]; then
        fail "$test_name"
        echo "'$disallowed_docker' found in actual output but is disallowed."
        test_passed=false
        exit 1
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
    exit 1
  fi
}

test_docker_commands() {
  read -r -d '' mock_docker_ps_lines <<EOM
abc123:container1
def456:container2
ghi789:container3
EOM

  read -r -d '' disallowed_docker_output <<EOM
stop container2
start container2
stop container3
start container3
EOM

  read -r -d '' expected_docker_output <<EOM
ps --no-trunc --format={{.ID}}:{{.Names}}
inspect --format {{json .Config.Labels}} abc123
EOM

  test_docker \
    --name "Test Docker Commands on default settings" \
    --mock "$mock_docker_ps_lines" \
    --expect "$expected_docker_output" \
    --disallow "$disallowed_docker_output"
}

# Run the tests
test_docker_commands
# test_docker_ps
# test_rsync
# test_skip_containers
# Cleanup
rm "$DOCKER_COMMANDS_FILE"
rm "$RSYNC_COMMANDS_RFILE"
rm -rf tests/src
rm -rf tests/dest

source pkg/logger.sh

delete_report_file
