#!/usr/bin/env bash

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

cecho "CYAN" "Installing ruby packages (for testing)..."
gem install bashcov simplecov-cobertura simplecov-html

echo "Adding aliases (for convenience)..."
echo "alias nbb=\"cd /workspaces/nautical-backup && docker build -t nautical-backup -t nautical-backup:test --progress=plain --no-cache --build-arg='NAUTICAL_VERSION=testing' .\"" >> ~/.zshrc
echo "alias nbbr=\"nbb && cd dev && docker-compose up\"" >> ~/.zshrc
echo "alias nbr=\"cd /workspaces/nautical-backup/dev && docker-compose up\"" >> ~/.zshrc
echo "alias nbt=\"cd /workspaces/nautical-backup && docker build -t nautical-test --no-cache --build-arg='NAUTICAL_VERSION=testing' --build-arg='TEST_MODE=true' .\"" >> ~/.zshrc
# echo "alias nbt=\"nbb && cd /workspaces/nautical-backup && docker build -f Dockerfile.test -t nautical-test -t minituff/nautical-test --progress=plain --no-cache --build-arg='NAUTICAL_VERSION=testing' .\"" >> ~/.zshrc
echo "alias nbtr=\"nbt && cd /workspaces/nautical-backup/tests && docker compose run nautical-backup-test3\"" >> ~/.zshrc

cecho "CYAN" "Installing python packages (for api)..."
python3 -m pip install -r /workspaces/nautical-backup/pkg/api/requirements.txt
cecho "CYAN" "Installing python packages (for docs)..."
python3 -m pip install -r /workspaces/nautical-backup/docs/requirements.txt
python3 -m pip install black

cecho "GREEN" "-- Init complete -- Nautical development enviornment ready to go!!"

zsh && omz reload
# No need to 'source ~/.zshrc' since the terminal won't be open yet
