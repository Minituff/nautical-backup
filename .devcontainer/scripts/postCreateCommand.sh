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


echo "Adding aliases (for convenience)..."

# Go back to the workspace directory
echo "alias home=\"cd /workspaces/nautical-backup\"" >> ~/.zshrc

# BUILD container
echo "alias nbb=\"home && docker build -t nautical-backup -t nautical-backup:test --no-cache --build-arg='NAUTICAL_VERSION=testing' .\"" >> ~/.zshrc

# BUILD & RUN container
echo "alias nbbr=\"nbb && cd dev && docker-compose up\"" >> ~/.zshrc

# RUN container that is already build
echo "alias nbr=\"home/dev && docker-compose up\"" >> ~/.zshrc

# BUILD TEST container
echo "alias nbt=\"home && docker build -t minituff/nautical-test --no-cache --build-arg='NAUTICAL_VERSION=testing' --build-arg='TEST_MODE=0' .\"" >> ~/.zshrc

# BUILD & RUN TEST container
echo "alias nbtr=\"nbt && cd /workspaces/nautical-backup/tests && docker compose run nautical-backup-test3\"" >> ~/.zshrc

# RUN API locally
echo "alias nbapi=\"python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8069 --use-colors\"" >> ~/.zshrc

# Run pytest and output report as hmtl
echo "alias nbpt=\"home && && clear && python3 -m pytest --cov api --cov-report html --cov-report term\"" >> ~/.zshrc


cecho "CYAN" "Installing python packages (for api)..."
python3 -m pip install -r /workspaces/nautical-backup/api/requirements.txt
cecho "CYAN" "Installing python packages (for api tests)..."
python3 -m pip install -r /workspaces/nautical-backup/pytest/requirements.txt
cecho "CYAN" "Installing python packages (for docs)..."
python3 -m pip install -r /workspaces/nautical-backup/docs/requirements.txt
python3 -m pip install black

cecho "GREEN" "-- Init complete -- Nautical development enviornment ready to go!!"

zsh && omz reload
# No need to 'source ~/.zshrc' since the terminal won't be open yet
