#!/usr/bin/python3
# Or whatever path to your python interpreter

# TODO: Add the following lines to your Dockerfile
# ln -s /workspaces/nautical-backup/pkg/backup.py /usr/local/bin/script-test
# chmod +x /usr/local/bin/script-test

import os
from datetime import datetime
from typing import Union
import sys
import docker

from api.db import DB
from api.config import Settings
from app.logger import Logger
from app.env import ENV

class NauticalBackup:
    def __init__(self):
        self.db = DB()
        self.env = ENV()
        self.logger = Logger() 
        self.settings = Settings()
        
        self.verify_source_location(self.env.SOURCE_LOCATION)
        self.verify_destination_location(self.env.DEST_LOCATION)
    
    def log_this(self, log_message, log_priority="INFO", message_type="default") -> None:
        """Wrapper for log this"""
        return self.logger.log_this(log_message, log_priority, message_type)
    
    def verify_source_location(self, src_dir):
        self.log_this(f"Verifying source directory '{src_dir}'...", "DEBUG", "init")
        if not os.path.isdir(src_dir):
            self.log_this(f"Source directory '{src_dir}' does not exist.", "ERROR", "init")
            sys.exit(1)
        elif not os.access(src_dir, os.R_OK):
            self.log_this(f"No read access to source directory '{src_dir}'.", "ERROR", "init")
            sys.exit(1)
        
        self.log_this("Source directory '{src_dir}' access verified", "TRACE", "init")

    def verify_destination_location(self, dest_dir):
        self.log_this(f"Verifying destination directory '{dest_dir}'...", "DEBUG", "init")
        if not os.path.isdir(dest_dir):
            self.log_this(f"Destination directory '{dest_dir}' does not exist.", "ERROR", "init")
            sys.exit(1)
        elif not os.access(dest_dir, os.R_OK):
            self.log_this(f"No read access to destination directory '{dest_dir}'.", "ERROR", "init")
            sys.exit(1)
        elif not os.access(dest_dir, os.W_OK):
            self.log_this(f"No write access to destination directory '{dest_dir}'.", "ERROR", "init")
            sys.exit(1)
            
        self.log_this("Destination directory '{dest_dir}' access verified", "TRACE", "init")
            
    def backup(self):
        self.db.put("backup_running", True)
        datetime_format2 = datetime.now().strftime("%m/%d/%y %I:%M")
        self.db.put("last_cron", datetime_format2)
        
    
        # Read the environment variables
        SKIP_CONTAINERS = self.env.SKIP_CONTAINERS
        SKIP_STOPPING = self.env.SKIP_STOPPING
        SELF_CONTAINER_ID = self.env.SELF_CONTAINER_ID

        # Convert the strings into lists
        skip_containers_array = SKIP_CONTAINERS.split(',')
        skip_stopping_array = SKIP_STOPPING.split(',')

        # Append SELF_CONTAINER_ID to the skip_containers_array
        skip_containers_array.append(SELF_CONTAINER_ID)

        # Example usage
        print(skip_containers_array)
        print(skip_stopping_array)
        
        self.db.put("backup_running", False)
        
if __name__ == "__main__":
    nautical = NauticalBackup()
    nautical.backup()