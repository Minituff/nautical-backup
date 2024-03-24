#!/usr/bin/python3
# Or whatever path to your python interpreter

# TODO: Add the following lines to your Dockerfile
# ln -s /workspaces/nautical-backup/pkg/backup.py /usr/local/bin/script-test
# chmod +x /usr/local/bin/script-test

import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import sys
import subprocess

import docker
from docker.models.containers import Container
from docker.errors import APIError

from api.db import DB
from api.config import Settings
from app.logger import Logger
from app.nautical_env import NauticalEnv
from enum import Enum

class BeforeOrAfter(Enum):
    BEFORE = 1
    AFTER = 2
    
class BeforeAfterorDuring(Enum):
    BEFORE = 1
    AFTER = 2
    DURING = 3
    
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
        skip_containers_set = set(SKIP_CONTAINERS.split(","))

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
            self.log_this(
                f"Skipping ${c.name} as 'nautical-backup.enable=true' was not found and REQUIRE_LABEL is true.", "DEBUG"
            )
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
        containers: List[Container] = self.docker.containers.list()  # type: ignore
        starting_container_amt = len(containers)
        self.log_this(f"Processing {starting_container_amt} number of containers...")
        self.db.put("number_of_containers", starting_container_amt)

        containers_by_group: Dict[str, List[Container]] = {}

        for c in containers:
            if self._should_skip_container(c) == True:
                continue  # Skip this container
            # Create a default group, so ungrouped items are not grouped together
            default_group = f"_{str(c.id)[0:12]}"
            group = str(c.labels.get("nautical-backup.group", default_group))

            if group not in containers_by_group:
                containers_by_group[group] = [c]
            else:
                containers_by_group[group].append(c)

        return containers_by_group

    def _run_curl(self, c: Container, when: BeforeAfterorDuring) -> Optional[subprocess.CompletedProcess[bytes]]:
        """Runs a curl command from the Nautical Container itself."""
        
        if when == BeforeAfterorDuring.BEFORE:
            command = str(c.labels.get("nautical-backup.curl.before", ""))
            if command and command != "":
                self.log_this("Running PRE-backup curl command for $name", "DEBUG")
        elif when == BeforeAfterorDuring.DURING:
            command = str(c.labels.get("nautical-backup.curl.during", ""))
            if command and command != "":
                self.log_this("Running DURING-backup curl command for $name", "DEBUG")
        elif when == BeforeAfterorDuring.AFTER:
            command = str(c.labels.get("nautical-backup.curl.after", ""))
            if command and command != "":
                self.log_this("Running AFTER-backup curl command for $name", "DEBUG")
        else:
            return None
        
        # Example command "curl -o /app/destination/google google.com"
        if not command or command == "":
            return None
        
        self.log_this(f"Running CURL command: {command}")
        out = subprocess.run(command, shell=True, executable="/bin/bash", capture_output=False)
        return out


    def _run_lifecyle_hook(self, c: Container, when: BeforeOrAfter):
        """Runs a commend inside the child container"""
        if when == BeforeOrAfter.BEFORE:
            command = str(c.labels.get("nautical-backup.lifecycle.before", ""))
            timeout = str(c.labels.get("nautical-backup.lifecycle.before.timeout", "60"))
            if command and command != "":
                self.log_this("Running DURING-backup lifecycle hook for $name", "DEBUG")
        elif when == BeforeOrAfter.AFTER:
            timeout = str(c.labels.get("nautical-backup.lifecycle.after.timeout", "60"))
            command = str(c.labels.get("nautical-backup.lifecycle.after", ""))
            if command and command != "":
                self.log_this("Running AFTER-backup lifecycle hook for $name", "DEBUG")
        else:
            return
        if not command or command == "":
            return None
        
        command = f"timeout {timeout} " + command

        self.log_this(f"RUNNING '{command}'", "DEBUG")
        c.exec_run(command)
        
    def _stop_container(self, c:Container, attempt=1) -> bool:
            c.reload() # Refresh the status for this container
            
            SKIP_STOPPING = self.env.SKIP_STOPPING
            skip_stopping_set = set(SKIP_STOPPING.split(","))
            if c.name in skip_stopping_set or c.id in skip_stopping_set:
                self.log_this(f"Container {c.name} is in SKIP_STOPPING list. Will not stop container." "DEBUG")
                return True
            
            stop_before_backup = str(c.labels.get("nautical-backup.stop-before-backup", "true"))
            if stop_before_backup.lower() == "false":
                self.log_this(f"Skipping stopping of {c.name} because of label" "DEBUG")
                return True
            if c.status != "running":
                self.log_this(f"Container {c.name} was not running. No need to stop.", "DEBUG")
                return True
            
            try:
                self.log_this(f"Stopping {c.name}...")
                c.stop(timeout=10) #* Actually stop the container
            except APIError as e:
                self.log_this(f"Error stopping container {c.name}. Skipping backup for this container.", "ERROR")
                return False
            
            c.reload() # Refresh the status for this container
            
            if c.status == "exited":
                return True
            elif attempt <= 3:
                self.log_this(f"Container {c.name} was not in exited state. Trying again (Attempt {attempt}/3)", "ERROR")
                self._stop_container(c, attempt=attempt+1)
            return False
            
    def backup(self):
        self.db.put("backup_running", True)
        self.db.put("last_cron", datetime.now().strftime("%m/%d/%y %I:%M"))

        containers_by_group = self.group_containers()

        # Before backup
        for group, containers in containers_by_group.items():
            for c in containers:
                # Run before hooks
                self._run_curl(c, BeforeAfterorDuring.BEFORE)
                self._run_lifecyle_hook(c, BeforeOrAfter.BEFORE)

                stop_result = self._stop_container(c)
                # Stop containers
                pass
            
        # During backup
        for group, containers in containers_by_group.items():
            for c in containers:
                c.reload() # Refresh the status for this container
                # Backup containers
                # if c.status == "exited" or label says its okay
                    # self._backup_now()
                pass
        # After backup
        for group, containers in containers_by_group.items():
            for c in containers:
                # Start containers
                
                self._run_lifecyle_hook(c, BeforeOrAfter.AFTER)
                self._run_curl(c, BeforeAfterorDuring.AFTER)

        self.db.put("backup_running", False)


if __name__ == "__main__":
    nautical = NauticalBackup()
    nautical.backup()
