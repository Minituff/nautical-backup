FROM mcr.microsoft.com/devcontainers/python:3.10

# These files must be ignored in the docker ignore
COPY api/requirements.txt /tmp/nautical/api-requirements.txt
COPY pytest/requirements.txt /tmp/nautical/pytest-requirements.txt

RUN echo "Installing python packages (for api)..." && \
    python3 -m pip install -r /tmp/nautical/api-requirements.txt && \
    echo "Installing python packages (for api tests)..." && \
    python3 -m pip install -r /tmp/nautical/pytest-requirements.txt