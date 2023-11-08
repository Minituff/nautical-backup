echo "Installing ruby packages (for testing)..."
gem install bashcov simplecov-cobertura simplecov-html

echo "Adding aliases (for convenience)..."
echo "alias nbb=\"cd /workspaces/nautical-backup && docker build -t nautical-backup -t nautical-backup:test --progress=plain --no-cache --build-arg='NAUTICAL_VERSION=testing' .\"" >> ~/.zshrc
echo "alias nbbr=\"nbb && cd dev && docker-compose up\"" >> ~/.zshrc
echo "alias nbr=\"cd /workspaces/nautical-backup/dev && docker-compose up\"" >> ~/.zshrc
echo "Aliases complete!"

echo "Installing python packages (for api)..."
python3 -m pip install -r /workspaces/nautical-backup/pkg/api/requirements.txt
echo "Installing python packages (for docs)..."
python3 -m pip install -r /workspaces/nautical-backup/docs/requirements.txt

echo "Init complete. Nautical development enviornment ready to go!!"

zsh && omz reload
# No need to 'source ~/.zshrc' since the terminal won't be open yet
