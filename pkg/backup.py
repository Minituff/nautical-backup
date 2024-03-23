#!/usr/local/bin/python
# Or whatever path to your python interpreter

# TODO: Add the following lines to your Dockerfile
# ln -s /workspaces/nautical-backup/pkg/backup.py /usr/local/bin/script-test
# chmod +x /usr/local/bin/script-test

from api.db import DB
from api.config import Settings
from typing import Union

print("TESTING: pkg.backup.py")