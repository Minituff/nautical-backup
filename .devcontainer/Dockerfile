# https://github.com/devcontainers/images/tree/main/src/python
FROM mcr.microsoft.com/devcontainers/python:3.13


RUN echo "Installing packages..." && \
    apt-get update && \
    apt-get install -y --no-install-recommends nano curl jq dos2unix && \
    rm -rf /var/lib/apt/lists/* && \
    echo "Packages installed."

# These files must be ignored in the docker ignore
COPY requirements.txt /tmp/nautical/requirements.txt
COPY requirements-dev.txt /tmp/nautical/requirements-dev.txt

RUN echo "Installing packages..." && \
  apt-get update && export DEBIAN_FRONTEND=noninteractive && \
  apt install -y \
    jq \
    curl \
    nano && \
  echo "Cleanup" && \
  rm -rf /var/lib/apt/lists/* && \
  echo "Installation complete."

RUN echo "Installing python packages (for api)..." && \
  python3 -m pip install --upgrade pip && \
  # This will also install everything in requirements.txt file
  python3 -m pip --no-cache-dir install -r /tmp/nautical/requirements-dev.txt && \
  echo "Installation complete."

RUN echo "Setting up bash history persistance..." && \
  SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" &&  \
  echo "$SNIPPET" >> "/root/.bashrc" && \
  SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.zsh_history" && \
  echo "$SNIPPET" >> "/root/.zshrc" && \
  echo "Bash history persistence setup complete."
  
# For development, prevents Nautical from stopping VSCode DevContainer itself
LABEL nautical-backup.enable=false