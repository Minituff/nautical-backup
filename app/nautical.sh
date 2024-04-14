#!/usr/bin/with-contenv bash
# `with-contenv` is an s6 feature that allows the script to run with the container's environment variables

# The backup script must be run from the root directory
cd /

python3 /app/backup.py