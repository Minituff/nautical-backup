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

RUN echo "Installing python packages (for api)..." && \
    # This will also install everything in requirements.txt file
    python3 -m pip --disable-pip-version-check --no-cache-dir install -r /tmp/nautical/requirements-dev.txt && \
    echo "Installation complete."

# For development, prevents Nautical from stopping VSCode DevContainer itself
LABEL nautical-backup.enable=false