#!/usr/bin/python
# Or whatever path to your python interpreter

# TODO: Add the following lines to your Dockerfile
# ln -s /workspaces/nautical-backup/pkg/backup.py /usr/local/bin/script-test
# chmod +x /usr/local/bin/script-test

import os
from datetime import datetime
from typing import Union

from api.db import DB
from api.config import Settings

class NauticalBackup:
    def __init__(self):
        self.db = DB()
        self.settings = Settings()

    def backup(self):
        self.db.put("backup_running", True)
        datetime_format2 = datetime.now().strftime("%m/%d/%y %I:%M")
        self.db.put("last_cron", datetime_format2)
        
        

        # Read the environment variables
        SKIP_CONTAINERS = os.environ.get('SKIP_CONTAINERS', '')
        SKIP_STOPPING = os.environ.get('SKIP_STOPPING', '')
        SELF_CONTAINER_ID = os.environ.get('SELF_CONTAINER_ID', '')

        # Convert the strings into lists
        skip_containers_array = SKIP_CONTAINERS.split(',')
        skip_stopping_array = SKIP_STOPPING.split(',')

        # Append SELF_CONTAINER_ID to the skip_containers_array
        skip_containers_array.append(SELF_CONTAINER_ID)

        # Example usage
        print(skip_containers_array)
        print(skip_stopping_array)
        
if __name__ == "__main__":
    nautical = NauticalBackup()
    nautical.backup()