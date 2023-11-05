gem install bashcov simplecov-cobertura simplecov-html

echo "Adding aliases..."
echo "alias nbb=\"cd /workspaces/nautical-backup && docker build -t nautical-backup -t nautical-backup:test --progress=plain --no-cache --build-arg='NAUTICAL_VERSION=testing' .\"" >> ~/.zshrc
echo "alias nbbr=\"nbb && cd dev && docker-compose up\"" >> ~/.zshrc
echo "alias nbr=\"cd /workspaces/nautical-backup/dev && docker-compose up\"" >> ~/.zshrc
zsh && omz reload
echo "Aliases complete!"
# No need to 'source ~/.zshrc' since the terminal won't be open yet
