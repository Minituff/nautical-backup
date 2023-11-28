#!/usr/bin/env bash

cecho() {
  local RED="\033[0;31m"
  local GREEN="\033[0;32m"  # <-- [0 means not bold
  local YELLOW="\033[1;33m" # <-- [1 means bold
  local CYAN="\033[1;36m"
  
  # ... Add more colors if you like

  NC="\033[0m" # No Color

  printf "${!1}${2} ${NC}\n"
}

# Call the command immediately 
cecho "$@"