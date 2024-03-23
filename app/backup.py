#!/usr/bin/python3
# Or whatever path to your python interpreter

# TODO: Add the following lines to your Dockerfile
# ln -s /workspaces/nautical-backup/pkg/backup.py /usr/local/bin/script-test
# chmod +x /usr/local/bin/script-test

import os
from datetime import datetime
from typing import Dict, List, Union
import sys
import docker
from docker.models.containers import Container

from api.db import DB
from api.config import Settings
from app.logger import Logger
from app.nautical_env import NauticalEnv

class NauticalBackup:
    def __init__(self):
        self.db = DB()
        self.env = NauticalEnv()
        self.logger = Logger() 
        self.settings = Settings()
        self.docker = docker.from_env()
        
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
    
    def _should_skip_container(self, c: Container) -> bool:
        """Use logic to determine if a container should be skipped by nautical completely"""
        # Read the environment variables
        SKIP_CONTAINERS = self.env.SKIP_CONTAINERS
    
        SELF_CONTAINER_ID = self.env.SELF_CONTAINER_ID

        # Convert the strings into lists
        skip_containers_set = set(SKIP_CONTAINERS.split(','))

        
        nautical_backup_enable_str = str(c.labels.get("nautical-backup.enable", ""))
        if nautical_backup_enable_str.lower() == "false":
            nautical_backup_enable = False
        elif nautical_backup_enable_str.lower() == "true":
            nautical_backup_enable = True
        else:
            nautical_backup_enable = None
        
        if c.id == SELF_CONTAINER_ID:
            self.log_this(f"Skipping {c.name} because it's ID is the same as Nautical", "TRACE")
            return True
        
        if nautical_backup_enable == False:
            self.log_this(f"Skipping {c.name} based on label", "DEBUG")
            return True
        
        if self.env.REQUIRE_LABEL == True and nautical_backup_enable is not True:
            self.log_this(f"Skipping ${c.name} as 'nautical-backup.enable=true' was not found and REQUIRE_LABEL is true.", "DEBUG")
            return True
        
        if c.id in skip_containers_set:
            self.log_this(f"Skipping {c.name} based on name", "DEBUG")
            return True
        
        if c.name in skip_containers_set:
            self.log_this(f"Skipping {c.name} based on ID {c.id}", "DEBUG")
            return True

        # No reason to skip
        return False
    
    def group_containers(self) -> Dict[str, List[Container]]:
        containers: List[Container] = self.docker.containers.list() # type: ignore
        starting_container_amt = len(containers)
        self.log_this(f"Processing {starting_container_amt} number of containers...")
        self.db.put("number_of_containers", starting_container_amt)
        
        SKIP_STOPPING = self.env.SKIP_STOPPING
        skip_stopping_set = set(SKIP_STOPPING.split(','))
        
        containers_by_group : Dict[str, List[Container]] = {}
        
        for c in containers:
            if self._should_skip_container(c) == True:
                continue # Skip this container
                
            group = str(c.labels.get("nautical-backup.group", "default"))
            print(c.name, group)
            
            if group not in containers_by_group:
                containers_by_group[group] = [c]
            else:
                containers_by_group[group].append(c)
        
        return containers_by_group
        
        
    def backup(self):
        self.db.put("backup_running", True)
        datetime_format2 = datetime.now().strftime("%m/%d/%y %I:%M")
        self.db.put("last_cron", datetime_format2)
        
        containers_by_group = self.group_containers()
        print(containers_by_group)
        
        self.db.put("backup_running", False)
        
if __name__ == "__main__":
    nautical = NauticalBackup()
    nautical.backup()