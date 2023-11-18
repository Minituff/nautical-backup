#!/usr/bin/env bash

echo "Installing 'cecho' command..."
ln -s /workspaces/nautical-backup/.devcontainer/scripts/cecho.sh /usr/bin/cecho
chmod +x /usr/bin/cecho

cecho CYAN "Installing 'nb' command..."
ln -s /workspaces/nautical-backup/.devcontainer/scripts/nb.sh /usr/bin/nb
chmod +x /usr/bin/nb


cecho CYAN "Installing python packages (for api)..."
python3 -m pip install -r /workspaces/nautical-backup/api/requirements.txt

cecho CYAN "Installing python packages (for api tests)..."
python3 -m pip install -r /workspaces/nautical-backup/pytest/requirements.txt

cecho CYAN "Installing python packages (for docs)..."
python3 -m pip install -r /workspaces/nautical-backup/docs/requirements.txt

cecho CYAN "Handling locales..."
echo "export LANG=en_US.UTF-8" >> ~/.zshrc; 
LC_CTYPE=en_US.UTF-8
echo en_US.UTF-8 UTF-8 > /etc/locale.gen
locale-gen

# Test commands
nb --help

cecho "GREEN" "Success!! Nautical Development enviornment ready to go!!"
cecho "GREEN" "Use the command 'nb --help' to get started."


zsh && omz reload
# No need to 'source ~/.zshrc' since the terminal won't be open yet
