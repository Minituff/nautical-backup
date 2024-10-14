#!/usr/bin/env bash

echo "Installing 'cecho' command..."
unlink /usr/bin/cecho
ln -s /workspaces/nautical-backup/.devcontainer/scripts/cecho.sh /usr/bin/cecho
chmod +x /usr/bin/cecho

cecho CYAN "Installing 'nb' command..."
unlink /usr/bin/nb
ln -s /workspaces/nautical-backup/.devcontainer/scripts/nb.sh /usr/bin/nb
chmod +x /usr/bin/nb


cecho CYAN "Installing python packages..."
python3 -m pip install --upgrade pip
python3 -m pip install -r /workspaces/nautical-backup/requirements-dev.txt

cecho CYAN "Adding aliases (for convenience)..."
for file in ~/.zshrc ~/.bashrc; do
    echo "alias home=\"cd /workspaces/nautical-backup\"" >> "$file"
    echo "alias cls=\"clear\"" >> "$file"
done

echo 'DISABLE_UPDATE_PROMPT=true  # Auto update ohmyzsh and dont ask' >> ~/.zshrc

# cecho CYAN "Installing python packages (for docs)..."
# python3 -m pip install -r /workspaces/nautical-backup/docs/requirements.txt

cecho CYAN "Handling locales..."
echo "export LANG=en_US.UTF-8" >> ~/.zshrc; 
LC_CTYPE=en_US.UTF-8
echo en_US.UTF-8 UTF-8 > /etc/locale.gen
locale-gen

# Test commands
nb --help

cecho CYAN "Installing pre-commit hooks..."
pre-commit install 

cecho "GREEN" "Success!! Nautical Development enviornment ready to go!!"
cecho "GREEN" "Use the command 'nb --help' to get started."

# cecho "YELLOW" "Please ensure the slashes are linux style, i.e. /workspaces/nautical-backup"
# cecho "CYAN" $LOCAL_WORKSPACE_FOLDER
exit 0
# No need to 'source ~/.zshrc' since the terminal won't be open yet
